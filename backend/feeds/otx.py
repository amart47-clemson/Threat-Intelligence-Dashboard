import logging
from collections import defaultdict
from datetime import datetime, timezone

import requests

from config import Config
from enrichment import base_score_from_pulses, calculate_threat_score, enrich_geoip
from models import IOC, IOCType, ScoreHistory, db

logger = logging.getLogger(__name__)

OTX_PULSES_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"

OTX_TYPE_MAP = {
    "IPv4": IOCType.ip,
    "domain": IOCType.domain,
    "URL": IOCType.url,
}


def _normalize_indicator(indicator_type, value):
    if indicator_type == "IPv4":
        return value.strip(), IOCType.ip
    if indicator_type == "domain":
        return value.strip().lower(), IOCType.domain
    if indicator_type == "URL":
        return value.strip(), IOCType.url
    return None, None


def fetch_otx_pulses():
    """Fetch subscribed pulses from AlienVault OTX."""
    headers = {"X-OTX-API-KEY": Config.OTX_API_KEY}
    logger.info("Fetching OTX subscribed pulses...")
    resp = requests.get(OTX_PULSES_URL, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    logger.info("OTX returned %d pulses", len(results))
    return results


def fetch_pulse_indicators(pulse_id):
    """Fetch indicators for a single pulse (not included in subscribed list)."""
    headers = {"X-OTX-API-KEY": Config.OTX_API_KEY}
    url = f"https://otx.alienvault.com/api/v1/pulses/{pulse_id}/indicators"
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.RequestException as exc:
        logger.error("Failed to fetch indicators for pulse %s: %s", pulse_id, exc)
        return []


def parse_pulses(pulses):
    """Aggregate indicators from pulses: value -> {type, tags, pulse_count, raw}."""
    aggregated = defaultdict(
        lambda: {
            "ioc_type": None,
            "tags": set(),
            "pulse_count": 0,
            "raw_pulses": [],
        }
    )

    for pulse in pulses:
        pulse_id = pulse.get("id")
        pulse_tags = pulse.get("tags", []) or []
        indicators = pulse.get("indicators") or fetch_pulse_indicators(pulse_id)
        logger.info(
            "Pulse %s: %d indicators", pulse.get("name", pulse_id), len(indicators)
        )

        for indicator in indicators:
            ind_type = indicator.get("type")
            value = indicator.get("indicator")
            if not value or ind_type not in OTX_TYPE_MAP:
                continue

            normalized, ioc_type = _normalize_indicator(ind_type, value)
            if not normalized:
                continue

            entry = aggregated[normalized]
            entry["ioc_type"] = ioc_type
            entry["pulse_count"] += 1
            entry["tags"].update(pulse_tags)
            entry["raw_pulses"].append(
                {"pulse_id": pulse_id, "indicator": indicator}
            )

    logger.info("Parsed %d unique indicators from OTX pulses", len(aggregated))
    return aggregated


def _record_score_history(ioc, score):
    history = ScoreHistory(ioc_id=ioc.id, threat_score=score)
    db.session.add(history)


def upsert_ioc(value, ioc_type, pulse_count, tags, raw_data):
    """Insert or update an IOC from OTX feed data."""
    now = datetime.now(timezone.utc)
    existing = IOC.query.filter_by(value=value).first()
    base = base_score_from_pulses(pulse_count)
    tags_str = ",".join(sorted(tags)) if tags else None

    if existing:
        existing.feed_count = max(existing.feed_count, pulse_count, 1)
        existing.last_seen = now
        if tags_str:
            existing_tags = set(existing.tags.split(",")) if existing.tags else set()
            existing_tags.update(tags)
            existing.tags = ",".join(sorted(existing_tags))
        existing.raw_data = raw_data
        score = calculate_threat_score(
            base, existing.abuse_confidence, existing.feed_count
        )
        existing.threat_score = score
        _record_score_history(existing, score)
        logger.info("Updated IOC %s (score=%.1f)", value, score)
        return existing

    score = calculate_threat_score(base, None, 1)
    ioc = IOC(
        value=value,
        ioc_type=ioc_type,
        threat_score=score,
        feed_count=1,
        tags=tags_str,
        first_seen=now,
        last_seen=now,
        raw_data=raw_data,
    )
    db.session.add(ioc)
    db.session.flush()
    _record_score_history(ioc, score)
    logger.info("Created IOC %s (score=%.1f)", value, score)
    return ioc


def run_otx_ingestion():
    """Main OTX ingestion entry point."""
    if not Config.OTX_API_KEY:
        logger.warning("OTX_API_KEY not set, skipping OTX ingestion")
        return 0

    pulses = fetch_otx_pulses()
    aggregated = parse_pulses(pulses)
    count = 0

    for value, data in aggregated.items():
        ioc = upsert_ioc(
            value=value,
            ioc_type=data["ioc_type"],
            pulse_count=data["pulse_count"],
            tags=data["tags"],
            raw_data={"otx_pulses": data["raw_pulses"]},
        )
        if ioc.ioc_type == IOCType.ip and (ioc.latitude is None or ioc.longitude is None):
            geo = enrich_geoip(value)
            if geo:
                ioc.latitude = geo["latitude"]
                ioc.longitude = geo["longitude"]
                if not ioc.country:
                    ioc.country = geo["country"]
        count += 1

    db.session.commit()
    logger.info("OTX ingestion complete: %d IOCs processed", count)
    from feeds.feed_state import update_feed_log

    update_feed_log("otx", count)
    return count


def lookup_otx_indicator(value, ioc_type=None):
    """Live lookup of a single indicator via OTX general search."""
    headers = {"X-OTX-API-KEY": Config.OTX_API_KEY}
    type_prefix = {
        IOCType.ip: "IPv4",
        IOCType.domain: "domain",
        IOCType.url: "url",
    }.get(ioc_type, "")
    path_value = value if ioc_type != IOCType.url else requests.utils.quote(value, safe="")
    if type_prefix:
        url = f"https://otx.alienvault.com/api/v1/indicators/{type_prefix}/{path_value}/general"
    else:
        url = f"https://otx.alienvault.com/api/v1/indicators/{value}/general"
    logger.info("OTX live lookup for %s", value)
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("OTX lookup error for %s: %s", value, exc)
        return None

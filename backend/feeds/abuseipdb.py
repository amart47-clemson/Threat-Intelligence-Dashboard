import logging
from datetime import datetime, timezone

import requests

from config import Config
from enrichment import calculate_threat_score, enrich_geoip
from models import IOC, IOCType, ScoreHistory, db

logger = logging.getLogger(__name__)

ABUSEIPDB_CHECK_URL = "https://api.abuseipdb.com/api/v2/check"


def check_abuseipdb(ip_address):
    """Query AbuseIPDB for a single IP address."""
    headers = {
        "Key": Config.ABUSEIPDB_API_KEY,
        "Accept": "application/json",
    }
    params = {"ipAddress": ip_address, "maxAgeInDays": 90}
    logger.info("AbuseIPDB check for %s", ip_address)
    try:
        resp = requests.get(
            ABUSEIPDB_CHECK_URL, headers=headers, params=params, timeout=30
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "abuse_confidence": data.get("abuseConfidenceScore"),
            "country": data.get("countryCode"),
            "isp": data.get("isp"),
            "raw": data,
        }
    except requests.RequestException as exc:
        logger.error("AbuseIPDB error for %s: %s", ip_address, exc)
        return None


def enrich_ioc_with_abuseipdb(ioc):
    """Enrich a single IP IOC with AbuseIPDB data."""
    if ioc.ioc_type != IOCType.ip:
        return False

    result = check_abuseipdb(ioc.value)
    if not result:
        return False

    ioc.abuse_confidence = result["abuse_confidence"]
    if result.get("country"):
        ioc.country = result["country"]

    raw = ioc.raw_data or {}
    raw["abuseipdb"] = result["raw"]
    ioc.raw_data = raw

    pulse_count = 0
    otx_data = raw.get("otx_pulses", [])
    if otx_data:
        pulse_count = len(otx_data)
    else:
        pulse_count = 1

    from enrichment import base_score_from_pulses

    base = base_score_from_pulses(pulse_count)
    score = calculate_threat_score(base, ioc.abuse_confidence, ioc.feed_count)
    ioc.threat_score = score
    ioc.last_seen = datetime.now(timezone.utc)

    history = ScoreHistory(ioc_id=ioc.id, threat_score=score)
    db.session.add(history)
    logger.info(
        "AbuseIPDB enriched %s: confidence=%s, score=%.1f",
        ioc.value,
        ioc.abuse_confidence,
        score,
    )
    return True


def run_abuseipdb_enrichment():
    """Enrich all IP IOCs missing abuse_confidence."""
    if not Config.ABUSEIPDB_API_KEY:
        logger.warning("ABUSEIPDB_API_KEY not set, skipping AbuseIPDB enrichment")
        return 0

    iocs = IOC.query.filter(
        IOC.ioc_type == IOCType.ip, IOC.abuse_confidence.is_(None)
    ).all()
    logger.info("AbuseIPDB enrichment: %d IPs to process", len(iocs))
    count = 0

    for ioc in iocs:
        if enrich_ioc_with_abuseipdb(ioc):
            if ioc.latitude is None or ioc.longitude is None:
                geo = enrich_geoip(ioc.value)
                if geo:
                    ioc.latitude = geo["latitude"]
                    ioc.longitude = geo["longitude"]
                    if not ioc.country:
                        ioc.country = geo["country"]
            count += 1

    db.session.commit()
    logger.info("AbuseIPDB enrichment complete: %d IOCs updated", count)
    from feeds.feed_state import update_feed_log

    update_feed_log("abuseipdb", count)
    return count

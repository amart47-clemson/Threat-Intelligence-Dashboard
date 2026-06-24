import logging
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request

from enrichment import base_score_from_pulses, calculate_threat_score, enrich_geoip
from feeds.abuseipdb import check_abuseipdb
from feeds.otx import lookup_otx_indicator
from models import IOC, IOCType, ScoreHistory, db

logger = logging.getLogger(__name__)

lookup_bp = Blueprint("lookup", __name__)

IP_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$"
)


def detect_ioc_type(value):
    value = value.strip()
    if IP_PATTERN.match(value):
        return IOCType.ip, value
    if value.startswith(("http://", "https://")):
        return IOCType.url, value
    if "." in value and not value.startswith("/"):
        return IOCType.domain, value.lower()
    return None, value


@lookup_bp.route("/api/lookup", methods=["GET"])
def lookup_ioc():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    existing = IOC.query.filter_by(value=q).first()
    if not existing:
        ioc_type, normalized = detect_ioc_type(q)
        if ioc_type:
            existing = IOC.query.filter_by(value=normalized).first()
            q = normalized

    if existing:
        result = existing.to_dict()
        result["source"] = "cache"
        return jsonify(result)

    ioc_type, normalized = detect_ioc_type(q)
    if not ioc_type:
        return jsonify({"error": "Could not determine IOC type for value"}), 400

    logger.info("Live lookup for %s (type=%s)", normalized, ioc_type.value)

    otx_data = lookup_otx_indicator(normalized, ioc_type)
    pulse_count = 0
    tags = set()
    raw_data = {}

    if otx_data:
        pulse_info = otx_data.get("pulse_info", {})
        pulse_count = pulse_info.get("count", 0)
        tags.update(otx_data.get("tags", []) or [])
        raw_data["otx"] = otx_data

    abuse_confidence = None
    country = None

    if ioc_type == IOCType.ip:
        abuse_result = check_abuseipdb(normalized)
        if abuse_result:
            abuse_confidence = abuse_result.get("abuse_confidence")
            country = abuse_result.get("country")
            raw_data["abuseipdb"] = abuse_result.get("raw")

    base = base_score_from_pulses(pulse_count)
    score = calculate_threat_score(base, abuse_confidence, feed_count=1)
    now = datetime.now(timezone.utc)

    ioc = IOC(
        value=normalized,
        ioc_type=ioc_type,
        threat_score=score,
        abuse_confidence=abuse_confidence,
        feed_count=1,
        country=country,
        tags=",".join(sorted(tags)) if tags else None,
        first_seen=now,
        last_seen=now,
        raw_data=raw_data,
    )

    if ioc_type == IOCType.ip:
        geo = enrich_geoip(normalized)
        if geo:
            ioc.latitude = geo["latitude"]
            ioc.longitude = geo["longitude"]
            if not ioc.country:
                ioc.country = geo["country"]

    db.session.add(ioc)
    db.session.flush()
    db.session.add(ScoreHistory(ioc_id=ioc.id, threat_score=score))
    db.session.commit()

    result = ioc.to_dict()
    result["source"] = "live"
    return jsonify(result)

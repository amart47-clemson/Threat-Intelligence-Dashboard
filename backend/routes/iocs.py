import csv
import io
import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func, or_

from models import IOC, IOCType, ScoreHistory, db, get_severity

logger = logging.getLogger(__name__)

iocs_bp = Blueprint("iocs", __name__)

SEVERITY_RANGES = {
    "Low": (0, 30),
    "Medium": (31, 60),
    "High": (61, 85),
    "Critical": (86, 100),
}


def _severity_filter(query, severity):
    if not severity or severity not in SEVERITY_RANGES:
        return query
    low, high = SEVERITY_RANGES[severity]
    return query.filter(IOC.threat_score >= low, IOC.threat_score <= high)


@iocs_bp.route("/api/iocs", methods=["GET"])
def list_iocs():
    ioc_type = request.args.get("type")
    severity = request.args.get("severity")
    country = request.args.get("country")
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "threat_score")
    has_coords = request.args.get("has_coords", "").lower() == "true"
    page = max(1, request.args.get("page", 1, type=int))
    limit = min(500, max(1, request.args.get("limit", 25, type=int)))

    query = IOC.query

    if ioc_type:
        try:
            query = query.filter(IOC.ioc_type == IOCType(ioc_type))
        except ValueError:
            return jsonify({"error": f"Invalid type: {ioc_type}"}), 400

    query = _severity_filter(query, severity)

    if country:
        query = query.filter(IOC.country.ilike(f"%{country}%"))

    if search:
        query = query.filter(IOC.value.ilike(f"%{search}%"))

    if has_coords:
        query = query.filter(
            IOC.latitude.isnot(None),
            IOC.longitude.isnot(None),
        )

    if sort == "last_seen":
        query = query.order_by(IOC.last_seen.desc())
    else:
        query = query.order_by(IOC.threat_score.desc(), IOC.last_seen.desc())
    total = query.count()
    iocs = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify(
        {
            "iocs": [ioc.to_dict() for ioc in iocs],
            "total": total,
            "page": page,
        }
    )


@iocs_bp.route("/api/iocs/<uuid:ioc_id>", methods=["GET"])
def get_ioc(ioc_id):
    ioc = db.session.get(IOC, ioc_id)
    if not ioc:
        return jsonify({"error": "IOC not found"}), 404
    return jsonify(ioc.to_dict(include_history=True))


@iocs_bp.route("/api/stats", methods=["GET"])
def get_stats():
    total = IOC.query.count()
    critical = IOC.query.filter(IOC.threat_score >= 86).count()
    high = IOC.query.filter(IOC.threat_score >= 61, IOC.threat_score <= 85).count()
    countries = (
        db.session.query(func.count(func.distinct(IOC.country)))
        .filter(IOC.country.isnot(None))
        .scalar()
    )
    last_updated = db.session.query(func.max(IOC.last_seen)).scalar()
    ip_count = IOC.query.filter(IOC.ioc_type == IOCType.ip).count()
    domain_count = IOC.query.filter(IOC.ioc_type == IOCType.domain).count()
    url_count = IOC.query.filter(IOC.ioc_type == IOCType.url).count()

    return jsonify(
        {
            "total_iocs": total,
            "critical_count": critical,
            "high_count": high,
            "countries_count": countries or 0,
            "ip_count": ip_count,
            "domain_count": domain_count,
            "url_count": url_count,
            "last_updated": last_updated.isoformat() if last_updated else None,
        }
    )


@iocs_bp.route("/api/export", methods=["GET"])
def export_iocs():
    fmt = request.args.get("format", "csv")
    if fmt != "csv":
        return jsonify({"error": "Only csv format is supported"}), 400

    iocs = IOC.query.order_by(IOC.threat_score.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "value",
            "ioc_type",
            "threat_score",
            "severity",
            "abuse_confidence",
            "feed_count",
            "country",
            "latitude",
            "longitude",
            "tags",
            "first_seen",
            "last_seen",
        ]
    )
    for ioc in iocs:
        writer.writerow(
            [
                str(ioc.id),
                ioc.value,
                ioc.ioc_type.value,
                ioc.threat_score,
                get_severity(ioc.threat_score),
                ioc.abuse_confidence,
                ioc.feed_count,
                ioc.country,
                ioc.latitude,
                ioc.longitude,
                ioc.tags,
                ioc.first_seen.isoformat() if ioc.first_seen else "",
                ioc.last_seen.isoformat() if ioc.last_seen else "",
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename=iocs_{datetime.now(timezone.utc).strftime("%Y%m%d")}.csv'
        },
    )

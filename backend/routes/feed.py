import logging
import threading

from flask import Blueprint, current_app, jsonify, request

from feeds.abuseipdb import run_abuseipdb_enrichment
from feeds.feed_state import is_feed_running, set_feed_running, update_feed_log
from feeds.otx import run_otx_ingestion
from models import FeedLog, IOC, IOCType, db

logger = logging.getLogger(__name__)

feed_bp = Blueprint("feed", __name__)

FEED_META = {
    "otx": {"name": "OTX", "label": "AlienVault OTX"},
    "abuseipdb": {"name": "AbuseIPDB", "label": "AbuseIPDB"},
}


def _count_otx_iocs():
    return IOC.query.filter(IOC.raw_data["otx_pulses"].isnot(None)).count()


def _count_abuseipdb_iocs():
    return IOC.query.filter(IOC.abuse_confidence.isnot(None)).count()


def _feed_status_entry(feed_key):
    meta = FEED_META[feed_key]
    log = FeedLog.query.filter_by(feed_name=feed_key).first()
    running = is_feed_running(feed_key)
    total = _count_otx_iocs() if feed_key == "otx" else _count_abuseipdb_iocs()
    return {
        "feed": feed_key,
        "name": meta["name"],
        "label": meta["label"],
        "status": "active" if log and log.last_run else "idle",
        "running": running,
        "last_run": log.last_run.isoformat() if log and log.last_run else None,
        "iocs_ingested_last_run": log.iocs_ingested if log else 0,
        "total_iocs": total,
    }


def _run_feed_job(app, feed_key):
    with app.app_context():
        set_feed_running(feed_key, True)
        try:
            if feed_key == "otx":
                run_otx_ingestion()
            elif feed_key == "abuseipdb":
                run_abuseipdb_enrichment()
        except Exception:
            logger.exception("Manual feed run failed: %s", feed_key)
            update_feed_log(feed_key, 0)
        finally:
            set_feed_running(feed_key, False)


@feed_bp.route("/api/feed-status", methods=["GET"])
def feed_status():
    return jsonify(
        {
            "feeds": [
                _feed_status_entry("otx"),
                _feed_status_entry("abuseipdb"),
            ]
        }
    )


@feed_bp.route("/api/feed/run", methods=["POST"])
def run_feed():
    data = request.get_json(silent=True) or {}
    feed_key = data.get("feed")
    if feed_key not in FEED_META:
        return jsonify({"error": "Invalid feed. Use 'otx' or 'abuseipdb'"}), 400
    if is_feed_running(feed_key):
        return jsonify({"error": f"{feed_key} is already running"}), 409

    app = current_app._get_current_object()
    thread = threading.Thread(target=_run_feed_job, args=(app, feed_key), daemon=True)
    thread.start()
    return jsonify({"status": "started", "feed": feed_key})

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

from feeds.abuseipdb import run_abuseipdb_enrichment
from feeds.feed_state import set_feed_running
from feeds.otx import run_otx_ingestion

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler(app: Flask):
    """Register and start APScheduler jobs within the Flask app context."""

    def otx_job():
        with app.app_context():
            logger.info("Scheduler: starting OTX feed pull")
            set_feed_running("otx", True)
            try:
                run_otx_ingestion()
            except Exception:
                logger.exception("OTX ingestion job failed")
            finally:
                set_feed_running("otx", False)

    def abuseipdb_job():
        with app.app_context():
            logger.info("Scheduler: starting AbuseIPDB enrichment")
            set_feed_running("abuseipdb", True)
            try:
                run_abuseipdb_enrichment()
            except Exception:
                logger.exception("AbuseIPDB enrichment job failed")
            finally:
                set_feed_running("abuseipdb", False)

    scheduler.add_job(
        otx_job,
        "interval",
        minutes=30,
        id="otx_ingestion",
        replace_existing=True,
    )
    scheduler.add_job(
        abuseipdb_job,
        "interval",
        minutes=60,
        id="abuseipdb_enrichment",
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started (OTX every 30m, AbuseIPDB every 60m)")

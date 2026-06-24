import logging
import threading

logger = logging.getLogger(__name__)

_running = {"otx": False, "abuseipdb": False}
_lock = threading.Lock()


def set_feed_running(feed_name, running):
    with _lock:
        _running[feed_name] = running


def is_feed_running(feed_name):
    with _lock:
        return _running.get(feed_name, False)


def any_feed_running():
    with _lock:
        return any(_running.values())


def update_feed_log(feed_name, iocs_ingested):
    from datetime import datetime, timezone

    from models import FeedLog, db

    log = FeedLog.query.filter_by(feed_name=feed_name).first()
    if not log:
        log = FeedLog(feed_name=feed_name)
        db.session.add(log)
    log.last_run = datetime.now(timezone.utc)
    log.iocs_ingested = iocs_ingested
    db.session.commit()
    logger.info("Feed log updated: %s ingested %d", feed_name, iocs_ingested)

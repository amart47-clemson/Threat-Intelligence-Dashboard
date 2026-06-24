import logging
import time

import requests

logger = logging.getLogger(__name__)

GEOIP_RATE_LIMIT = 40  # max requests per minute
_geoip_last_request = 0.0
_geoip_request_count = 0
_geoip_window_start = 0.0


def base_score_from_pulses(pulse_count):
    if pulse_count == 0:
        return 10
    if pulse_count <= 3:
        return 30
    if pulse_count <= 9:
        return 50
    return 70


def calculate_threat_score(base_score, abuse_confidence=None, feed_count=1):
    abuse = (abuse_confidence or 0) * 0.4
    feed_bonus = feed_count * 10
    return min(100.0, base_score + abuse + feed_bonus)


def _geoip_rate_limit_wait():
    global _geoip_last_request, _geoip_request_count, _geoip_window_start
    now = time.time()
    if now - _geoip_window_start >= 60:
        _geoip_window_start = now
        _geoip_request_count = 0
    if _geoip_request_count >= GEOIP_RATE_LIMIT:
        sleep_time = 60 - (now - _geoip_window_start)
        if sleep_time > 0:
            logger.info("GeoIP rate limit reached, sleeping %.1fs", sleep_time)
            time.sleep(sleep_time)
        _geoip_window_start = time.time()
        _geoip_request_count = 0
    _geoip_request_count += 1
    _geoip_last_request = time.time()


def enrich_geoip(ip_address):
    """Look up lat/lon/country for an IP via ip-api.com."""
    _geoip_rate_limit_wait()
    url = f"http://ip-api.com/json/{ip_address}"
    try:
        logger.info("GeoIP lookup for %s", ip_address)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "success":
            logger.warning("GeoIP lookup failed for %s: %s", ip_address, data.get("message"))
            return None
        return {
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "country": data.get("countryCode"),
        }
    except requests.RequestException as exc:
        logger.error("GeoIP request error for %s: %s", ip_address, exc)
        return None

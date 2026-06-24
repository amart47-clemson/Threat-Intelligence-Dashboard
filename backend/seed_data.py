"""Seed sample IOCs for local API testing. Run from backend/: python seed_data.py"""
from datetime import datetime, timezone, timedelta

from flask import Flask

from config import Config
from models import IOC, IOCType, ScoreHistory, db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

SAMPLES = [
    {
        "value": "185.220.101.45",
        "ioc_type": IOCType.ip,
        "threat_score": 92.0,
        "abuse_confidence": 85.0,
        "feed_count": 3,
        "country": "DE",
        "latitude": 51.2993,
        "longitude": 9.4910,
        "tags": "tor,malware",
    },
    {
        "value": "evil-domain.example.com",
        "ioc_type": IOCType.domain,
        "threat_score": 55.0,
        "abuse_confidence": None,
        "feed_count": 2,
        "country": None,
        "latitude": None,
        "longitude": None,
        "tags": "phishing",
    },
    {
        "value": "45.33.32.156",
        "ioc_type": IOCType.ip,
        "threat_score": 72.0,
        "abuse_confidence": 60.0,
        "feed_count": 2,
        "country": "US",
        "latitude": 37.751,
        "longitude": -97.822,
        "tags": "scanner,botnet",
    },
    {
        "value": "http://malicious-site.test/payload",
        "ioc_type": IOCType.url,
        "threat_score": 40.0,
        "abuse_confidence": None,
        "feed_count": 1,
        "country": None,
        "latitude": None,
        "longitude": None,
        "tags": "malware",
    },
]

with app.app_context():
    now = datetime.now(timezone.utc)
    for sample in SAMPLES:
        existing = IOC.query.filter_by(value=sample["value"]).first()
        if existing:
            print(f"Skipping existing: {sample['value']}")
            continue
        ioc = IOC(
            **sample,
            first_seen=now - timedelta(days=7),
            last_seen=now,
            raw_data={"seed": True},
        )
        db.session.add(ioc)
        db.session.flush()
        for days_ago, score in [(7, sample["threat_score"] - 10), (3, sample["threat_score"] - 5), (0, sample["threat_score"])]:
            db.session.add(
                ScoreHistory(
                    ioc_id=ioc.id,
                    threat_score=max(0, score),
                    recorded_at=now - timedelta(days=days_ago),
                )
            )
        print(f"Seeded: {sample['value']}")

    db.session.commit()
    print("Seed complete.")

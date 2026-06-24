import enum
import uuid
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID

db = SQLAlchemy()


class IOCType(enum.Enum):
    ip = "ip"
    domain = "domain"
    url = "url"
    hash = "hash"


class IOC(db.Model):
    __tablename__ = "iocs"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = db.Column(db.String(512), nullable=False, unique=True, index=True)
    ioc_type = db.Column(Enum(IOCType), nullable=False)
    threat_score = db.Column(db.Float, nullable=False, default=0.0)
    abuse_confidence = db.Column(db.Float, nullable=True)
    feed_count = db.Column(db.Integer, nullable=False, default=1)
    country = db.Column(db.String(64), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    tags = db.Column(db.String(1024), nullable=True)
    first_seen = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    raw_data = db.Column(JSONB, nullable=True, default=dict)

    score_history = db.relationship(
        "ScoreHistory", backref="ioc", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, include_history=False):
        data = {
            "id": str(self.id),
            "value": self.value,
            "ioc_type": self.ioc_type.value,
            "threat_score": self.threat_score,
            "abuse_confidence": self.abuse_confidence,
            "feed_count": self.feed_count,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "tags": self.tags.split(",") if self.tags else [],
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "severity": get_severity(self.threat_score),
        }
        if include_history:
            data["score_history"] = [
                h.to_dict()
                for h in self.score_history.order_by(ScoreHistory.recorded_at.asc())
            ]
        return data


class FeedLog(db.Model):
    __tablename__ = "feed_log"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_name = db.Column(db.String(32), nullable=False, unique=True, index=True)
    last_run = db.Column(db.DateTime(timezone=True), nullable=True)
    iocs_ingested = db.Column(db.Integer, nullable=False, default=0)

    def to_dict(self):
        return {
            "feed_name": self.feed_name,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "iocs_ingested": self.iocs_ingested,
        }


class ScoreHistory(db.Model):
    __tablename__ = "score_history"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ioc_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("iocs.id"), nullable=False, index=True
    )
    threat_score = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "ioc_id": str(self.ioc_id),
            "threat_score": self.threat_score,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


def get_severity(score):
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Medium"
    if score <= 85:
        return "High"
    return "Critical"

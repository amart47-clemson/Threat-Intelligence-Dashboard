import os
from pathlib import Path

from dotenv import load_dotenv

_backend_env = Path(__file__).resolve().parent / ".env"
_root_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_backend_env)
load_dotenv(_root_env)


def _env(key, default=""):
    return os.getenv(key, default).strip()


class Config:
    DATABASE_URL = _env(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/threatintel"
    )
    OTX_API_KEY = _env("OTX_API_KEY")
    ABUSEIPDB_API_KEY = _env("ABUSEIPDB_API_KEY")
    FLASK_ENV = _env("FLASK_ENV", "development")
    CORS_ORIGIN = _env("CORS_ORIGIN", "http://localhost:5173")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

import os
from pathlib import Path

from dotenv import load_dotenv

_backend_env = Path(__file__).resolve().parent / ".env"
_root_env = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_backend_env)
load_dotenv(_root_env)


class Config:
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/threatintel"
    )
    OTX_API_KEY = os.getenv("OTX_API_KEY", "")
    ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

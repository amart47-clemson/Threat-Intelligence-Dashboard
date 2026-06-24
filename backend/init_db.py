"""Initialize database tables. Run from backend/: python init_db.py"""
import logging

from flask import Flask

from config import Config
from models import db

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")

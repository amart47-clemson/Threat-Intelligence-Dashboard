import logging
import os
import sys

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models import db
from routes.feed import feed_bp
from routes.iocs import iocs_bp
from routes.lookup import lookup_bp
from scheduler import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=[Config.CORS_ORIGIN])

    @app.route("/")
    def health():
        return jsonify({"status": "ok", "service": "threat-intel-api"})

    db.init_app(app)
    app.register_blueprint(iocs_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(lookup_bp)

    with app.app_context():
        db.create_all()
        logger.info("Database tables created/verified")

    # Avoid double scheduler start when Flask debug reloader spawns a child process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or Config.FLASK_ENV != "development":
        start_scheduler(app)

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=Config.FLASK_ENV == "development")

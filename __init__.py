from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
import os

mongo = PyMongo()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # MongoDB Configuration
    app.config["MONGO_URI"] = os.getenv("MONGO_URI")  # Or use your Atlas URI

    mongo.init_app(app)
    CORS(app)

    # ✅ Import and register routes without `backend.`
    from routes.auth import auth_bp
    from routes.owner import owner_bp
    from routes.worker import worker_bp
    from routes.tender import tender_bp
    from routes.auction import auction_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(owner_bp, url_prefix="/api/owner")
    app.register_blueprint(worker_bp, url_prefix="/api/worker")
    app.register_blueprint(tender_bp, url_prefix="/api/tenders")
    app.register_blueprint(auction_bp, url_prefix="/api/auctions")

    return app

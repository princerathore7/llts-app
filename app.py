from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.mongo import mongo
from backend.routes.auth import auth_bp
from backend.routes.worker import worker_bp
from backend.routes.tender import tender_bp
from backend.routes.auction import auction_bp
from backend.routes.owner import owner_bp
from backend.routes.admin import admin_bp
from backend.routes.report import report_bp
from backend.routes.token import token_bp
from backend.routes.razorpay_webhook import razorpay_bp
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv

# 🔐 Load environment variables
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ MongoDB Config
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo.init_app(app)

# ✅ JWT Config
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY") or "secret"
jwt = JWTManager(app)

# ✅ Allowed frontend origins
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8000",
    "http://localhost:8000"
]

# ✅ CORS Setup
CORS(app, origins=ALLOWED_ORIGINS,
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers="Content-Type",
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

# ✅ Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(worker_bp, url_prefix='/api/worker')
app.register_blueprint(tender_bp, url_prefix='/api')
app.register_blueprint(auction_bp, url_prefix='/api')
app.register_blueprint(owner_bp, url_prefix='/api/owner')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(report_bp, url_prefix='/api')
app.register_blueprint(token_bp, url_prefix="/api/token")
app.register_blueprint(razorpay_bp)

# ✅ JWT Error Handling
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({"error": "Missing or invalid JWT token"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Invalid token"}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401

# ✅ 404 Handler
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "API route not found"}), 404



# ✅ Start Server
if __name__ == "__main__":
    app.run(debug=True)

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from mongo import mongo
from routes.auth import auth_bp
from routes.worker import worker_bp
from routes.tender import tender_bp
from routes.auction import auction_bp
from routes.owner import owner_bp
from routes.admin import admin_bp
from routes.report import report_bp
from routes.token import token_bp
from routes.razorpay_webhook import razorpay_bp

# ✅ Load .env from parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ MongoDB Config
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo.init_app(app)

# ✅ JWT Config
app.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY") or "secret"
jwt = JWTManager(app)

# ✅ Allowed frontend origins (from .env)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

# ✅ CORS Setup - UNIVERSAL
CORS(app,
     resources={r"/*": {"origins": ALLOWED_ORIGINS}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type"],
     methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

# ✅ Add CORS headers after every response
@app.after_request
def apply_cors_headers(response):
    origin = request.headers.get("Origin", "")
    for allowed in ALLOWED_ORIGINS:
        if origin.startswith(allowed):  # use startswith instead of exact match
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            break
    return response


# ✅ Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(worker_bp, url_prefix='/api/worker')
app.register_blueprint(tender_bp, url_prefix='/api')
app.register_blueprint(auction_bp, url_prefix='/api')
app.register_blueprint(owner_bp, url_prefix='/api/owner')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(report_bp, url_prefix='/api')
app.register_blueprint(token_bp, url_prefix='/api/token')
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
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


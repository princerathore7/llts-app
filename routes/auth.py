from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask_jwt_extended import create_access_token
from flask_cors import cross_origin, CORS

import os
from dotenv import load_dotenv
from datetime import datetime
from mongo import mongo
from models.token import init_token_record

# ✅ Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise Exception("❌ SECRET_KEY not found. Please check your .env file and restart.")

# ✅ Allowed frontend origins (local + deployed)
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://llts-app.onrender.com"
]

auth_bp = Blueprint('auth', __name__)
CORS(auth_bp, origins=ALLOWED_ORIGINS, supports_credentials=True)

# ===================== SIGNUP =====================
@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def signup():
    if request.method == 'OPTIONS':
        return '', 200

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role')
    name = data.get('name')
    phone = data.get('phone')  # ✅ Add this line

    if not all([username, password, email, role, name, phone]):
        return jsonify({"error": "Missing fields"}), 400

    if mongo.db.users.find_one({'username': username}):
        return jsonify({"error": "Username already exists"}), 409

    hashed_password = generate_password_hash(password)

    user_data = {
        "username": username,
        "password": hashed_password,
        "email": email,
        "role": role,
        "name": name,
        "phone": phone,  # ✅ Store phone
        "status": "active",
        "created_at": datetime.utcnow()
    }

    if role.lower() == 'worker':
        user_data.update({
            "location": "",
            "experience": 0,
            "skills": [],
            "tendersApplied": 0,
            "auctionsParticipated": 0,
            "totalEarnings": 0
        })

    result = mongo.db.users.insert_one(user_data)
    new_user_id = result.inserted_id

    init_token_record(str(new_user_id), role.lower())

    return jsonify({"message": "Signup successful"}), 201

# ===================== LOGIN =====================
@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def login():
    if request.method == 'OPTIONS':
        return '', 200  # ✅ Preflight fix for CORS

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    # ✅ Admin Backdoor login
    if username == "admin" and password == os.getenv("ADMIN_PASS", "admin123"):
        access_token = create_access_token(identity="admin-override", additional_claims={
            "role": "admin",
            "username": "admin",
            "id": "admin"
        })
        return jsonify({
            "token": access_token,
            "role": "admin"
        }), 200

    # ✅ Normal user login
    user = mongo.db.users.find_one({
        "$or": [
            {"username": username},
            {"email": username}
        ]
    })

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("status") == "disabled":
        return jsonify({"error": "Your account has been disabled by admin."}), 403

    if not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user['_id']), additional_claims={
        "role": user["role"],
        "username": user["username"],
        "id": str(user['_id'])
    })

    return jsonify({
        "token": access_token,
        "role": user["role"].lower()
    }), 200

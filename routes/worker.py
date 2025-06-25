from flask import Blueprint, request, jsonify
from bson import ObjectId
from mongo import mongo
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from datetime import datetime, timedelta
import os
from werkzeug.security import check_password_hash
from models.token import get_token_record, decrement_token
from dotenv import load_dotenv

# ✅ Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(dotenv_path=env_path)

worker_bp = Blueprint('worker', __name__)

# ========================= 🔐 WORKER LOGIN =========================
@worker_bp.route('/login', methods=['POST', 'OPTIONS'])
def worker_login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = mongo.db.users.find_one({"username": username, "role": "worker"})

    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.get("status") == "disabled":
        return jsonify({"error": "Your account has been disabled by admin."}), 403

    if not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # ✅ Give 150 tokens to first-time login if not present
    existing_token_doc = mongo.db.tokens.find_one({"user_id": str(user["_id"])})
    if not existing_token_doc:
        mongo.db.tokens.insert_one({
            "user_id": str(user["_id"]),
            "role": "worker",
            "tokens": 150,
            "issued_at": datetime.utcnow()
        })

    access_token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=timedelta(days=1)
    )

    return jsonify({
        "token": access_token,
        "role": user["role"]
    }), 200

# ========================= 👤 WORKER PROFILE =========================
@worker_bp.route('/profile', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_worker_profile():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    worker_id = get_jwt_identity()
    worker = mongo.db.users.find_one({'_id': ObjectId(worker_id), 'role': 'worker'})

    if not worker:
        return jsonify({'error': 'Worker not found'}), 404

    return jsonify({
        "id": str(worker['_id']),
        "name": worker.get('name'),
        "role": worker.get('role'),
        "location": worker.get('location', ''),
        "email": worker.get('email'),
        "experience": worker.get('experience', 0),
        "skills": worker.get('skills', '').split(',') if isinstance(worker.get('skills'), str) else worker.get('skills', []),
        "tendersApplied": worker.get('tendersApplied', 0),
        "auctionsParticipated": worker.get('auctionsParticipated', 0),
        "totalEarnings": worker.get('totalEarnings', 0)
    })

# ========================= 📋 ACTIVE JOBS =========================
@worker_bp.route('/api/worker/active_jobs/<worker_id>', methods=['GET'])
def get_active_jobs(worker_id):
    tenders = mongo.db.tenders.find({'assigned_worker_id': worker_id})
    jobs = [{
        "id": str(t['_id']),
        "title": t.get('title'),
        "status": t.get('status', 'assigned')
    } for t in tenders]
    return jsonify({"jobs": jobs}), 200

# ========================= 📄 GET ALL TENDERS & AUCTIONS =========================
@worker_bp.route('/api/get-tenders', methods=['GET'])
def get_all_tenders_and_auctions():
    combined_list = []

    tenders = mongo.db.tenders.find({"status": {"$ne": "disabled"}})
    for tender in tenders:
        combined_list.append({
            "id": str(tender["_id"]),
            "title": tender.get("title"),
            "description": tender.get("description"),
            "location": tender.get("location"),
            "budget": tender.get("budget"),
            "category": tender.get("category"),
            "deadline": tender.get("deadline").strftime('%Y-%m-%d') if tender.get("deadline") else None,
            "type": "tender"
        })

    auctions = mongo.db.auctions.find({"status": {"$ne": "disabled"}})
    for auction in auctions:
        combined_list.append({
            "id": str(auction["_id"]),
            "title": auction.get("title"),
            "description": auction.get("description"),
            "item_name": auction.get("item_name"),
            "starting_bid": auction.get("starting_bid"),
            "location": auction.get("location"),
            "end_date": auction.get("end_date").strftime('%Y-%m-%d') if auction.get("end_date") else None,
            "type": "auction"
        })

    return jsonify({"tenders": combined_list}), 200

# ========================= ✅ APPLY FOR TENDER =========================
@worker_bp.route("/apply-tender", methods=["POST", "OPTIONS"])
@jwt_required()
def apply_tender():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        print("📥 Received Apply Data:", data)

        tender_id = data.get("tender_id")
        worker_name = data.get("worker_name")
        mobile = data.get("contact")
        quoted_price = data.get("quoted_price")
        message = data.get("message")

        if not tender_id:
            return jsonify({"error": "Tender ID is required"}), 400

        tender_obj_id = ObjectId(tender_id)
        tender = mongo.db.tenders.find_one({"_id": tender_obj_id})
        if not tender:
            return jsonify({"error": "Tender not found"}), 404

        if tender.get("status") == "disabled":
            return jsonify({"error": "Tender is no longer active"}), 403

        # ✅ Check token balance
        token_info = get_token_record(user_id, "worker")
        if not token_info or token_info.get("tokens", 0) < 3:
            return jsonify({"error": "You need at least 3 tokens to apply. Please recharge."}), 402

        # ✅ Check if already applied
        existing = mongo.db.applications.find_one({
            "tender_id": tender_obj_id,
            "worker_id": ObjectId(user_id)
        })
        if existing:
            return jsonify({"error": "Already applied."}), 409

        # ✅ Save application
        mongo.db.applications.insert_one({
            "tender_id": tender_obj_id,
            "worker_id": ObjectId(user_id),
            "owner_id": str(tender["created_by"]),
            "worker_name": worker_name,
            "contact": mobile,
            "quoted_price": quoted_price,
            "message": message,
            "status": "pending",
            "applied_at": datetime.utcnow()
        })

        # ✅ Decrement 3 tokens after success
        mongo.db.tokens.update_one(
            {"user_id": str(user_id), "role": "worker"},
            {"$inc": {"tokens": -3}}
        )

        return jsonify({"msg": "Application submitted successfully"}), 200

    except Exception as e:
        print("❌ ERROR in apply-tender:", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500
# ========================= 🔢 GET COUNT OF APPLIED TENDERS =========================
@worker_bp.route('/applied-count', methods=['GET'])
@jwt_required()
def get_applied_tender_count():
    try:
        worker_id = get_jwt_identity()
        count = mongo.db.applications.count_documents({
            "worker_id": ObjectId(worker_id)
        })
        return jsonify({"count": count}), 200
    except Exception as e:
        print("❌ Error in counting applications:", str(e))
        return jsonify({"error": "Server error"}), 500
# ========================= 🔢 worekr profile=========================
@worker_bp.route('/all-profiles', methods=['GET'])
def get_all_worker_profiles():
    workers = mongo.db.users.find({"role": "worker"})
    result = []
    for w in workers:
        result.append({
            "id": str(w["_id"]),
            "name": w.get("name", "Unnamed"),
            "skill": w.get("skills", ""),
            "experience": w.get("experience", 0),
            "location": w.get("location", ""),
            "img": w.get("img", "default-worker.jpg"),  # Optional image field
            "icon": "bi-person-workspace"  # For frontend
        })
    return jsonify(result), 200

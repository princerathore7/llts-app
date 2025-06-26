from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_cors import cross_origin
from datetime import datetime

from mongo import mongo
from models.token import init_token_record

owner_bp = Blueprint('owner_bp', __name__)

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://llts-app.onrender.com"
]

# ✅ Owner Profile
@owner_bp.route('/api/owner/profile', methods=['GET'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def get_owner_profile():
    owner_id = get_jwt_identity()
    print("🔍 Owner ID:", owner_id)
    owner = mongo.db.users.find_one({'_id': ObjectId(owner_id), 'role': 'owner'})

    if not owner:
        return jsonify({"status": "error", "message": "Owner not found"}), 404
    if owner.get("status") == "disabled":
        return jsonify({"status": "error", "message": "Your account is disabled"}), 403

    return jsonify({
        "status": "success",
        "profile": {
            "id": str(owner['_id']),
            "name": owner.get('name'),
            "role": owner.get('role'),
            "location": owner.get('location', ''),
            "email": owner.get('email')
        }
    }), 200

# ✅ Post New Tender
@owner_bp.route('/api/owner/tenders', methods=['POST', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def create_tender():
    if request.method == "OPTIONS":
        return '', 200

    try:
        owner_id = get_jwt_identity()
        owner = mongo.db.users.find_one({"_id": ObjectId(owner_id), "role": "owner"})
        if not owner:
            return jsonify({"status": "error", "message": "Owner not found"}), 404
        if owner.get("status") == "disabled":
            return jsonify({"status": "error", "message": "Your account has been disabled by admin."}), 403

        data = request.get_json()
        required_fields = ["title", "budget", "deadline", "description"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        tender = {
            "title": data["title"],
            "budget": data["budget"],
            "deadline": data["deadline"],
            "description": data["description"],
            "created_by": str(owner["_id"]),
            "status": "active",
            "created_at": datetime.utcnow()
        }

        result = mongo.db.tenders.insert_one(tender)
        tender["_id"] = str(result.inserted_id)

        return jsonify({"status": "success", "tender": tender}), 201

    except Exception as e:
        print("❌ Error in create_tender:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ Get Owner's Tenders
@owner_bp.route('/api/owner/tenders', methods=['GET', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def get_owner_tenders():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        owner_id = get_jwt_identity()
        owner = mongo.db.users.find_one({"_id": ObjectId(owner_id), "role": "owner"})
        if not owner:
            return jsonify({"status": "error", "message": "Owner not found"}), 404
        if owner.get("status") == "disabled":
            return jsonify({"status": "error", "message": "Your account is disabled"}), 403

        tenders = list(mongo.db.tenders.find({"created_by": str(owner_id)}))
        for t in tenders:
            t["_id"] = str(t["_id"])

        return jsonify({"status": "success", "count": len(tenders), "tenders": tenders}), 200

    except Exception as e:
        print("❌ Error in get_owner_tenders:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ Delete Tender
@owner_bp.route('/api/owner/delete-tender/<tender_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def delete_tender(tender_id):
    # ✅ Handle preflight request properly
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", request.headers.get("Origin", "*"))
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "DELETE,OPTIONS")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response, 200

    try:
        # ✅ Check JWT token
        verify_jwt_in_request()
        owner_id = get_jwt_identity()

        # ✅ Find tender by ID
        tender = mongo.db.tenders.find_one({"_id": ObjectId(tender_id)})
        if not tender:
            return jsonify({"status": "error", "message": "Tender not found"}), 404

        # ✅ Verify ownership
        if tender.get("created_by") != str(owner_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        # ✅ Delete tender and related applications
        mongo.db.tenders.delete_one({"_id": ObjectId(tender_id)})
        mongo.db.applications.delete_many({"tender_id": ObjectId(tender_id)})

        return jsonify({"status": "success", "message": "Tender deleted successfully"}), 200

    except Exception as e:
        print("❌ Error in delete_tender:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
# ✅ Accept Application
@owner_bp.route('/accept-application/<app_id>', methods=['PATCH', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def accept_application(app_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        app = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
        if not app:
            return jsonify({"status": "error", "message": "Application not found"}), 404

        mongo.db.applications.update_one(
            {"_id": ObjectId(app_id)},
            {"$set": {"status": "accepted"}}
        )

        tender = mongo.db.tenders.find_one({"_id": app["tender_id"]})
        mongo.db.users.update_one(
            {"_id": ObjectId(app["worker_id"])},
            {"$push": {
                "notifications": {
                    "type": "success",
                    "message": f"🎉 Your application for '{tender.get('title')}' was accepted.",
                    "timestamp": datetime.utcnow()
                }
            }}
        )

        return jsonify({"status": "success", "message": "Application accepted and worker notified"}), 200

    except Exception as e:
        print("❌ Error in accept_application:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@owner_bp.route('/reject-application/<app_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def reject_application(app_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

    try:
        # ✅ This line manually verifies JWT, only for non-OPTIONS
        verify_jwt_in_request()
        owner_id = get_jwt_identity()

        app = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
        if not app:
            return jsonify({"status": "error", "message": "Application not found"}), 404

        tender = mongo.db.tenders.find_one({"_id": app["tender_id"]})
        if not tender:
            return jsonify({"status": "error", "message": "Tender not found"}), 404

        # ✅ Optional: Check if tender was created by this owner
        if tender.get("created_by") != str(owner_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        mongo.db.users.update_one(
            {"_id": ObjectId(app["worker_id"])},
            {"$push": {
                "notifications": {
                    "type": "rejection",
                    "message": f"❌ Your application for '{tender.get('title')}' was rejected.",
                    "timestamp": datetime.utcnow()
                }
            }}
        )

        mongo.db.applications.delete_one({"_id": ObjectId(app_id)})

        return jsonify({"status": "success", "message": "Application rejected and deleted"}), 200

    except Exception as e:
        print("❌ Error in reject_application:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

# ✅ Get Applications Received for Owner's Tenders
@owner_bp.route('/api/owner/my-applications', methods=['GET', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
@jwt_required()
def get_owner_received_applications():
    if request.method == "OPTIONS":
        print("🟡 CORS Preflight: /my-applications")
        return jsonify({"message": "Preflight OK"}), 200

    try:
        owner_id = get_jwt_identity()
        print("🧾 Owner ID:", owner_id)

        applications = list(mongo.db.applications.find({
            "$or": [
                {"owner_id": str(owner_id)},
                {"owner_id": ObjectId(owner_id)}
            ]
        }))

        enriched = []
        for app in applications:
            try:
                tender = mongo.db.tenders.find_one(
                    {"_id": ObjectId(app["tender_id"])} if isinstance(app["tender_id"], str)
                    else {"_id": app["tender_id"]}
                )
                worker = mongo.db.users.find_one({"_id": ObjectId(app["worker_id"])})

                enriched.append({
                    "_id": str(app["_id"]),
                    "tender_title": tender.get("title", "N/A") if tender else "N/A",
                    "quoted_price": app.get("quoted_price", "N/A"),
                    "message": app.get("message", "No message"),
                    "status": app.get("status", "pending"),
                    "applied_at": app.get("applied_at", "-"),
                    "worker_name": worker.get("name", "Unknown") if worker else "Unknown",
                    "worker_contact": worker.get("contact", "N/A") if worker else "N/A"
                })
            except Exception as e:
                print("⚠️ Skipping application:", e)

        return jsonify({"applications": enriched}), 200

    except Exception as e:
        print("❌ Error in /my-applications:", e)
        return jsonify({"error": "Server error", "details": str(e)}), 500

from flask import Blueprint, jsonify, request
from backend.mongo import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from bson import ObjectId
from datetime import datetime
from flask_cors import cross_origin
from flask import redirect
owner_bp = Blueprint('owner_bp', __name__)

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

# ✅ Dummy Owner Profile
@owner_bp.route('/api/owner/profile', methods=['GET'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def get_owner_profile():
    owner_id = get_jwt_identity()
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


# ✅ Create Tender
@owner_bp.route('/api/owner/tenders', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def create_tender():
    if request.method == "OPTIONS":
        return '', 200

    owner_id = get_jwt_identity()
    owner = mongo.db.users.find_one({"_id": ObjectId(owner_id), "role": "owner"})
    if not owner:
        return jsonify({"status": "error", "message": "Owner not found"}), 404
    if owner.get("status") == "disabled":
        return jsonify({"status": "error", "message": "Your account has been disabled by admin."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON data"}), 400

    required_fields = ["title", "budget", "deadline", "description"]
    if not all(field in data for field in required_fields):
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


# ✅ Get Tenders Posted by This Owner
@owner_bp.route('/api/owner/tenders', methods=['GET', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def get_owner_tenders():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        verify_jwt_in_request_(optional=True)
        owner_id = get_jwt_identity()

        if not owner_id:
            return jsonify({"status": "error", "message": "Missing or invalid token"}), 401

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
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500


# ✅ Delete Tender
@owner_bp.route('/api/owner/delete-tender/<tender_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def delete_tender(tender_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        owner_id = get_jwt_identity()
        tender = mongo.db.tenders.find_one({"_id": ObjectId(tender_id)})
        if not tender:
            return jsonify({"status": "error", "message": "Tender not found"}), 404

        if tender.get("created_by") != str(owner_id):
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        mongo.db.tenders.delete_one({"_id": ObjectId(tender_id)})
        mongo.db.applications.delete_many({"tender_id": ObjectId(tender_id)})

        return jsonify({"status": "success", "message": "Tender and related applications deleted"}), 200

    except Exception as e:
        print("❌ Error in delete_tender:", str(e))
        return jsonify({"status": "error", "message": "Internal error", "details": str(e)}), 500


# ✅ Get Worker Applications by Owner ID
@owner_bp.route('/api/owner/applications/<owner_id>', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def get_worker_applications(owner_id):
    if request.method == "OPTIONS":
        return '', 200

    if get_jwt_identity() != owner_id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    try:
        tenders = list(mongo.db.tenders.find({"created_by": owner_id}))
        tender_ids = [ObjectId(t["_id"]) for t in tenders]
        if not tender_ids:
            return jsonify({"status": "success", "applications": []}), 200

        applications = list(mongo.db.applications.find({"tender_id": {"$in": tender_ids}}))
        enriched = []

        for app in applications:
            worker = mongo.db.users.find_one({"_id": ObjectId(app["worker_id"])})
            tender = mongo.db.tenders.find_one({"_id": app["tender_id"]})
            enriched.append({
                "_id": str(app["_id"]),
                "tender_id": str(app["tender_id"]),
                "worker_id": str(app["worker_id"]),
                "status": app.get("status", "pending"),
                "applied_at": app.get("applied_at", "-"),
                "quoted_price": app.get("quoted_price", "N/A"),
                "message": app.get("message", "No message"),
                "worker_name": worker.get("name") if worker else "Unknown",
                "worker_email": worker.get("email") if worker else "N/A",
                "contact": worker.get("contact") if worker else "",
                "tender_title": tender.get("title") if tender else "N/A"
            })

        return jsonify({"status": "success", "applications": enriched}), 200

    except Exception as e:
        print("❌ Error in get_worker_applications:", str(e))
        return jsonify({"status": "error", "message": "Internal server error", "details": str(e)}), 500


# ✅ Accept Application
@owner_bp.route('/accept-application/<app_id>', methods=['PATCH', 'OPTIONS'])
@jwt_required(optional=True)
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
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
        return jsonify({"status": "error", "message": "Internal error", "details": str(e)}), 500


# ✅ Reject Application
@owner_bp.route('/reject-application/<app_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required(optional=True)
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def reject_application(app_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        app = mongo.db.applications.find_one({"_id": ObjectId(app_id)})
        if not app:
            return jsonify({"status": "error", "message": "Application not found"}), 404

        tender = mongo.db.tenders.find_one({"_id": app["tender_id"]})
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
        return jsonify({"status": "error", "message": "Internal error", "details": str(e)}), 500
@owner_bp.route('/delete-tender-safe', methods=['POST'])
def delete_tender_safe():
    try:
        tender_id = request.form.get('tender_id')
        if not tender_id:
            return "Tender ID missing", 400

        mongo.db.tenders.delete_one({"_id": ObjectId(tender_id)})
        mongo.db.applications.delete_many({"tender_id": ObjectId(tender_id)})

        # Redirect back to tender history
        return redirect("http://127.0.0.1:5500/owner-posted.html")

    except Exception as e:
        print("❌ Safe delete error:", str(e))
        return "Failed to delete tender", 500
    # ✅ Final Fix: Missing Received Applications Route
# ✅ Final CORS-compatible route for Received Applications
# ✅ GET: Received Applications for Logged-in Owner
from bson import ObjectId

@owner_bp.route('/received-applications', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def received_applications():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    try:
        owner_id = get_jwt_identity()
        owner_oid = ObjectId(owner_id)

        # ✅ Step 1: Find tenders by this owner
        tenders = list(mongo.db.tenders.find({"created_by": owner_oid}))
        tender_ids = [t["_id"] for t in tenders]  # keep ObjectId

        if not tender_ids:
            return jsonify({"status": "success", "applications": []}), 200

        # ✅ Step 2: Find applications linked to those tenders
        applications = list(mongo.db.applications.find({
            "tender_id": {"$in": tender_ids}
        }))

        enriched = []
        for app in applications:
            worker = mongo.db.users.find_one({"_id": ObjectId(app["worker_id"])})
            tender = mongo.db.tenders.find_one({"_id": app["tender_id"]})

            enriched.append({
                "_id": str(app["_id"]),
                "tender_id": str(app["tender_id"]),
                "worker_id": str(app["worker_id"]),
                "status": app.get("status", "pending"),
                "applied_at": app.get("applied_at", "-"),
                "quoted_price": app.get("quoted_price", "N/A"),
                "message": app.get("message", "No message"),
                "worker_name": worker.get("name") if worker else "Unknown",
                "worker_email": worker.get("email") if worker else "N/A",
                "contact": worker.get("contact") if worker else "N/A",
                "tender_title": tender.get("title") if tender else "N/A"
            })

        return jsonify({"status": "success", "applications": enriched}), 200

    except Exception as e:
        print("❌ Error in /received-applications:", str(e))
        return jsonify({"status": "error", "message": "Internal server error"}), 500

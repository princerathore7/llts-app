from flask import Blueprint, jsonify, request
from mongo import mongo
from bson import ObjectId
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_cors import cross_origin  # ✅ THIS IS REQUIRED
from models.token import add_tokens

admin_bp = Blueprint('admin_bp', __name__)

# =============================
# 🔒 Toggle or Set User Status
# =============================
@admin_bp.route('/user-status/<user_id>', methods=['PATCH', 'OPTIONS'])
def update_user_status(user_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    current_status = user.get("status", "active")
    new_status = "disabled" if current_status == "active" else "active"

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"status": new_status}}
    )

    return jsonify({
        "status": "success",
        "message": f"User status updated to {new_status}",
        "new_status": new_status
    }), 200

# =============================
# 🧾 Get All Users
# =============================
@admin_bp.route('/all-users', methods=['GET'])
def get_all_users():
    users = list(mongo.db.users.find())
    for u in users:
        u["_id"] = str(u["_id"])
    return jsonify({"status": "success", "users": users}), 200

# =============================
# 📄 Toggle or Set Tender Status
# =============================
@admin_bp.route('/tender-status/<tender_id>', methods=['PATCH', 'OPTIONS'])
def update_tender_status(tender_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    tender = mongo.db.tenders.find_one({"_id": ObjectId(tender_id)})
    if not tender:
        return jsonify({"status": "error", "message": "Tender not found"}), 404

    current_status = tender.get("status", "active")
    new_status = "disabled" if current_status == "active" else "active"

    mongo.db.tenders.update_one(
        {"_id": ObjectId(tender_id)},
        {"$set": {"status": new_status}}
    )

    return jsonify({
        "status": "success",
        "message": f"Tender status updated to {new_status}",
        "new_status": new_status
    }), 200

# =============================
# 📄 Get All Tenders
# =============================
@admin_bp.route('/all-tenders', methods=['GET'])
def get_all_tenders():
    tenders = list(mongo.db.tenders.find())
    for t in tenders:
        t["_id"] = str(t["_id"])
    return jsonify({"status": "success", "tenders": tenders}), 200

# =============================
# 🔨 Toggle or Set Auction Status
# =============================
@admin_bp.route('/auction-status/<auction_id>', methods=['PATCH', 'OPTIONS'])
def update_auction_status(auction_id):
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    auction = mongo.db.auctions.find_one({"_id": ObjectId(auction_id)})
    if not auction:
        return jsonify({"status": "error", "message": "Auction not found"}), 404

    current_status = auction.get("status", "active")
    new_status = "disabled" if current_status == "active" else "active"

    mongo.db.auctions.update_one(
        {"_id": ObjectId(auction_id)},
        {"$set": {"status": new_status}}
    )

    return jsonify({
        "status": "success",
        "message": f"Auction status updated to {new_status}",
        "new_status": new_status
    }), 200

# =============================
# 🔨 Get All Auctions
# =============================
@admin_bp.route('/all-auctions', methods=['GET'])
def get_all_auctions():
    auctions = list(mongo.db.auctions.find())
    for a in auctions:
        a["_id"] = str(a["_id"])
    return jsonify({"status": "success", "auctions": auctions}), 200

# =============================
# 🔨 DELETE TENDERS
# =============================
@admin_bp.route('/api/admin/delete-tender/<tender_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin(origins=ALLOWED_ORIGINS, supports_credentials=True)
def admin_delete_tender(tender_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

    try:
        verify_jwt_in_request()
        admin_id = get_jwt_identity()
        print("🧾 Admin:", admin_id)

        tender = mongo.db.tenders.find_one({"_id": ObjectId(tender_id)})
        if not tender:
            return jsonify({"status": "error", "message": "Tender not found"}), 404

        mongo.db.tenders.delete_one({"_id": ObjectId(tender_id)})
        mongo.db.applications.delete_many({"tender_id": ObjectId(tender_id)})

        return jsonify({"status": "success", "message": "Tender deleted successfully"}), 200

    except Exception as e:
        print("❌ Error deleting tender (admin):", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500


# =============================
# 🚀 ADMIN: Grant Tokens to Any User
# =============================
@admin_bp.route("/grant-tokens", methods=["POST", "OPTIONS"])
@jwt_required()
def admin_grant_tokens():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    claims = get_jwt()
    role = claims.get("role", "")

    if role not in ["admin", "owner"]:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    identifier = data.get("identifier")
    amount = data.get("amount")

    if not identifier or not amount:
        return jsonify({"error": "Missing username/email or amount"}), 400

    user = mongo.db.users.find_one({
        "$or": [{"username": identifier}, {"email": identifier}]
    })

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        user_id = ObjectId(user["_id"])
        add_tokens(user_id, int(amount))
        return jsonify({
            "message": f"{amount} tokens granted to user '{identifier}'"
        }), 200
    except Exception as e:
        return jsonify({"error": "Failed to grant tokens", "details": str(e)}), 500

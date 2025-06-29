from flask import Blueprint, request, jsonify
from bson import ObjectId
from mongo import mongo
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin

tender_bp = Blueprint('tender', __name__)

ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://llts-app.onrender.com"
]

# ---------------------------------------
# ✅ POST /api/tenders - Create a tender
# ---------------------------------------
@tender_bp.route("/tenders", methods=["POST", "OPTIONS"])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS)
def post_tender():
    try:
        data = request.json
        current_user = get_jwt_identity()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        required_fields = ['title', 'description', 'budget', 'location', 'deadline', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        # ✅ Fetch phone number from user profile
        user = mongo.db.users.find_one({"_id": ObjectId(current_user)})
        owner_phone = user.get("phone", "919999999999") if user else "919999999999"

        tender = {
    "title": data["title"],
    "description": data["description"],
    "budget": data["budget"],
    "location": data["location"],
    "deadline": data["deadline"],
    "category": data["category"],
    "created_by": ObjectId(current_user),  # ✅ fixed here
    "owner_phone": owner_phone,
    "date_posted": datetime.utcnow()
}


        result = mongo.db.tenders.insert_one(tender)

        return jsonify({
            "message": "Tender posted successfully",
            "tender_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print("❌ Error posting tender:", e)
        return jsonify({"error": "Internal Server Error"}), 500


# ------------------------------------------------------------------
# ✅ GET /api/get-tenders - Get all tenders and auctions
# ------------------------------------------------------------------
@tender_bp.route('/get-tenders', methods=['GET'])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS)
def get_all_tenders_and_auctions():
    try:
        tender_docs = list(mongo.db.tenders.find().sort("date_posted", -1))
        auction_docs = list(mongo.db.auctions.find().sort("date_posted", -1))

        tenders = []
        for tender in tender_docs:
            owner_name = "Unknown"
            owner_id = tender.get("created_by", "")
            parsed_owner_id = None
            user = None  # ✅ Always define user

            try:
                if isinstance(owner_id, dict) and "$oid" in owner_id:
                    parsed_owner_id = ObjectId(owner_id["$oid"])
                elif isinstance(owner_id, str):
                    parsed_owner_id = ObjectId(owner_id)
                elif isinstance(owner_id, ObjectId):
                    parsed_owner_id = owner_id

                if parsed_owner_id:
                    user = mongo.db.users.find_one({"_id": parsed_owner_id})
                    if user:
                        owner_name = user.get("name", "Unknown")
                        owner_id = str(user["_id"])
                    else:
                        owner_id = str(parsed_owner_id)
                else:
                    owner_id = "Unavailable"

            except Exception as e:
                print("⚠️ Error parsing owner ID:", e)
                owner_id = "Invalid"

            tenders.append({
    "_id": str(tender.get("_id")),
    "title": tender.get("title", "Untitled"),
    "description": tender.get("description", ""),
    "budget": tender.get("budget", 0),
    "location": tender.get("location", "Not specified"),
    "deadline": str(tender.get("deadline", "Not set")),
    "category": tender.get("category", "General"),
    "owner": owner_name,
    "owner_id": owner_id,
    "owner_phone": tender.get("owner_phone") or (user.get("phone") if user and user.get("phone") else "919999999999"),
    "type": "tender"
})

        auctions = []
        for auction in auction_docs:
            owner_name = "Unknown"
            owner_id = auction.get("created_by", "")
            parsed_owner_id = None

            try:
                if isinstance(owner_id, dict) and "$oid" in owner_id:
                    parsed_owner_id = ObjectId(owner_id["$oid"])
                elif isinstance(owner_id, str):
                    parsed_owner_id = ObjectId(owner_id)
                elif isinstance(owner_id, ObjectId):
                    parsed_owner_id = owner_id

                if parsed_owner_id:
                    user = mongo.db.users.find_one({"_id": parsed_owner_id})
                    if user:
                        owner_name = user.get("name", "Unknown")

            except Exception as e:
                print("⚠️ Error parsing auction owner ID:", e)

            auctions.append({
                "_id": str(auction.get("_id")),
                "item_name": auction.get("item_name", "Untitled"),
                "description": auction.get("description", ""),
                "starting_bid": auction.get("starting_bid", 0),
                "location": auction.get("location", "Not specified"),
                "end_date": str(auction.get("end_date", "Not set")),
                "owner": owner_name,
                "type": "auction"
            })

        return jsonify({
            "tenders": tenders,
            "auctions": auctions
        }), 200

    except Exception as e:
        print("❌ Error fetching tenders/auctions:", e)
        return jsonify({"error": "Internal Server Error"}), 500


# --------------------------------------------------------
# ✅ DELETE /api/delete-tender/<tender_id> - Delete tender
# --------------------------------------------------------
@tender_bp.route("/delete-tender/<tender_id>", methods=["DELETE"])
@jwt_required()
@cross_origin(origins=ALLOWED_ORIGINS)
def delete_tender(tender_id):
    try:
        current_user = get_jwt_identity()
        result = mongo.db.tenders.delete_one({
            "_id": ObjectId(tender_id),
            "created_by": str(current_user)
        })

        if result.deleted_count == 1:
            return jsonify({"message": "Tender deleted"}), 200
        else:
            return jsonify({"error": "Tender not found or not authorized"}), 404

    except Exception as e:
        print("❌ Error deleting tender:", e)
        return jsonify({"error": "Internal Server Error"}), 500

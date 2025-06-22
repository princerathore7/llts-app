from flask import Blueprint, request, jsonify
from mongo import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from flask_cors import cross_origin

auction_bp = Blueprint('auction_bp', __name__)

# ✅ POST Auction (POST /api/post-auction)
@auction_bp.route('/post-auction', methods=['POST', 'OPTIONS'])
@cross_origin(origins=["http://127.0.0.1:5500", "http://localhost:5500"])  # ✅ Match your frontend
@jwt_required()
def post_auction():
    try:
        data = request.json
        print("📥 Auction Received:", data)

        current_user = get_jwt_identity()  # from JWT
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 401

        required_fields = [
            'item_name', 'title', 'description',
            'starting_bid', 'base_price', 'location',
            'condition', 'end_date'
        ]

        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        auction = {
            "item_name": data["item_name"],
            "title": data["title"],
            "description": data["description"],
            "starting_bid": float(data["starting_bid"]),
            "base_price": float(data["base_price"]),
            "location": data["location"],
            "condition": data["condition"],
            "end_date": data["end_date"],  # Expecting ISO date string from frontend
            "created_by": ObjectId(current_user),
            "date_posted": datetime.utcnow()
        }

        result = mongo.db.auctions.insert_one(auction)
        print("✅ Auction Inserted:", auction)

        return jsonify({
            "message": "Auction posted successfully!",
            "auction_id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print("❌ Error posting auction:", e)
        return jsonify({"error": "Internal Server Error"}), 500

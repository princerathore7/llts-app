# backend/routes/token.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models.token import get_token_record, add_tokens
from bson import ObjectId
from mongo import mongo

token_bp = Blueprint("token", __name__)

# =============================
# 🔹 Get Total Token Balance
# =============================
@token_bp.route("/get-tokens", methods=["GET"])
@jwt_required()
def get_tokens():
    user_id = get_jwt_identity()
    record = get_token_record(user_id)
    if record:
        return jsonify({"status": "success", "tokens": record["tokens"]})
    return jsonify({"status": "fail", "message": "Token record not found"}), 404

# =============================
# 💳 Buy Tokens
# =============================
@token_bp.route("/buy-tokens", methods=["POST"])
@jwt_required()
def buy_tokens():
    user_id = get_jwt_identity()
    amount = request.json.get("amount", 0)
    if amount > 0:
        add_tokens(user_id, amount)
        return jsonify({"status": "success", "message": f"{amount} tokens added."})
    return jsonify({"status": "fail", "message": "Invalid amount"}), 400

# =============================
# 🧾 User Token Info (History)
# =============================
@token_bp.route("/user/token-info", methods=["GET"])
@jwt_required()
def get_token_info():
    user_id = get_jwt_identity()
    token_data = mongo.db.tokens.find_one({"user_id": str(user_id)})  # ✅ fix here

    if not token_data:
        return jsonify({"tokens": 0, "history": []}), 200

    token_data["_id"] = str(token_data["_id"])
    return jsonify(token_data), 200

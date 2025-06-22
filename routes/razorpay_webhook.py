from flask import Blueprint, request, jsonify
import hmac, hashlib
import os
from mongo import mongo
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

razorpay_bp = Blueprint('razorpay_webhook', __name__)

# ✅ Razorpay secret from .env
RAZORPAY_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

@razorpay_bp.route("/api/razorpay-webhook", methods=["POST"])
def handle_razorpay_webhook():
    try:
        # Razorpay sends raw body + signature
        payload = request.get_data()
        signature = request.headers.get('X-Razorpay-Signature')

        # ✅ Verify signature using secret key
        generated_signature = hmac.new(
            bytes(RAZORPAY_SECRET, 'utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(generated_signature, signature):
            data = request.get_json()

            # ✅ Extract useful info (update according to actual event)
            if data.get("event") == "payment.captured":
                email = data['payload']['payment']['entity']['email']
                amount = int(data['payload']['payment']['entity']['amount']) / 100

                # 🔍 Match user by email (or add mapping logic)
                user = mongo.db.users.find_one({"email": email})
                if user:
                    user_id = str(user["_id"])

                    # ✅ Determine tokens based on amount
                    token_map = {
                        10: 5,
                        20: 11,
                        30: 22,
                        50: 40,
                        75: 65,
                        100: 90
                    }
                    tokens_to_add = token_map.get(int(amount), 0)

                    if tokens_to_add:
                        mongo.db.tokens.update_one(
                            {"user_id": ObjectId(user_id)},
                            {"$inc": {"tokens": tokens_to_add}},
                            upsert=True
                        )
                        print(f"✅ {tokens_to_add} tokens added for {email}")
                return jsonify({"status": "Webhook processed"}), 200
            else:
                return jsonify({"msg": "Unhandled event type"}), 200
        else:
            return jsonify({"error": "Invalid signature"}), 403

    except Exception as e:
        print("❌ Webhook Error:", e)
        return jsonify({"error": "Webhook processing failed"}), 500

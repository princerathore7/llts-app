from flask import Blueprint, request, jsonify
import hmac, hashlib
import os
from mongo import mongo
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

razorpay_bp = Blueprint('razorpay_webhook', __name__)

# ✅ Razorpay secret from .env
RAZORPAY_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")


@razorpay_bp.route("/api/razorpay-webhook", methods=["POST"])
def handle_razorpay_webhook():
    try:
        payload = request.get_data()
        signature = request.headers.get('X-Razorpay-Signature')

        # ✅ Verify signature using HMAC SHA256
        generated_signature = hmac.new(
            bytes(RAZORPAY_SECRET, 'utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, signature):
            print("❌ Invalid signature received.")
            return jsonify({"error": "Invalid signature"}), 403

        data = request.get_json()
        print("🔔 Razorpay webhook payload:", data)

        # ✅ Handle only payment.captured event
        if data.get("event") == "payment.captured":
            payment = data['payload']['payment']['entity']
            email = payment.get('email')
            amount_paise = payment.get('amount', 0)
            amount_rupees = amount_paise // 100

            if not email:
                print("❌ Missing email in payment payload.")
                return jsonify({"status": "ignored - no email"}), 200

            # ✅ Find user by email
            user = mongo.db.users.find_one({"email": email})
            if not user:
                print(f"❌ No user found for email: {email}")
                return jsonify({"status": "ignored - user not found"}), 200

            user_id = str(user["_id"])

            # ✅ Token mapping based on recharge amount
            token_map = {
                10: 5,
                20: 11,
                30: 22,
                50: 40,
                75: 65,
                100: 90
            }
            tokens_to_add = token_map.get(amount_rupees, 0)

            if tokens_to_add:
                # ✅ Update tokens
                mongo.db.tokens.update_one(
                    {"user_id": user_id},
                    {"$inc": {"tokens": tokens_to_add, "totalPurchased": tokens_to_add}},
                    upsert=True
                )
                print(f"✅ {tokens_to_add} tokens credited to {email}")

                # ✅ Insert into transaction log
                mongo.db.token_transactions.insert_one({
                    "user_id": user_id,
                    "email": email,
                    "tokens_added": tokens_to_add,
                    "amount_rupees": amount_rupees,
                    "source": "razorpay",
                    "timestamp": datetime.utcnow(),
                    "payment_id": payment.get("id")
                })

            else:
                print(f"⚠️ No matching token pack for ₹{amount_rupees}")

            return jsonify({"status": "Webhook processed"}), 200

        return jsonify({"status": "ignored - event not handled"}), 200

    except Exception as e:
        print("❌ Webhook error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

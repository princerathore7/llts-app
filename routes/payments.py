@payment_bp.route('/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    import hmac
    import hashlib
    from flask import request

    RAZORPAY_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    payload = request.data
    received_sig = request.headers.get('X-Razorpay-Signature')

    expected_sig = hmac.new(
        RAZORPAY_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(received_sig, expected_sig):
        print("❌ Invalid Razorpay signature")
        return jsonify({"status": "invalid signature"}), 400

    data = request.get_json()
    print("🔔 Razorpay Webhook received:", data)

    if data.get('event') == "payment.captured":
        payment_entity = data['payload']['payment']['entity']
        amount = payment_entity['amount'] / 100
        email = payment_entity.get('email')

        if not email:
            print("❌ Email missing from payment entity.")
            return jsonify({"status": "ignored - no email"}), 200

        user = mongo.db.users.find_one({"email": email})
        if not user:
            print(f"❌ No user found for email: {email}")
            return jsonify({"status": "ignored - user not found"}), 200

        token_map = {10: 5, 20: 11, 30: 22, 50: 40, 75: 65, 100: 90}
        tokens_to_add = token_map.get(int(amount), 0)

        if tokens_to_add == 0:
            print(f"⚠️ No token mapping found for ₹{amount}")
            return jsonify({"status": "ignored - no token mapping"}), 200

        mongo.db.tokens.update_one(
            {"user_id": str(user["_id"])},
            {"$inc": {"tokens": tokens_to_add, "totalPurchased": tokens_to_add}},
            upsert=True
        )

        print(f"✅ {tokens_to_add} tokens credited to {email}")
        return jsonify({"message": "Tokens added"}), 200

    return jsonify({"status": "ignored - not payment.captured"}), 200

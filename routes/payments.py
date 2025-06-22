@payment_bp.route('/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    import hmac
    import hashlib
    from flask import request

    RAZORPAY_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    # ✅ 1. Verify Signature
    payload = request.data
    received_sig = request.headers.get('X-Razorpay-Signature')

    expected_sig = hmac.new(
        RAZORPAY_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(received_sig, expected_sig):
        data = request.get_json()
        if data['event'] == "payment.captured":
            amount = data['payload']['payment']['entity']['amount'] / 100
            email = data['payload']['payment']['entity']['email']

            user = mongo.db.users.find_one({"email": email})
            if not user:
                return jsonify({"error": "User not found"}), 404

            token_map = {10: 5, 20: 11, 30: 22, 50: 40, 75: 65, 100: 90}
            tokens_to_add = token_map.get(int(amount), 0)

            mongo.db.tokens.update_one(
                {"user_id": str(user["_id"])},
                {"$inc": {"tokens": tokens_to_add, "totalPurchased": tokens_to_add}},
                upsert=True
            )

            return jsonify({"message": "Tokens added"}), 200

    return jsonify({"status": "invalid signature"}), 400

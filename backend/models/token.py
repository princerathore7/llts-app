from bson import ObjectId
from datetime import datetime
from backend.mongo import mongo

# =============================
# 🔍 Get Token Record for User
# =============================
def get_token_record(user_id, role=None):
    query = {"user_id": str(user_id)}  # ✅ stored as string in DB
    if role:
        query["role"] = role
    return mongo.db.tokens.find_one(query)

# =============================
# 🎁 Initialize Token Record on Signup
# =============================
def init_token_record(user_id, role):
    tokens = 150  # 🎁 Give 150 tokens to everyone on signup
    mongo.db.tokens.insert_one({
        "user_id": str(user_id),
        "role": role,
        "tokens": tokens,
        "issued_at": datetime.utcnow(),
        "history": [{
            "type": "signup-bonus",
            "amount": tokens,
            "time": datetime.utcnow()
        }]
    })

# =============================
# ➖ Decrement Token (on usage)
# =============================
def decrement_token(user_id, role=None):
    query = {"user_id": str(user_id)}
    if role:
        query["role"] = role
    mongo.db.tokens.update_one(query, {
        "$inc": {"tokens": -1},
        "$push": {"history": {
            "type": "used",
            "amount": -1,
            "time": datetime.utcnow()
        }}
    })

# =============================
# ➕ Add Tokens (admin or buy)
# =============================
def add_tokens(user_id, amount):
    existing = mongo.db.tokens.find_one({"user_id": str(user_id)})
    if existing:
        mongo.db.tokens.update_one(
            {"user_id": str(user_id)},
            {
                "$inc": {"tokens": amount},
                "$push": {"history": {
                    "type": "grant",
                    "amount": amount,
                    "time": datetime.utcnow()
                }}
            }
        )
    else:
        mongo.db.tokens.insert_one({
            "user_id": str(user_id),
            "tokens": amount,
            "issued_at": datetime.utcnow(),
            "history": [{
                "type": "grant",
                "amount": amount,
                "time": datetime.utcnow()
            }]
        })

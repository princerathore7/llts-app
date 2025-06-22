from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# ⚠️ MongoDB connection (update db name if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client['llts']  # <== change this to your actual DB name
users = db.users

# 🔁 Update all worker passwords (if not already hashed)
updated_count = 0
for user in users.find({"role": "worker"}):
    password = user.get('password', '')
    
    # Check if password is already hashed (starts with 'pbkdf2')
    if not password.startswith('pbkdf2:sha256:'):
        hashed_password = generate_password_hash(password)
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed_password}}
        )
        print(f"✅ Updated password for {user.get('username')}")
        updated_count += 1
    else:
        print(f"⏩ Skipped (already hashed): {user.get('username')}")

print(f"\n✨ Done! {updated_count} passwords updated.")
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# ⚠️ MongoDB connection (update db name if needed)
client = MongoClient("mongodb://localhost:27017/")
db = client['llts']  # <== change this to your actual DB name
users = db.users

# 🔁 Update all worker passwords (if not already hashed)
updated_count = 0
for user in users.find({"role": "worker"}):
    password = user.get('password', '')
    
    # Check if password is already hashed (starts with 'pbkdf2')
    if not password.startswith('pbkdf2:sha256:'):
        hashed_password = generate_password_hash(password)
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed_password}}
        )
        print(f"✅ Updated password for {user.get('username')}")
        updated_count += 1
    else:
        print(f"⏩ Skipped (already hashed): {user.get('username')}")

print(f"\n✨ Done! {updated_count} passwords updated.")

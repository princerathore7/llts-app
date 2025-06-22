from backend.mongo import mongo
from datetime import datetime
from bson import ObjectId

# ✅ Get all tenders (optional, not always needed)
def get_all_tenders():
    tenders = list(mongo.db.tenders.find())
    for t in tenders:
        t["_id"] = str(t["_id"])
    return tenders

# ✅ Get tender by ID
def get_tender_by_id(tender_id):
    try:
        tender = mongo.db.tenders.find_one({"_id": ObjectId(tender_id)})
        if tender:
            tender["_id"] = str(tender["_id"])
        return tender
    except:
        return None

# ✅ Create a new tender
def create_tender(data, owner_id):
    new_tender = {
        "title": data.get("title"),
        "description": data.get("description"),
        "budget": data.get("budget"),
        "deadline": data.get("deadline"),  # Already in string or ISO format
        "created_by": str(owner_id),
        "status": "active",
        "created_at": datetime.utcnow()
    }

    result = mongo.db.tenders.insert_one(new_tender)
    new_tender["_id"] = str(result.inserted_id)
    return new_tender

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.mongo import mongo
from bson import ObjectId
from datetime import datetime

report_bp = Blueprint('report_bp', __name__)

# =============================
# 📤 Submit a Report
# =============================
@report_bp.route('/report', methods=['POST'])
@jwt_required()
def submit_report():
    data = request.get_json()
    user_id = get_jwt_identity()

    if not data.get("type") or not data.get("target_id") or not data.get("reason"):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    report = {
        "reported_by": ObjectId(user_id),
        "report_type": data.get("type"),  # "tender", "auction", or "user"
        "target_id": ObjectId(data.get("target_id")),
        "reason": data.get("reason"),
        "status": "pending",
        "timestamp": datetime.utcnow()
    }

    mongo.db.reports.insert_one(report)
    return jsonify({"status": "success", "message": "Report submitted"}), 201


# =============================
# 📥 Get All Reports (Admin Only)
# =============================
@report_bp.route('/admin/reports', methods=['GET'])
def get_reports():
    reports = list(mongo.db.reports.find().sort("timestamp", -1))
    for r in reports:
        r["_id"] = str(r["_id"])
        r["reported_by"] = str(r["reported_by"])
        r["target_id"] = str(r["target_id"])
        r["timestamp"] = r["timestamp"].isoformat()
    return jsonify({"reports": reports})

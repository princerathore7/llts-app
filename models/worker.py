# backend/models/worker.py
from . import db

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20), unique=True)
    total_earnings = db.Column(db.Float, default=0)
    # aur bhi fields as needed

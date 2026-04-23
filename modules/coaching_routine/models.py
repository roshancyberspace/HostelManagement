from datetime import datetime
from models.db import db

class CoachingRoutine(db.Model):
    __tablename__ = 'coaching_routine'

    id = db.Column(db.Integer, primary_key=True)
    routine_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    coach_name = db.Column(db.String(100))
    days = db.Column(db.String(50))  # Mon,Tue,Wed
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    location = db.Column(db.String(100))
    target_group = db.Column(db.String(50))
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CoachingRoutineStudent(db.Model):
    __tablename__ = 'coaching_routine_students'

    id = db.Column(db.Integer, primary_key=True)
    ledger_no = db.Column(db.String(20), nullable=False)
    routine_id = db.Column(db.Integer, nullable=False)
    assigned_on = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='ACTIVE')

from .models import CoachingRoutine
from database import db

def create_routine(data):
    routine = CoachingRoutine(**data)
    db.session.add(routine)
    db.session.commit()
    return routine

def get_all_routines():
    return CoachingRoutine.query.order_by(CoachingRoutine.created_at.desc()).all()

def get_routine(routine_id):
    return CoachingRoutine.query.get(routine_id)

def update_status(routine, status):
    routine.status = status
    db.session.commit()

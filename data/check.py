import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

def in_person_first_time(email):
    # returns true if email not in db
    email_exist = db.session.query(db.exists().where(User.email == email)).scalar()
    return (not email_exist)

def in_person(phone, email):
    # Returns true if user paid in person
    phone_exist = db.session.query(db.exists().where(User.phone == phone)).scalar()
    print(phone_exist)
    email_exist = db.session.query(db.exists().where(User.email == email)).scalar()
    print(email_exist)

    return (phone_exist and not email_exist)

def link(phone, email):
    user = User.query.filter(User.phone == phone)
    user.email = email
    db.session.commit()

    tracker_info = []
    trackers = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.email == email)
    for row in tracker_info:
        tracker = dict(row.__dict__)
        tracker.pop('_sa_instance_state')
        tracker_info.append(tracker)

    return tracker_info

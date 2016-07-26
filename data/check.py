import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

def in_person_first_time(email, media):
    # returns true if email not in db
    if media == 'fb':
        return not db.session.query(db.exists().where(User.fb_email == email)).scalar()
    elif media == 'google':
        return not db.session.query(db.exists().where(User.google_email == email)).scalar()

def in_person(phone, email, media):
    # Returns true if user paid in person
    phone_exist = db.session.query(db.exists().where(User.phone == phone)).scalar()
    print(phone_exist)
    if media == 'fb':
        user.fb_email = email
    elif media == 'google':
        user.google_email = email
    email_exist = db.session.query(db.exists().where(User.email == email)).scalar()
    print(email_exist)

    return (phone_exist and not email_exist)

def link(phone, user_id, email, media):
    print('link function:')
    user = User.query.filter(User.phone == phone).first()
    print(user)
    # Add their email to the respective login type
    if media == 'fb':
        user.fb_email = email
    elif media == 'google':
        user.google_email = email
    print(user)
    db.session.commit()

    tracker_info = []
    tracker_info = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.user_id == user.user_id)
    print(tracker_info)
    for row in tracker_info:
        tracker = dict(row.__dict__)
        print(tracker)
        tracker.pop('_sa_instance_state')
        tracker_info.append(tracker)

    return tracker_info

def get_user_id(email, media):
    if media == 'fb':
        return User.query.filter(User.fb_email == email).first().user_id
    elif media == 'google':
        return User.query.filter(User.google_email == email).first().user_id

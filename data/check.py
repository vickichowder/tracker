import os, logging

from math import floor

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

def link(phone, email, media, name):
    try:
        print('link function:')
        user = User.query.filter(User.phone == phone).first()
        # Add their email to the respective login type
        if media == 'fb':
            user.fb_email = email
        elif media == 'google':
            user.google_email = email
        print(user)

        if user.name is None:
            user.name = name
        # Commit changes
        db.session.commit()

        return True
    except Exception as e:
        # Return false on failure
        print(e)
        return False

def get_user_id(email, media):
    # Get user id based on the type of email used to sign in
    if media == 'fb':
        return User.query.filter(User.fb_email == email).first().user_id
    elif media == 'google':
        return User.query.filter(User.google_email == email).first().user_id

def get_new_tracker(user_id):
    # Get all tracker ids that haven't been initialized yet
    trackers = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.added == 0).filter(Tracker.user_id == user_id)

    return listify_column(trackers)

def get_trackers(user_id):
    # Get all trackers for this user id
    trackers = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.user_id == User.user_id)

    return listify_column(trackers)

def listify_column(result):
    # Turn the results of a sqlalchemy cursor of one column into list
    result_list = []

    for row in result:
        result_list.append(row[0])

    return result_list

def get_credits(user_id):
    # Remaining credits
    # = balance (in cents) - 180 (6 buffer texts) / 30
    return floor((User.query.with_entities(User.balance).filter(User.user_id==user_id).first()[0] - 180) / 30)

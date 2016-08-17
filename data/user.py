import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User


def init(info, tracker_id):
    print('init function for', info['name'])
    # Add tracker information from the initialization form to db
    try:
        # Create a new user
        # Default balance = 100
        user = User(info['phone'], info['email'], info['name'], 100, 'User')
        db.session.add(user)
        print(user)

        if len(info['imei']) == 10:
            # Add a new tracker for the new user if imei exists
            # 'added' column = 0 --> user needs to login and review tracker info before it's finalized
            # Default type = 'Vehicle'
            print('Add tracker for this user,', info['user'], 'imei:', info['imei'])
            tracker = Tracker(info['imei'], info['user_id'], 0, info['tracker_name'], 'Vehicle', info['make'], info['model'], info['year'], info['color'])
            db.session.add(tracker)
            print('added tracker', info['tracker_name'])

        db.session.commit()
        # True on success
        return True
    except Exception as e:
        print(e)
        return False

def in_person_first_time(email, media):
    # returns true if email not in db
    if media == 'fb':
        return not db.session.query(db.exists().where(User.fb_email == email)).scalar()
    # Support for google login in the future
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

def get_role(user_id):
    # Return true if user is admin
    return (User.query.with_entities(User.role).filter(User.user_id==user_id).first()[0]) == 'Admin'

def get_credits(user_id):
    # Remaining credits
    return User.query.with_entities(User.balance).filter(User.user_id==user_id).first()[0]

def use_credit(user_id):
    # Use up a credit
    try:
        user = User.query.filter(User.user_id==user_id)
        user.balance -= 1
        db.session.commit()
    except Exception as e:
        print(e)
        pass

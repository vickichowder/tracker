import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta

from connect.phone import Twilio
from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

twilio_client = Twilio().client

def get_info(tracker_list):
    # Get tracker's info, given the list of tracker ids
    trackers = Tracker.query.filter(Tracker.tracker_id.in_(tracker_list)).all()

    info = []
    for row in trackers:
        tracker = {}
        tracker['tracker_id'] = row.tracker_id
        tracker['tracker_name'] = row.tracker_name
        tracker['imei'] = row.imei
        tracker['make'] = row.make
        tracker['model'] = row.model
        tracker['year'] = row.year
        tracker['color'] = row.color
        info.append(tracker)

    return info

def init(info, tracker_id):
    print('init function for', tracker_id)
    # Add tracker information from the initialization form to db
    try:
        # Get the tracker by tracker id
        tracker = Tracker.query.filter(Tracker.tracker_id == tracker_id).first()
        # Update the tracker info with the input from form
        tracker.tracker_name = info['tracker_name']
        tracker.year = info['year']
        tracker.model = info['model']
        tracker.make = info['make']
        tracker.color = info['color']

        # Commit / save
        db.session.commit()

        # Set the tracker to be 'added' / initialized after the commit above is successful
        tracker.added = 1
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False

def get_trackers(user_id):
    # Query the trackers that belong to this user_id
    tracker_list = Tracker.query.with_entities(Tracker.tracker_id, Tracker.tracker_name).filter(Tracker.user_id==user_id)
    trackers = {}

    for row in tracker_list:
        trackers[row.tracker_name] = row.tracker_id

    return trackers

def get_locations(tracker_id):
    sync(tracker_id)
    # Get time delta for 24 hours within last coord
    latest = Position.query.with_entities(Position.time).filter(Position.tracker_id==tracker_id).order_by(Position.time.desc()).first()[0]
    print(latest)
    delta = latest - timedelta(hours=24)
    print(delta)
    locations = []
    # Query the locations for each tracker
    for ping in Position.query.filter(Position.tracker_id==tracker_id).filter(Position.time > delta).order_by(Position.time.desc()):
        print(ping)
        locations.append({
            'time' : ping.time,
            'latitude' : ping.latitude,
            'longitude' : ping.longitude})
    return locations

def get_tracker_id(user_id, tracker_name):
    return Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.user_id==user_id).filter(Tracker.tracker_name==tracker_name).first()[0]

def sync(tracker_id):
    # Get latest postiion's date
    latest = Position.query.with_entities(Position.time).order_by(Position.time.desc()).first()[0]
    sms_list = []

    if latest is None:
        # Get all positions
        sms_list += twilio_client.sms.messages.list(from_=tracker_id)
    else:
        # Get the time from last ping to current day
        delta = datetime.now() - latest
        for day in range(delta.days + 1):
            sms_list += twilio_client.sms.messages.list(from_=tracker_id, date_sent=day)

    for sms in sms_list:
        timestamp = None
        latitude = None
        longitude = None

        if ('maps' in sms.body):
            # Parse through sms body only if it returns with google maps link (has 'maps' in it)
            details = sms.body.split(' ')
            for (index, val) in enumerate(details):
                # Parse through the message body, build a return string

                if ('lat:' in val) and (len(val) > 5):
                    # Get latitude
                    latitude = val[6:]
                elif ('long:' in val) and (len(val) > 5):
                    # Get longitude
                    longitude = val[5:]

                timestamp = sms.date_sent

            if timestamp and latitude and longitude:
                # It's all there, so add it to our db
                new_record = Position(tracker_id, timestamp, latitude, longitude)
                try:
                    db.session.add(new_record)
                    db.session.commit()
                except:
                    db.session.rollback()
                    continue
    print('Sync\'d:', tracker_id)

def get_new_tracker(user_id):
    # Get all tracker ids that haven't been initialized yet
    trackers = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.added == 0).filter(Tracker.user_id == user_id)

    return listify_column(trackers)

def get_trackers(user_id):
    # Get all trackers for this user id
    trackers = Tracker.query.with_entities(Tracker.tracker_id).filter(Tracker.user_id == User.user_id)

    return listify_column(trackers)

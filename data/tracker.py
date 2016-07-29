import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

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

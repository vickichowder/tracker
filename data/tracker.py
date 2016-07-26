import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

def tracker_info(tracker_list):
    trackers = Tracker.query.with_entities(\
        Tracker.tracker_id, Tracker.tracker_name, Tracker.imei, Tracker.type_,\
        Tracker.make, Tracker.model, Tracker.year, Tracker.color)\
        .filter(Tracker.tracker_id.in_(tracker_list)).all()

    info = []
    for row in trackers:
        info.append(row._asdict)

    return info

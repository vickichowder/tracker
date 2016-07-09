import os, logging

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from data.db import db
from data.position import Position
from data.tracker import Tracker
from data.user import User

class Pings:
    def __init__(self, twilio_client, email):
        # data = dict[tracker_id]: [{time, name, link}]
        self.location = {}
        # list of the trackers for this email
        self.trackers = {}
        self.email = email

        self.get_trackers(db)
        self.refresh(twilio_client, db)
        self.get_locations(db)

    def get_trackers(self, db):
        # Query the trackers that belong to this email
        trackers = Tracker.query.with_entities(Tracker.tracker_id, Tracker.tracker_name).join(User, User.user_id==Tracker.user_id).filter(User.email==self.email)
        for row in trackers:
            self.trackers[row.tracker_id] = row.tracker_name

    def get_locations(self, db):
        # Query the locations for each tracker
        for tracker_id in self.trackers:
            self.location[tracker_id] = []
            for ping in Position.query.filter_by(tracker_id=tracker_id).order_by(desc(Position.time)):
                self.location[tracker_id].append({
                    'time' : ping.time,
                    'link' : "https://www.google.com/maps?f=q&q={},{}&z=16".format(ping.latitude, ping.longitude)})

    def refresh(self, twilio_cient, db, tracker_id):
        # Assuming that we ping on demand... get pings for today only
        # We'll need to change this logic if pings happen at intervals
        today = twilio_client.sms.messages.list(from_=phone, date_sent=datetime.datetime.now().strftime("%Y-%m-%d"))
        existing = Position.query(sms_id).filter_by(tracker_id).all()

        for sms in today:
            timestamp = None
            latitude = None
            longitude = None

            if ('maps' in sms.body) and ('T:' in sms.body) and sms.sid not in existing:
                # Parse through body only if it returns with google maps link
                details = sms.body.split(' ')
                for (index, val) in enumerate(details):
                    # Parse through the message body, build a return string

                    if ('lat:' in val) and (len(val) > 5):
                        # Get latitude
                        latitude = val[6:]
                    elif ('long:' in val) and (len(val) > 5):
                        # Get longitude
                        longitude = val[5:]
                    elif ('T:' in val):
                        # Get the date and time
                        timestamp = "{} {}".format(val[4:], details[index + 1])

                if timestamp and latitude and longitude:
                    # It's all there, so add it to our db
                    new_record = Position(tracker_id, datetime.strptime(timestamp, "%m/%d/%y %H:%m"), latitude, longitude)
                    db.session.add(new_record)
                    db.session.commit()

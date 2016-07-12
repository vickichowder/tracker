from model.db import db

class Position(db.Model):
    # Mirrors the position table in db
    tracker_id = db.Column(db.String(12), primary_key=True)
    time = db.Column(db.DateTime, primary_key=True)
    latitude = db.Column(db.Float(precision=5, asdecimal=True), primary_key=True)
    longitude = db.Column(db.Float(precision=5, asdecimal=True), primary_key=True)

    def __init__(self, tracker_id, time, latitude, longitude):
        self.tracker_id = tracker_id
        self.time = time
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return '<Position %r on %r @ lat:%r long:%r>' % self.tracker_id, self.time, self.latitude, self.longitude

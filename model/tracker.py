from model.db import db

class Tracker(db.Model):
    # Mirrors the tracker table in db
    tracker_id = db.Column(db.String(12), unique=True, primary_key=True)
    imei = db.Column(db.String(15), unique=True)
    user_id = db.Column(db.Integer)
    added = db.Column(db.Integer)
    tracker_name = db.Column(db.String(120))
    type_ = db.Column(db.String(100))
    make = db.Column(db.String(120))
    model = db.Column(db.String(150))
    year = db.Column(db.Integer)
    color = db.Column(db.String(50))

    def __init__(self, tracker_id, imei, user_id, added, tracker_name, type_, make, model, year, color):
        self.tracker_id = tracker_id
        self.imei = imei
        self.user_id = user_id
        self.added = added
        self.tracker_name = tracker_name
        self.type_ = type_
        self.make = make
        self.model = model
        self.year = year
        self.color = color

    def __repr__(self):
        return '<Tracker %r>' % self.tracker_id

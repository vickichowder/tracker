from flask_sqlalchemy import SQLAlchemy

class Tracker(db):
    tracker_id = db.Column(db.String(12), unique=True, primary_key=True)
    user_id = db.Column(db.String(80), unique=True)
    tracker_name = db.Column(db.String(120))

    def __init__(self, tracker_id, user_id, tracker_name):
        self.tracker_id = tracker_id
        self.user_id = user_id
        self.tracker_name = tracker_name

    def __repr__(self):
        return '<Tracker %r>' % self.tracker_id

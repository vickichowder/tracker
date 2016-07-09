from data.db import db

class User(db.Model):
    user_id = db.Column(db.String(80), unique=True, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    balance = db.Column(db.Integer, unique=True)

    def __init__(self, user_id, email, balance, name):
        self.user_id = user_id
        self.email = email
        self.balance = balance
        self.name = name

    def __repr__(self):
        return '<User %r>' % self.name

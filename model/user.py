from model.db import db

class User(db.Model):
    # Mirrors the user table in db
    user_id = db.Column(db.Integer, unique=True, primary_key=True) # auto_increment integer
    phone = db.Column(db.String(10), unique=True)
    fb_email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(120), unique=True)
    balance = db.Column(db.Integer, unique=True)
    role = db.Column(db.String(50))

    def __init__(self, phone, email, name, balance, role):
        self.phone = phone
        self.email = email
        self.name = name
        self.balance = balance
        self.role = role

    def __repr__(self):
        return '<User {}>'.format(self.name)

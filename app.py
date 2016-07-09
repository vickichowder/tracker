import os
import json
import logging

from datetime import date
from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
from runenv import load_env
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

from data.base import Base
from connect.phone import Twilio
from connect.database import DB
from data.pings import Pings

# Ideally this will not be here. We will eventually containerize this
# So the environment variables are global in the app
load_env(env_file='.env')
# load other stuffs
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TRACKER_APP_ID = os.getenv('TRACKER_APP_ID')
TRACKER_1 = os.getenv('TRACKER_1')

twilio_client = Twilio().client
session_db = DB()
db_client = session_db.client

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = session_db.uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = os.getenv('APP_SECRET_KEY')
db = SQLAlchemy(app)

@app.before_first_request
def setup():
    # Recreate database each time for demo
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)

@app.route('/', methods=['POST', 'GET'])
def landing():
    return render_template("landing.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/login')
def login():
    try:
        email = request.form['email']
        if email:
            session['user'] = True
            print('Started a session\n')
    except Exception as e:
        print(e)
    return render_template("landing.html")


@app.route('/ping', methods=['POST', 'GET'])
def ping_it():
    # Make a call to the tracker
    call = twilio_client.calls.create(
        to=TRACKER_1,
        from_=TWILIO_NUMBER,
        url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient")

    # Call details
    stringy = """
        <h1>Call successful</h1>
        Call id: {}<br>
        Called: {}<br>
        Status: {}<br><br>
        <form action="/status/{}">
            <input type="submit" value="Refresh Call Status">
        </form>
        <form action="/sms">
            <input type="submit" value="Check sms">
        </form>
    """.format(call.sid, call.to, call.status, call.sid)
    return(stringy)

@app.route('/status/<string:call_sid>', methods=['POST', 'GET'])
def status_refresh(call_sid):
    # Get call info
    call = twilio_client.calls.get(call_sid)

    # Call details
    stringy = """
        <h1>Call successful</h1>
        Call id: {}<br>
        Called: {}<br>
        Status: {}<br><br>
        <form action="/status/{}">
            <input type="submit" value="Refresh Call Status">
        </form>
    """.format(call.sid, call.to, call.status, call.sid)
    return(stringy)

@app.route('/pings', methods=['POST', 'GET'])
def load_pings():
    email = request.args.get('email', '', type=str)
    print('email', email)
    pings = Pings(twilio_client, db, 'vickalie@hotmail.com')

    return render_template("trackers.html", pings=pings.trackers)

@app.errorhandler(500)
def server_error(e):
    # Goddamn errors
    logging.exception('An error occurred during a request.')
    return """
        An internal error occurred: <pre>{}</pre>
        See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # localhost:8000
    app.run(port=8000, debug=True)

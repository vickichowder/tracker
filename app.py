import os
import json
# For debugging
import logging, traceback

from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from runenv import load_env
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

# Include our own models
from data.check import in_person, link, in_person_first_time, get_new_tracker, get_trackers, get_user_id
from data.tracker import tracker_info
from model.db import db
from data.pings import Pings
from connect.database import uri
from connect.phone import Twilio

# Create and fill out .env file from .env_sample
load_env(env_file='.env')
# Ideally this will not be here. We will hopefully dockerize/containerize this
# So the environment variables are global in the app
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TRACKER_1 = os.getenv('TRACKER_1')

# initialize the flask app
app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')
# sqlalchemy track mod is required to speed up queries
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# access our database
app.config['SQLALCHEMY_DATABASE_URI'] = uri
db.init_app(app)

twilio_client = Twilio().client

@app.route('/', methods=['GET', 'POST'])
def landing():
    if request.method == 'POST':
        # Init all session vars
        return home()
    else:
        # Not logged in
        return render_template('landing.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Init all session vars
        session['email'] = request.form['email']
        session['name'] = request.form['name']
        session['media'] = request.form['media']
        session['user'] = True

    if in_person_first_time(session['email'], session['media']):
        # First time this person has logged in, we need to get their email
        return render_template("welcome.html")

    session['user_id'] = get_user_id(session['email'], session['media'])
    print('user id:', session['user_id'])

    new_trackers = get_new_tracker(session['user_id'])
    if len(new_trackers) > 0:
        # There are uninitialized trackers
        return new_tracker(new_trackers)
    else:
        # Go to the page of trackers
        return trackers()

@app.route('/trackers', methods=['POST', 'GET'])
def trackers():
    # Get the list of trackers
    session['trackers'] = get_trackers(session['user_id'])
    return render_template("trackers.html", pings=session['trackers'])

@app.route('/new', methods=['POST', 'GET'])
def new():
    if request.method == 'POST':
        # Get their primary number
        session['phone'] = request.form['phone']
        # Link their fb email to their phone number
        linked = link(session['phone'], session['email'], session['media'], session['name'])
        session['user_id'] = get_user_id(session['email'], session['media'])
        print('user id:', session['user_id'])
        if not linked:
            # Take them back to enter their number again
            return render_template("welcome.html", try_again='true')

    # Get any new trackers they need to init
    new_trackers = get_new_tracker(session['user_id'])
    if len(new_trackers) > 0:
        # They have an unintialized tracker they need to verify
        return new_tracker(new_trackers)
    elif len(new_trackers) == 0:
        # No trackers for them to initialize
        return home()

@app.route('/new_tracker', methods=['POST', 'GET'])
def new_tracker(trackers):
    # List of zipped tracker info:
    # [zip(tracker_id, tracker_name, imei, type_, make, model, year, color)]
    info = tracker_info(trackers)
    print(info)
    return render_template("info.html", trackers=info)

@app.route('/ping', methods=['POST', 'GET'])
def ping_it():
    # Make a call to the tracker
    # The tracker will acknoledge the call and then hang up
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

@app.route('/logout')
def logout():
    # Get rid of the session vars
    session.pop('user', None)
    session.pop('email', None)
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('media', None)
    session.pop('phone', None)
    session.pop('pings', None)
    # Go home
    return redirect('/')

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

import os
import json
# For debugging
import logging, traceback

from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from runenv import load_env
from flask_sqlalchemy import SQLAlchemy

# Include our own models
from data.check import in_person, link, in_person_first_time, get_new_tracker, get_trackers, get_user_id
from data.tracker import get_info, init
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
    if request.method == 'POST' or session['user']:
        # Init all session vars
        return redirect(url_for('home'))
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

    if session['user']:
        print('Session vars', session['email'], session['name'], session['media'])

    if in_person_first_time(session['email'], session['media']):
        # First time this person has logged in, we need to get their email
        return render_template("welcome.html")

    session['user_id'] = get_user_id(session['email'], session['media'])
    print('user id:', session['user_id'])

    # List of dicts with tracker info:
    # [{tracker_id, tracker_name, imei, type_, make, model, year, color}]
    # Separate the list of tracker ids and the tracker's info
    # So we don't pass the tracker id into front end
    session['new_trackers'] = get_new_tracker(session['user_id'])
    session['new_tracker_info'] = get_info(session['new_trackers'])
    if len(session['new_tracker_info']) > 0:
        # There are uninitialized trackers
        return redirect(url_for('new_tracker'))
    else:
        # Go to the page of trackers
        return redirect(url_for('trackers'))

@app.route('/trackers', methods=['POST', 'GET'])
def trackers():
    # Get the list of trackers
    session['tracker_names'] = get_trackers(session['user_id'])
    return render_template("trackers.html", pings=session['tracker_names'])

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
    if len(session['new_trackers']) > 0:
        # They have an unintialized tracker they need to verify
        return redirect(url_for('new_tracker'))
    else:
        # No trackers for them to initialize
        return redirect(url_for('home'))

@app.route('/new_tracker', methods=['POST', 'GET'])
def new_tracker():
    # After a submit, check if there are any more new trackers to initialize
    if request.method == 'POST':
        print('Got an ajax post')
        if (len(session['new_tracker_info']) > 0):
            # Get the tracker info from form and commit to db
            inputs = request.form
            if len(inputs) > 0:
                added = init(inputs, session['new_trackers'][0])
                print('added:', added, inputs)
                if not added:
                    print('not added')
                    # Commit not successful, refresh, put up an error message
                    return render_template("info.html", tracker=session['new_tracker_info'][0], error_msg="Sorry, something went wrong, please try again")
                else:
                    # Commit successful
                    # Remove the first tracker's info - the one just committed
                    print('added')
                    session['new_trackers'] = session['new_trackers'][1:]
                    session['new_tracker_info'] = session['new_tracker_info'][1:]

    # For simplicity, render one form/one tracker's info at a time
    if len(session['new_tracker_info']) > 0:
        # There are still uninitialized trackers
        return render_template("info.html", tracker=session['new_tracker_info'][0])
    else:
        # No new trackers, go to the main trackers page
        return redirect(url_for('trackers'))

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

# This will just be a button on the tracker's page
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
    # Point browser to localhost:8000
    app.run(port=8000, debug=True)

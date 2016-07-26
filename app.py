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
from data.check import in_person, link, in_person_first_time
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
        session['email'] = request.form['email']
        session['name'] = request.form['name']
        session['user'] = True
        print('session["user"]:', session['user'])
        return home()
    else:
        print('not logged in')
        return render_template('landing.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    print('home:', session['email'], session['name'])
    if in_person_first_time(session['email'], 'fb'):
        print('first time user login')
        return render_template("welcome.html")
    else:
        # Take then to their trackers
        session['pings'] = Pings(twilio_client, session['email'])
        return redirect(url_for('trackers'))

@app.route('/trackers', methods=['POST', 'GET'])
def trackers():
    print('email:', session['email'])
    # Get the list of trackers

    return render_template("trackers.html", pings=session['pings'].trackers)

@app.route('/logout')
def logout():
    # Get rid of the session vars
    session['user'] = False
    session.pop('email', None)
    session.pop('name', None)
    session.pop('phone', None)
    session.pop('pings', None)
    # Go home
    return redirect('/')

@app.route('/new', methods=['POST', 'GET'])
def firstLogin():
    try:
        # Get info on what they're tracking
        # Name, vehicle info
        session['phone'] = request.form['phone']
        # Link their fb email to their phone number
        # returns {user:{user info}, trackers:[{tracker info}]}
        info = link(session['phone'], session['email'], 'fb')
        print(info)

        return render_template("info.html", info=info)
    except Exception as e:
        # Fall back home if fail
        print(e)
        return render_template('landing.html')

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

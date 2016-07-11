import os
import json
import logging

from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from runenv import load_env
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy


from data.check import in_person, link, in_person_first_time
from model.db import db
from data.pings import Pings
from connect.database import uri
from connect.phone import Twilio

load_env(env_file='.env')
# Ideally this will not be here. We will eventually containerize this
# So the environment variables are global in the app
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
# TRACKER_APP_ID = os.getenv('TRACKER_APP_ID')
TRACKER_1 = os.getenv('TRACKER_1')

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.secret_key = os.getenv('APP_SECRET_KEY')
db.init_app(app)

twilio_client = Twilio().client

email = None

@app.route('/', methods=['POST', 'GET'])
def landing():
    try:
        # Go to heythere (prompt phone input) or landing if already signed up
        email = request.form['email']
        session['user'] = True
        print(email)
        if in_person_first_time(email):
            print('here')
            return render_template("heythere.html")
        else:
            print('here?')
            return render_template("landing.html")
    except Exception as e:
        # Go to landing if fails
        print(e)
        return render_template('landing.html')
        # return render_template("oops.html")

@app.route('/logout')
def logout():
    # Get rid of the session vars, take back home
    session.pop('user', None)
    email = None
    return redirect('/')

@app.route('/firsttime', methods=['POST', 'GET'])
def firstLogin():
    # Get info on what they're tracking
    try:
        phone = request.form['phone']
        email = request.form['email']
        if in_person_first_time(phone, email):
            # Did this person pay in person (we have their phone # but they haven't logged in through FB yet)
            info = link(phone, email)

            print(email, phone, info)
            # Link their fb email to this account
            # returns {user:{user info}, trackers:[{tracker info}]}
            return render_template("info.html", info=info)
        else:
            return render_template("new.html")
    except:
        # Fall back home if fail
        return render_template('landing.html')
        # return render_template("oops.html")

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

@app.route('/trackers', methods=['POST', 'GET'])
def load_pings():
    email = request.args.get('email', '', type=str)
    print('email', email)
    pings = Pings(twilio_client, email)

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

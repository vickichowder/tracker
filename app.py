import logging
import os
import json

from datetime import date
from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
from runenv import load_env

from connect.phone import Twilio
from connect.database import DB
from data.pings import Pings

app = Flask(__name__)

load_env(env_file='.env')
# Ideally this will not be here. We will eventually containerize this
# So the environment variables are global in the app
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TRACKER_APP_ID = os.getenv('TRACKER_APP_ID')
TRACKER_1 = os.getenv('TRACKER_1')

twilio_client = Twilio().client
db_client = DB().client

@app.route('/')
def landing():
    # Boring af landing page
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
    # Make a call to the tracker
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
    pings = Pings(twilio_client, db_client, email)

    return render_template("pinged.html", pings=pings.data, email=email)

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

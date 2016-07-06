import logging
import os
import json

from datetime import date
from flask import Flask, request, session, redirect, render_template, url_for, json
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException

from runenv import load_env

# Load environment variables from .env file
load_env(env_file='.env')

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TRACKER_APP_ID = os.getenv('TRACKER_APP_ID')
TRACKER_1 = os.getenv('TRACKER_1')

app = Flask(__name__)

def get_client():
    # Create and return Twilio client
    try:
        client = TwilioRestClient(account=TWILIO_ACCOUNT_SID, token=TWILIO_AUTH_TOKEN)
        print('Retrieved a twilio client object')
        return client
    except TwilioRestException as e:
        print("Could not establish Twilio client")
        print(e)
        print('--------------------\n')
        traceback.print_exc(file=sys.stdout)
        return

@app.route('/')
def landing():
    # Boring af landing page
    return render_template("landing.html")

@app.route('/ping', methods=['POST', 'GET'])
def ping_it():
    # Make a call to the tracker
    client = get_client()
    call = client.calls.create(
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
    client = get_client()
    call = client.calls.get(call_sid)

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

@app.route('/sms', methods=['POST', 'GET'])
def receive_sms():
    # Retrieve all sms from tracker 1 and print it
    client = get_client()

    # Orders from most recent to oldest
    sms_list = client.sms.messages.list(to=TWILIO_NUMBER)
    # list of strings with details of each ping
    pings = []

    # number the message and print the body of message
    for (index, sms) in enumerate(sms_list):
        # parse through sms body
        if ('maps' in sms.body) and ('T:' in sms.body):
            # Parse through body only if it returns with google maps link
            details = sms.body.split(' ')
            ping = {}
            for (index, val) in enumerate(details):
                # Parse through the message body, build a return string

                if ('T:' in val):
                    # Get the date and time
                    ping["to"] = sms.to
                    ping["timestamp"] = "{} {}".format(val[4:], details[index + 1])
                elif ('maps' in val) and (len(val) > 50):
                    # Get the maps link
                    ping["link"] = val[2:]

            if len(ping) == 3:
                pings.append(ping)
                print(ping)

    return render_template("tracked.html", pings=pings)

@app.route('/auth/<string:phone>', methods=['POST', 'GET'])
def add_auth(phone):
    # Add an authorized number to the tracker
    client = get_client()
    # send phone number to authorize with predefined template
    message = client.messages.create(to=TRACKER_1, from_=TWILIO_NUMBER,
                                     body="admin123456 " + phone)
    # Wooooo admin added
    stringy = """
        <h1>Add admin request sent</h1>
        Added admin: {}<br>
        Sms id: {}<br>
        Status: {}<br>
    """.format(phone, message.sid, message.status)

    return(stringy)

@app.route('/apn', methods=['POST', 'GET'])
def set_apn():
    # Add an authorized number to the tracker
    client = get_client()
    # send phone number to authorize with predefined template
    message = client.messages.create(to=TRACKER_1, from_=TWILIO_NUMBER,
                                     body="check123456")
    # Wooooo admin added
    stringy = """
        <h1>APN request sent</h1>
        Sms id: {}<br>
        Status: {}<br>
        Sms body: {}<br>
    """.format(message.sid, message.status, message.body)

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

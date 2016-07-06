import logging
import os

from datetime import date
from flask import Flask, request
from twilio import twiml
from twilio.rest import TwilioRestClient
from twilio import TwilioRestException

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TRACKER_APP_ID = os.getenv('TRACKER_APP_ID')
TRACKER_1 = os.getenv('TRACKER_1')

app = Flask(__name__)
print(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
def get_client():
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
    return('Landing page')

@app.route('/call', methods=['POST', 'GET'])
def receive_call():
    # Make a call to the tracker
    client = get_client()
    call = client.calls.create(
        to=TRACKER_1,
        from_=TWILIO_NUMBER,
        url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient")

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

@app.route('/status/<string:call_sid>', methods=['POST', 'GET'])
def status_refresh(call_sid):
    # Make a call to the tracker
    client = get_client()
    call = client.calls.get(call_sid)

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

    sms_list = client.sms.messages.list()

    stringy = """
        <h1>Received messages</h1>
        Found {} incoming sms:<br>
    """.format(len(sms_list))

    for (index, sms) in enumerate(sms_list):
        stringy += str(index+1) + ": " + sms.body + "<br>"

    return(stringy)

@app.route('/auth/<string:phone>', methods=['POST', 'GET'])
def add_auth(phone):
    # Retrieve all sms from tracker 1 and print it
    client = get_client()

    message = client.messages.create(to=TRACKER_1, from_=TWILIO_NUMBER,
                                     body="admin123456 " + phone)

    stringy = """
        <h1>Add admin request sent</h1>
        Added admin: {}<br>
        Sms id: {}<br>
        Status: {}<br>
    """.format(phone, message.sid, message.status)

    return(stringy)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    app.run(port=8000, debug=True)

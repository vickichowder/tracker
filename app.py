import os
import json
# For debugging
import logging, traceback

from flask import Flask, request, session, redirect, render_template, url_for, jsonify
from twilio import twiml
from runenv import load_env
from flask_sqlalchemy import SQLAlchemy

# Include our own models
import data.check as dc
import data.tracker as dt
import data.user as du
from model.db import db
from connect.database import uri

# Create and fill out .env file from .env_sample
load_env(env_file='.env')
# Ideally this will not be here. We will hopefully dockerize/containerize this
# So the environment variables are global in the app
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')

# initialize the flask app
app = Flask(__name__)

# Secret key so our session vars stay safe
app.secret_key = os.getenv('APP_SECRET_KEY')

# sqlalchemy track mod is required to speed up queries
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# access database
app.config['SQLALCHEMY_DATABASE_URI'] = uri
db.init_app(app)


@app.route('/', methods=['GET', 'POST'])
def landing():
    return render_template('landing.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Init session vars
        session['email'] = request.form['email']
        session['name'] = request.form['name']
        session['media'] = request.form['media']
        session['user'] = True

    if in_person_first_time(session['email'], session['media']):
        # First time this person has logged in, we need to get their email
        return render_template("welcome.html")

    # Save user id into this session
    session['user_id'] = du.get_user_id(session['email'], session['media'])
    print('user id:', session['user_id'])

    # List of dicts with tracker info:
    # [{tracker_id, tracker_name, imei, type_, make, model, year, color}]
    # Separate the list of tracker ids and the tracker's info
    # So we don't pass the tracker id into front end
    session['new_trackers'] = dt.get_new_tracker(session['user_id'])
    session['new_tracker_info'] = dt.get_info(session['new_trackers'])

    if len(session['new_tracker_info']) > 0:
        # There are uninitialized trackers
        return redirect(url_for('new_tracker'))
    else:
        # Go to page of trackers
        return redirect(url_for('trackers'))

@app.route('/trackers', methods=['POST', 'GET'])
def trackers():
    # Get list of trackers for this user_id
    session['tracker_name_id'] = dt.get_trackers(session['user_id'])

    admin = du.get_role(session['user_id'])

    if admin:
        return render_template("trackers.html", tracker_names=list(session['tracker_name_id'].keys()), admin=True)
    else:
        return render_template("trackers.html", tracker_names=list(session['tracker_name_id'].keys()))

@app.route('/credits', methods=['POST', 'GET'])
def credits():
    remaining = du.get_credits(session['user_id'])

    return render_template("credits.html", credits_remaining=remaining)

@app.route('/new', methods=['POST', 'GET'])
def new():
    if request.method == 'POST':
        # Get their primary number
        session['phone'] = request.form['phone']

        # Link their fb email to their phone number
        linked = du.link(session['phone'], session['email'], session['media'], session['name'])
        session['user_id'] = du.get_user_id(session['email'], session['media'])
        print('user id:', session['user_id'])

        if not linked:
            # Take them back to enter their number again
            return render_template("welcome.html", try_again='true')

    # Get any new trackers they need to init
    if len(session['new_trackers']) > 0:
        # They have an unintialized tracker they need to verify
        return redirect(url_for('new_tracker'))
    else:
        # No trackers to initialize
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
                added = dt.init(inputs, session['new_trackers'][0])
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
        # No more new trackers, go to main trackers page
        return redirect(url_for('trackers'))

@app.route('/tracker/<string:tracker_name>', methods=['POST', 'GET'])
def tracker_name(tracker_name):
    # Get their remaining credits
    credits = du.get_credits(session['user_id'])
    # Read locations from db
    locations = dt.get_locations(dt.get_tracker_id(session['user_id'], tracker_name))

    return render_template("location.html", locations=locations, tracker_name=tracker_name, credits=credits)

@app.route('/ping/<string:tracker_name>', methods=['POST', 'GET'])
def ping(tracker_name):
    try:
        # Make a call to the tracker
        # The tracker will acknoledge the call and then hang up
        call = twilio_client.calls.create(
            to=get_tracker_id(session['user_id'], tracker_name),
            from_=TWILIO_NUMBER,
            url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient")
        du.use_credit(session['user_id'])
    except Exception as e:
        print(e)

    return redirect('/tracker/'+tracker_name)

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        # Grap user info from new register page
        user = request.form
        added = du.init(user)

        # Print different messages on page depending on outcome
        if added:
            return render_template('register.html', added='success', user=user['name'])
        else:
            return render_template('register.html', added='fail')

    return render_template('register.html')

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
    session.pop('twilio_client', None)
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

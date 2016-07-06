import os, logging

from twilio.rest import TwilioRestClient
from twilio import TwilioRestException
from runenv import load_env

class Twilio:
    load_env(env_file='.env')
    def __init__(self):
        self.config = {
            "account" : os.getenv('TWILIO_ACCOUNT_SID'),
            "token" : os.getenv('TWILIO_AUTH_TOKEN') }
        self.client = self.get_client()

    def get_client(self):
        # Create and return Twilio client
        try:
            client = TwilioRestClient(**self.config)
            print('Retrieved a twilio client object')
            return client
        except TwilioRestException as e:
            print("Could not establish Twilio client")
            print(e)
            return

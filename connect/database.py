import os, logging
import MySQLdb

from runenv import load_env

class DB:
    load_env(env_file='.env')
    def __init__(self):
        self.config = {
            "host" : os.getenv('DB_HOST'),
            "user" : os.getenv('DB_USER'),
            "passwd" : os.getenv('DB_PW'),
            "db" : os.getenv('DB_NAME') }

        self.client = self.get_client()

    def get_client(self):
        # Create and return Twilio client
        try:
            client = MySQLdb.connect(**self.config)
            print('Retrieved a mysql client object')
            return client
        except Exception as e:
            print("Could not establish Mysql client")
            print(e)
            return

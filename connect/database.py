import os, logging

from runenv import load_env

class DB:
    load_env(env_file='.env')
    def __init__(self):
        self.config = {
            "host" : os.getenv('DB_HOST'),
            "user" : os.getenv('DB_USER'),
            "passwd" : os.getenv('DB_PW'),
            "db" : os.getenv('DB_NAME'),
            "port" : int(os.getenv('DB_PORT')) }

        self.uri = 'mysql://' +\
            os.getenv('DB_USER') + ':' +\
            os.getenv('DB_PW') + '@' +\
            os.getenv('DB_HOST') + ':' +\
            os.getenv('DB_PORT') + '/' +\
            os.getenv('DB_NAME')

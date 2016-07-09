import os, logging

from runenv import load_env

load_env(env_file='.env')
uri = 'mysql://' +\
    os.getenv('DB_USER') + ':' +\
    os.getenv('DB_PW') + '@' +\
    os.getenv('DB_HOST') + ':' +\
    os.getenv('DB_PORT') + '/' +\
    os.getenv('DB_NAME')

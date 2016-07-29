import os, logging

from math import floor

from twilio import twiml
from flask_sqlalchemy import SQLAlchemy

from model.db import db
from model.position import Position
from model.tracker import Tracker
from model.user import User

def listify_column(result):
    # Turn the results of a sqlalchemy cursor of one column into list
    result_list = []

    for row in result:
        result_list.append(row[0])

    return result_list

import os, logging
import pymysql

from twilio import twiml

class Pings:
    def __init__(self, twilio_client, db_client, email):
        self.data = []
        self.phones = []
        self.email = email

        self.refresh(twilio_client, db_client)
        self.get_locations(db_client, email)

    def refresh(self, twilio_client, db_client):
        # get the tracker phone number(s)
        c = db_client.cursor(pymysql.cursors.DictCursor)
        c.execute("SELECT tracker_id FROM trackers WHERE email = '{}'".format(self.email))
        self.phones = c.fetchall()
        c.close()
        print(self.phones[0]['tracker_id'])
        # Get the most recent ping
        sms = twilio_client.sms.messages.list(from_=self.phones[0]['tracker_id'])[0]
        print(sms)
        timestamp = ''
        latitude = ''
        longitude = ''

        # number the message and print the body of message
        if ('maps' in sms.body) and ('T:' in sms.body):
            # Parse through body only if it returns with google maps link
            details = sms.body.split(' ')
            for (index, val) in enumerate(details):
                # Parse through the message body, build a return string

                if ('lat:' in val) and (len(val) > 5):
                    # Get latitude
                    latitude = val[6:]
                elif ('long:' in val) and (len(val) > 5):
                    # Get longitude
                    longitude = val[5:]
                elif ('T:' in val):
                    # Get the date and time
                    timestamp = "{} {}".format(val[4:], details[index + 1])

            c = db_client.cursor()
            try:
                insert = "INSERT INTO positions VALUES ('{}', STR_TO_DATE('{}','%m/%d/%y %H:%i'), {}, {})".format(self.phones[0]['tracker_id'], timestamp, latitude, longitude)
                c.execute(insert)
                db_client.commit()
                c.close()
                print(insert, '\n')
            except Exception as e:
                db_client.rollback()
                print("Could not execute insert", e)

    def get_locations(self, db_client, email):
        # Retrieve all sms from tracker phone number
        c = db_client.cursor(pymysql.cursors.DictCursor)
        pings = []
        try:
            c.execute("""
                SELECT * FROM positions p
                JOIN trackers t ON p.tracker_id = t.tracker_id
                WHERE t.tracker_id='{}'
                    AND t.email='{}' ORDER BY p.pinged_on DESC
                """.format(self.phones[0]['tracker_id'], email))
            data = c.fetchall()
            print(data)
            for row in data:
                ping = {}
                ping['timestamp'] = row['pinged_on']
                ping['link'] = "https://www.google.com/maps?f=q&q={},{}&z=16".format(row['latitude'], row['longitude'])
                pings.append(ping)
                print(ping)

        except Exception as e:
            print("Could not execute select", e)

        self.data = pings

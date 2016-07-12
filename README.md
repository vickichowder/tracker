# Tracker

Bootstrapped:
- [x] Landing
- [x] Signed in
- [ ] Form for new sign in
- [ ] List of trackers
- [ ] Positions of tracker (with 'ping' button)

### Requirements
Runs on Python 3
Install the following with `pip3`:
```
pymysql
twilio
flask
runenv
```
### Usage
Fill in `.env_sample`, rename it to `.env`

### Database
Recreate the `mysql` db with `build.sql` locally. Port is default 3306 so no need to specify it in command
Run:
```
mysql -u [yourusername] -p[yourpassword] <data/build.sql
```
Insert commands can be modified.

### Run
```
python3 app.py
```
Point to `localhost:8000`

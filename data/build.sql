create database tracker;

use tracker;

create table `position`(
   tracker_id VARCHAR(12) NOT NULL,
   `time` datetime NOT NULL,
   latitude DECIMAL(8,5),
   longitude DECIMAL(8,5),
   PRIMARY KEY ( tracker_id, `time`, latitude, longitude )
);

create table tracker(
  tracker_id varchar(12) not null unique,
  user_id int not null,
  added int default 0, -- Initially not added/initialized by user = 0 / False
  tracker_name varchar(80) not null,
  imei varchar(15) unique,
  type_ varchar(50) not null default 'Vehicle',
  make varchar(50),
  model varchar(50),
  year int,
  color varchar(50),
  primary key (tracker_id)
);

create table user(
  user_id int not null auto_increment,
  phone varchar(10) not null unique,
  name varchar(120),
  email varchar(80) default null, -- contact email
  fb_email varchar(80) default null,
  google_email varchar(80) default null,
  balance int default 0, -- in cents
  role varchar(50) not null default 'User',
  primary key (user_id)
);

insert into user (phone, name, role) values('4169392992', 'Vicki', 'Admin');
insert into user (phone, name, role) values('6474488877', 'Martin', 'Admin');

insert into tracker (tracker_id, user_id, tracker_name, imei) values ('+16478776809', 1, 'The first one', '123456789012345');
insert into tracker (tracker_id, user_id, tracker_name, imei) values ('+16479710112', 2, 'Martin\'s', '123456789012344');

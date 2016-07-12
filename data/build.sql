create database tracker;

use tracker;

create table position(
   tracker_id VARCHAR(12) NOT NULL,
   pinged_on datetime NOT NULL,
   latitude DECIMAL(8,5),
   longitude DECIMAL(8,5),
   PRIMARY KEY ( tracker_id, pinged_on, latitude, longitude )
);

create table tracker(
  tracker_id varchar(12) not null unique,
  user_id int not null,
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
  email varchar(50),
  name varchar(120),
  balance int default 0,
  type varchar(50) not null default 'User',
  primary key (user_id)
);

insert into user (phone, email, name) values('4169392992', null, null);

insert into tracker (tracker_id, user_id, tracker_name, imei) values ('+16478776809', 1, 'The first one', '123456789012345');

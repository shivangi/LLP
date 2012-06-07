-- Schema creation script for LLP aggregate DB
-- This DB drives the LLP website
-- This code is released under the terms of the GNU GPL v3 
-- and is free software

DROP TABLE IF EXISTS "tb_bhierarchy" cascade;
CREATE TABLE "tb_bhierarchy" (
  "id" integer unique, -- 'Hierarchy id'
  "name" varchar(300) NOT NULL,
  PRIMARY KEY  ("id")
);

insert into tb_bhierarchy (id,name) values (14,'project');
insert into tb_bhierarchy (id,name) values (15,'circle');
insert into tb_bhierarchy (id,name) values (13,'district');
insert into tb_bhierarchy (id,name) values (11,'cluster');
insert into tb_bhierarchy (id,name) values (10,'block');
insert into tb_bhierarchy (id,name) values (12,'school');
insert into tb_bhierarchy (id,name) values (9,'district');


DROP TABLE IF EXISTS "tb_boundary_type" cascade;
CREATE TABLE "tb_boundary_type" (
  "id" integer unique, 
  "name" varchar(300) NOT NULL,
  PRIMARY KEY  ("id")
);

insert into tb_boundary_type (id,name) values (1,'Primary School');
insert into tb_boundary_type (id,name) values (2,'Pre School');
insert into tb_boundary_type (id,name) values (3,'High School');

DROP TABLE IF EXISTS "tb_boundary" cascade;
CREATE TABLE "tb_boundary" (
  "id" integer unique, -- 'Boundary id'
  "parent" integer default NULL,
  "name" varchar(300) NOT NULL,
  "hid" integer NOT NULL references "tb_bhierarchy" ("id") on delete cascade,
  "type" integer NOT NULL references "tb_boundary_type" ("id") on delete cascade,
  PRIMARY KEY  ("id")
);


DROP TYPE IF EXISTS school_category cascade;
CREATE TYPE school_category as enum('Others',  'Primary', 'Pri. with U.Pri.', 'Pri. with UP', 'High School', 'U Primary only','Pri. with UP, Sec/HS');
DROP TYPE IF EXISTS school_sex cascade;
CREATE TYPE school_sex as enum('Boys','Girls','Co-ed');
DROP TYPE IF EXISTS sex cascade;
CREATE TYPE sex as enum('male','female');
DROP TYPE IF EXISTS school_moi cascade;
CREATE TYPE school_moi as enum('Kannada','Urdu','Tamil','Telugu','English','Marathi','Malayalam', 'Hindi', 'Konkani', 'Sanskrit', 'Sindhi', 'Other', 'Gujarathi', 'Not known', 'English and Marathi', 'Multi lng', 'Nepali', 'Oriya', 'Bengali', 'English and Hindi', 'English, Telugu and Urdu');  -- 'Medium of instruction
DROP TYPE IF EXISTS school_management cascade;
CREATE TYPE school_management as enum('Department of Education','Pvt. Unaided','Central Govt.','Others');

DROP TABLE IF EXISTS "tb_address" cascade;
CREATE TABLE "tb_address" (
  "id" integer unique, -- 'Address id'
  "address" varchar(1000) default NULL,
  "area" varchar(1000) default NULL,
  "pincode" varchar(20) default NULL,
  "landmark" varchar(1000) default NULL,
  "instidentification" varchar(1000) default NULL,
  "bus" varchar(1000) default NULL,
  "instidentification2" varchar(1000) default NULL,
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_school" cascade;
CREATE TABLE "tb_school" (
  "id" integer unique, -- 'School id'
  "aid" integer NOT NULL REFERENCES "tb_address" ("id") ON DELETE CASCADE, 
  "bid" integer NOT NULL REFERENCES "tb_boundary" ("id") ON DELETE CASCADE, -- 'Lowest Boundary id'
  "dise_code" varchar(14) default NULL,
  "name" varchar(300) NOT NULL,
  "cat" school_category default NULL,
  "sex" school_sex default 'Co-ed',
  "moi" school_moi default 'English',
  "mgmt" school_management default 'Department of Education',
  "status" integer NOT NULL,
  PRIMARY KEY  ("id")
);

DROP TABLE IF EXISTS "tb_child" cascade;
CREATE TABLE "tb_child" (
  "id" integer unique, -- 'School id'
  "name" varchar(300),
  "dob" date default NULL,
  "sex" sex NOT NULL default 'male',
  "mt" school_moi default 'English', -- Mother tongue   Change this depending on what is correct for that geography
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_class" cascade;
CREATE TABLE "tb_class" (
  "id" integer unique, -- 'Class id'
  "sid" integer, -- School id
  "name" char(50) NOT NULL,
  "section" char(1) default NULL,  
  PRIMARY KEY ("id")
);
DROP TABLE IF EXISTS "tb_academic_year" cascade;
CREATE TABLE "tb_academic_year" (
  "id" integer unique, -- 'Academic year id'
  "name" varchar(20),
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_student" cascade;
CREATE TABLE "tb_student" (
  "id" integer unique, -- 'Student id'  
  "cid" integer NOT NULL REFERENCES "tb_child" ("id") ON DELETE CASCADE, -- 'Child id'
  "otherstudentid" varchar(100),
  "status" integer NOT NULL,
  PRIMARY KEY ("id")
);
DROP TABLE IF EXISTS "tb_student_class" cascade;
CREATE TABLE "tb_student_class" ( 
 "stuid" integer NOT NULL REFERENCES "tb_student" ("id") ON DELETE CASCADE, 
 "clid" integer NOT NULL REFERENCES "tb_class" ("id") ON DELETE CASCADE,
 "ayid" integer NOT NULL REFERENCES "tb_academic_year" ("id") ON DELETE CASCADE,
 "status" integer NOT NULL
);

DROP TABLE IF EXISTS "tb_programme" cascade;
CREATE TABLE "tb_programme" (
  "id" serial unique, -- 'Programme id'
  "name" varchar(300) NOT NULL,
  "start" date default CURRENT_DATE,
  "end" date default CURRENT_DATE,
  "type" integer NOT NULL references "tb_boundary_type" ("id") on delete cascade,
  "ayid" integer  REFERENCES "tb_academic_year" ("id") ON DELETE CASCADE,
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_assessment" cascade;
CREATE TABLE "tb_assessment" (
  "id" serial unique, -- 'Assessment id'
  "name" varchar(300) NOT NULL,
  "pid" integer references "tb_programme" ("id") ON DELETE CASCADE, -- Programme id
  "start" date default CURRENT_DATE,
  "end" date default CURRENT_DATE,
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_question" cascade;
CREATE TABLE "tb_question" (
  "id" integer, -- 'Question id'
  "assid" integer references "tb_assessment" ("id") ON DELETE CASCADE, -- Assessment id
  "desc" varchar(100) NOT NULL,
  "qtype" integer, --0- grade, 1-marks
  "maxmarks" decimal,
  "minmarks" decimal default 0,
  "grade" varchar(100),
  PRIMARY KEY ("id")
);

DROP TABLE IF EXISTS "tb_student_eval" cascade;
CREATE TABLE "tb_student_eval" (
  "qid" integer references "tb_question" ("id") ON DELETE CASCADE, -- 'Question id'
  "stuid" integer references "tb_student" ("id") ON DELETE CASCADE, -- Student id
  "mark" numeric(5,2) default NULL,
  "grade" char(2) default NULL,
  PRIMARY KEY ("qid", "stuid")
);



-- Remote views via dblink

CREATE OR REPLACE VIEW vw_boundary_coord as 
       select * from dblink('host=localhost dbname=llp-coord user=klp password=1q2w3e4r', 'select * from boundary_coord') 
       as t1 (id_bndry integer, 
              type varchar(20), 
              coord geometry);

CREATE OR REPLACE VIEW vw_inst_coord as
       select * from dblink('host=localhost dbname=llp-coord user=klp password=1q2w3e4r', 'select * from inst_coord') 
       as t2 (instid integer,
              coord geometry);

-- The web user will query the DB
GRANT SELECT ON tb_school, 
                tb_bhierarchy, 
                tb_boundary, 
                tb_boundary_type, 
                tb_address,
                tb_student,
                tb_academic_year,
                tb_programme,
                tb_assessment,
                tb_question,
                tb_class,
                tb_child,
                tb_student_class,
                tb_student_eval,
                vw_boundary_coord, 
                vw_inst_coord
TO web;


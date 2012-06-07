DROP TABLE IF EXISTS "tb_sys_data" cascade;
CREATE TABLE "tb_sys_data" (
  "id" serial unique, -- 'SYS id'
  "schoolid" integer,
  "name" varchar(100),
  "email" varchar(100),
  "telephone" varchar(50),
  "dateofvisit" varchar(50),
  "comments" varchar(500),
  "entered_timestamp" timestamp with time zone not null default now(),
  "verified" varchar(1) default 'N'
);

DROP TABLE IF EXISTS "tb_sys_qans";
CREATE TABLE "tb_sys_qans"(
  "sysid" integer NOT NULL references "tb_sys_data" ("id") on delete cascade,
  "qid" integer,
  "answer" varchar(500)
);

DROP TYPE IF EXISTS sys_question_type;
CREATE TYPE sys_question_type as enum('text', 'numeric', 'radio','checkbox');

DROP TABLE IF EXISTS "tb_sys_questions";
CREATE TABLE "tb_sys_questions" (
  "id" serial unique, -- 'Question id'
  "hiertype" integer, -- 1 for school, 2 for preschool
  "qtext" varchar(500),
  "qfield" varchar(50)
);
 
--Seed data for school questions
INSERT INTO tb_sys_questions values(default,1,'An All weather (pucca) building','schoolq1');
INSERT INTO tb_sys_questions values(default,1,'Boundary wall/ Fencing','schoolq2');
INSERT INTO tb_sys_questions values(default,1,'Play ground','schoolq3');
INSERT INTO tb_sys_questions values(default,1,'Accessibility to students with disabilities','schoolq4');
INSERT INTO tb_sys_questions values(default,1,'Separate office for Headmaster','schoolq5');
INSERT INTO tb_sys_questions values(default,1,'Separate room as Kitchen / Store for Mid day meals','schoolq6');
INSERT INTO tb_sys_questions values(default,1,'Separate Toilets for Boys and Girls','schoolq7');
INSERT INTO tb_sys_questions values(default,1,'Drinking Water facility','schoolq8');
INSERT INTO tb_sys_questions values(default,1,'Library','schoolq9');
INSERT INTO tb_sys_questions values(default,1,'Play Material or Sports Equipment','schoolq10');
INSERT INTO tb_sys_questions values(default,1,'Did you see any evidence of mid day meal being served (food being cooked, food waste etc.) on the day of your visit?','schoolq11');
INSERT INTO tb_sys_questions values(default,1,'How many functional class rooms (exclude rooms that are not used for conducting classes for whatever reason) does the school have?','schoolq12');
INSERT INTO tb_sys_questions values(default,1,'Teachers sharing a single class room','schoolq13');
INSERT INTO tb_sys_questions values(default,1,'How many classrooms had no teachers in the class?','schoolq14');
INSERT INTO tb_sys_questions values(default,1,'What was the total numbers of teachers present (including head master)?','schoolq15');

--Seed extra for school questions
INSERT INTO tb_sys_questions values(default,1,'Designated Librarian/Teacher','schoolq16');
INSERT INTO tb_sys_questions values(default,1,'Class-wise timetable for the Library','schoolq17');
INSERT INTO tb_sys_questions values(default,1,'Teaching and Learning material','schoolq18');
INSERT INTO tb_sys_questions values(default,1,'Sufficient number of class rooms','schoolq19');
INSERT INTO tb_sys_questions values(default,1,'Were at least 50% of the children enrolled present on the day you visited the school?','schoolq20');
INSERT INTO tb_sys_questions values(default,1,'Were all teachers present on the day you visited the school?','schoolq21');



DROP TABLE IF EXISTS "tb_sys_displayq";
CREATE TABLE "tb_sys_displayq" (
  "id" serial unique, -- 'Question id'
  "hiertype" integer, -- 1 for school, 2 for preschool
  "qtext" varchar(500),
  "qfield" varchar(50),
  "qtype" sys_question_type,
  "options" varchar(500)[][]
);

--Seed data for school questions
INSERT INTO tb_sys_displayq values(default,1,'Check the boxes to indicate whether you observed or found the following in the school (You can check multiple boxes):','schoolq0','checkbox','{{"schoolq1","An All weather (Pucca) building"},{"schoolq2","Boundary wall/ Fencing"},{"schoolq3","Play ground"},{"schoolq7","Separate Toilets for Boys and Girls"},{"schoolq8","Drinking Water facility"},{"schoolq5","Separate office for Headmaster"},{"schoolq6","Separate room as Kitchen / Store for Mid day meals"},{"schoolq4","Accessibility to students with disabilities"}}');
INSERT INTO tb_sys_displayq values(default,1,'Check the boxes to indicate whether you observed or found the following in the school (You can check multiple boxes):','schoolq0','checkbox','{{"schoolq9","Library"},{"schoolq16","Designated Librarian/Teacher"},{"schoolq17","Class-wise timetable for the Library"},{"schoolq10","Play Material or Sports Equipment"},{"schoolq18","Teaching and Learning material"},{"schoolq19","Sufficient number of class rooms"},{"schoolq13","Teachers sharing a single class room"}}');
INSERT INTO tb_sys_displayq values(default,1,'Did you see any evidence of mid day meal being served (food being cooked,food waste etc.) on the day of your visit?','schoolq11','radio','{"Yes","No"}');
INSERT INTO tb_sys_displayq values(default,1,'Were at least 50% of the children enrolled present on the day you visited the school?','schoolq20','radio','{"Yes","No"}');
INSERT INTO tb_sys_displayq values(default,1,'Were all teachers present on the day you visited the school?','schoolq21','radio','{"Yes","No"}');




DROP TABLE IF EXISTS "tb_sys_images";
CREATE TABLE "tb_sys_images" (
  "schoolid" integer,
  "original_file" varchar(100),
  "hash_file" varchar(100),
  "verified" varchar(1) default 'N',
  "sysid" integer NOT NULL references "tb_sys_data" ("id") on delete cascade
);


GRANT SELECT ON tb_sys_data,
                tb_sys_displayq,
                tb_sys_questions,
                tb_sys_images
TO web;

GRANT UPDATE ON tb_sys_data,tb_sys_data_id_seq,tb_sys_images TO web;
GRANT INSERT ON tb_sys_data,tb_sys_images,tb_sys_qans TO web;

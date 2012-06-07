-- Aggregation tables

DROP TABLE IF EXISTS "tb_school_agg";
CREATE TABLE "tb_school_agg" (
  "id" integer,
  "name" varchar(300),
  "bid" integer,
  "sex" sex,
  "mt" school_moi,
  "num" integer
);

DROP TABLE IF EXISTS "tb_school_basic_assessment_info";
CREATE TABLE "tb_school_basic_assessment_info" (
  "sid" integer REFERENCES "tb_school" ("id") ON DELETE CASCADE,
  "assid" integer REFERENCES "tb_assessment" ("id") ON DELETE CASCADE,
  "clid" integer REFERENCES "tb_class" ("id") ON DELETE CASCADE,
  "sex" sex,
  "mt" school_moi,
  "num" integer
);

DROP TABLE IF EXISTS "tb_school_assessment_agg";
CREATE TABLE "tb_school_assessment_agg" (
  "sid" integer REFERENCES "tb_school" ("id") ON DELETE CASCADE,
  "assid" integer REFERENCES "tb_assessment" ("id") ON DELETE CASCADE,
  "clid" integer REFERENCES "tb_class" ("id") ON DELETE CASCADE,
  "sex" sex,
  "mt" school_moi,
  "aggtext" varchar(100) NOT NULL,
  "aggval" numeric(6,2) DEFAULT 0
);





CREATE OR REPLACE function agg_school(int) returns void as $$
declare
        schs RECORD;
begin
        for schs in SELECT s.id as id, s.name as name, s.bid as bid, c.sex as sex, c.mt as mt, count(stu.id) AS count
                 FROM tb_student stu, tb_class cl, tb_student_class sc, tb_child c, tb_school s
                 WHERE cl.sid = s.id AND sc.clid = cl.id AND sc.stuid = stu.id AND sc.status=1 AND stu.cid = c.id AND sc.ayid = $1
                 GROUP BY s.id, s.name, s.bid, c.sex, c.mt 
        loop
                insert into tb_school_agg values (schs.id, schs.name, schs.bid, schs.sex, schs.mt, schs.count);
        end loop;
end;
$$ language plpgsql;


CREATE OR REPLACE function basic_assess_school(int,int) returns void as $$
declare
        schs RECORD;
begin
        for schs in SELECT s.id as id,ass.id as assid,cl.id as clid,c.sex as sex, c.mt as mt, count(distinct stu.id) AS count
                 FROM tb_student_eval se,tb_question q,tb_assessment ass,tb_student stu, tb_class cl, tb_student_class sc, tb_child c, tb_school s,tb_programme p,tb_boundary b
                 WHERE se.stuid=stu.id and se.qid=q.id and q.assid=ass.id and ass.pid=p.id and sc.stuid=stu.id and sc.clid=cl.id AND cl.sid = s.id AND stu.cid = c.id AND sc.ayid = $1 and ass.id=$2 and sc.ayid=p.ayid and s.bid=b.id and p.type=b.type
                 GROUP BY s.id, ass.id,cl.id,c.sex,c.mt
        loop
                insert into tb_school_basic_assessment_info values (schs.id, schs.assid, schs.clid ,schs.sex, schs.mt, schs.count);
        end loop;
end;
$$ language plpgsql;


-- Populate tb_school_agg for the current academic year
select agg_school(102);


GRANT SELECT ON tb_school_agg
TO web;

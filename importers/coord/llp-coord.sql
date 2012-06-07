-- This code is released under the terms of the GNU GPL v3 
-- and is free software


DROP TABLE IF EXISTS "inst_coord";
CREATE TABLE "inst_coord" (
  "instid" varchar(14) NOT NULL,
  PRIMARY KEY  ("instid")
);

SELECT AddGeometryColumn('','inst_coord','coord','-1','POINT',2);

DROP TABLE IF EXISTS "boundary_coord";
CREATE TABLE "boundary_coord" (
  "id_bndry" integer NOT NULL,
  "type" varchar(20) NOT NULL,
  PRIMARY KEY  ("id_bndry")
);

SELECT AddGeometryColumn('','boundary_coord','coord','4326','POINT',2);

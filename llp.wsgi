import web
import psycopg2
import decimal
import jsonpickle
import csv
import re
import difflib
import smtplib,email,email.encoders,email.mime.text,email.mime.base,mimetypes
from web import form

# Needed to find the templates
import sys, os,traceback
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

from Utility import KLPDB

urls = (
     '/','visualization',
     '/pointinfo/', 'getPointInfo',
     '/assessment/(.*)/(.*)/(.*)','assessments',
     '/info/school/(.*)','getSchoolInfo',
     '/shareyourstory(.*)\?*','shareyourstory',
     '/schoolpage/(.*)/(.*)','schoolpage',
     '/info/(.*)/(.*)','getBoundaryInfo',
     '/boundaryPoints/(.*)/(.*)','getBoundaryPoints',
     '/villagePoints/(.*)','getVillagePoints',
     '/text/(.+)', 'text',
     '/schoolInfo/(.*)','getSchoolBoundaryInfo',
     '/insertsys/(.*)','insertSYS',
     '/postSYS/(.*)','postSYS',
     '/sysinfo','getSYSInfo',
     '/listFiles/(.*)','listFiles',
)

connection = None
cursor = None
sysconnection = None
syscursor = None


try:
  connection = KLPDB.getConnection()
  cursor = connection.cursor()
  sysconnection = KLPDB.getSysConnection()
  syscursor = sysconnection.cursor()
except:
  print "Unexpected error:", sys.exc_info()
  print "Exception in user code:"
  print '-'*60
  traceback.print_exc(file=sys.stdout)
  print '-'*60

mySchoolform =form.Form(
                   form.Hidden('schoolid'),
                   form.Textbox('name'),
                   form.Textbox('email'),
                   form.Textbox('telephone'),
                   form.Textbox('dateofvisit'),
                   form.File('file1'),
                   form.File('file2'),
                   form.File('file3'),
                   form.File('file4'),
                   form.File('file5'),
                   form.Textarea('comments'),
                   form.Hidden('chkboxes'))


myPreSchoolform =form.Form(
                   form.Hidden('schoolid'),
                   form.Textbox('name'),
                   form.Textbox('email'),
                   form.Textbox('telephone'),
                   form.Textbox('dateofvisit'),
                   form.File('file1'),
                   form.File('file2'),
                   form.File('file3'),
                   form.File('file4'),
                   form.File('file5'),
                   form.Textarea('comments'),
                   form.Hidden('chkboxes'))


preschoolAgeGroup=5
preschoolPids=['5','18']
pidType={"grade":[1,4,5,7,8,13,15,17,18,19,20],"mark":[2,3,6,9,10,11,12,14,16]}

baseassess = {"1":[1],
              "2":[5,6,7,8],
              "3":[13,14,15,16],
              "4":[21],
              "5":[23],
              "6":[25],
              "7":[27],
              "8":[30],
              "9":[33],
              "10":[35],
              "11":[37],
              "12":[39],
              "13":[40],
              "14":[41,43,45,47],
              "15":[49],
              "16":[51,53],
              "18":[56],
              "19":[59]
              }


statements = {'get_district':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='District' and b.id=bcoord.id_bndry order by b.name",
              'get_village':"select distinct area from tb_address order by area",
              'get_preschooldistrict':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='PreSchoolDistrict' and b.id=bcoord.id_bndry order by b.name",
              'get_block':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='Block' and b.id=bcoord.id_bndry order by b.name",
              'get_cluster':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='Cluster' and b.id=bcoord.id_bndry order by b.name",
              'get_project':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='Project' and b.id=bcoord.id_bndry order by b.name",
              'get_circle':"select bcoord.id_bndry,ST_AsText(bcoord.coord),initcap(b.name) from vw_boundary_coord bcoord, tb_boundary b where bcoord.type='Circle' and b.id=bcoord.id_bndry order by b.name",
              'get_school':"select inst.instid ,ST_AsText(inst.coord),upper(s.name) from vw_inst_coord inst, tb_school s,tb_boundary b,tb_bhierarchy bhier where s.id=inst.instid and s.bid=b.id and bhier.id = b.hid and b.type='1' order by s.name",
              'get_preschool':"select inst.instid ,ST_AsText(inst.coord),upper(s.name) from vw_inst_coord inst, tb_school s,tb_boundary b,tb_bhierarchy bhier where s.id=inst.instid and s.bid=b.id and bhier.id = b.hid and b.type='2' order by s.name",
              'get_district_points':"select distinct b1.id, b1.name from tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy hier where b.id=b1.parent and b1.id=b2.parent and b.hid=hier.id and b.type=1 and b.id=%s order by b1.name",
              'get_village_points':"select distinct s.id, s.name from tb_school s, tb_address a where s.aid=a.id and a.area=%s order by s.name",
              'get_preschooldistrict_points':"select distinct b1.id, b1.name from tb_boundary b, tb_boundary b1,tb_boundary b2,tb_bhierarchy hier where b2.parent=b1.id and b1.parent = b.id and b.hid = hier.id and b.type=2 and b.id=%s",
              'get_block_points':"select distinct b2.id, b2.name from tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy hier where b.id=b1.parent and b1.id=b2.parent  and b.hid = hier.id and b.type=1 and b1.id=%s order by b2.name",
              'get_cluster_points':"select distinct s.id, s.name from tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier where b.id=b1.parent and b1.id=b2.parent and s.bid=b2.id and b.hid = hier.id and b.type=1 and b2.id=%s order by s.name",
              'get_project_points':"select distinct b2.id, b2.name from tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy hier where b.id=b1.parent and b1.id=b2.parent  and b.hid = hier.id and b.type=2 and b1.id=%s order by b2.name",
              'get_circle_points':"select distinct s.id, s.name from tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier where b.id=b1.parent and b1.id=b2.parent and s.bid=b2.id and b.hid = hier.id and b.type=2 and b2.id=%s order by s.name",
              'get_district_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b.id = %s group by sv.sex",
              'get_district_info':"select count(distinct sv.id),b.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b.id = %s group by b.name",
              'get_preschooldistrict_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b.id = %s group by sv.sex",
              'get_preschooldistrict_info':"select count(distinct sv.id),b.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b.id = %s group by b.name",
              'get_block_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b1.id = %s group by sv.sex",
              'get_block_info':"select count(distinct sv.id),b1.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b1.id = %s group by b1.name",
              'get_project_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy bhier where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.hid=bhier.id and b.type='2' and b1.id = %s group by sv.sex",
              'get_project_info':"select count(distinct sv.id),b1.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy bhier where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.hid=bhier.id and b.type='2' and b1.id = %s group by b1.name",
              'get_cluster_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.id = %s group by sv.sex",
              'get_cluster_info':"select count(distinct sv.id),b2.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2 where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.id = %s group by b2.name",
              'get_circle_gender':"select sv.sex, sum(sv.num) from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy bhier where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.hid=bhier.id and b.type='2'and b2.id = %s group by sv.sex",
              'get_circle_info':"select count(distinct sv.id),b2.name from tb_school_agg sv, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_bhierarchy bhier where sv.bid = b2.id and b2.parent = b1.id and b1.parent = b.id and b2.hid=bhier.id and b.type='2' and b2.id = %s group by b2.name",
              'get_school_gender':"select sv.name, sv.sex, sum(sv.num) from tb_school_agg sv where sv.id = %s group by sv.name, sv.sex",
              'get_school_mt':"select sv.name, sv.mt, sum(sv.num) from tb_school_agg sv where sv.id = %s group by sv.name, sv.mt",
              'get_school_boundary_info':"select b.name, b1.name, b2.name, s.name,b.type from tb_boundary b, tb_boundary b1, tb_boundary b2, tb_school s,tb_bhierarchy h where s.id = %s and b.id=b1.parent and b1.id=b2.parent and s.bid=b2.id and b.hid=h.id",
              'get_num_stories':"select count(*) from tb_sys_data where schoolid= %s",
              'get_sys_qids':"select id, qfield from tb_sys_questions order by id",
              'get_sys_qtext':"select id, qtext from tb_sys_questions order by id",
              'get_sys_school_questions':"select * from tb_sys_displayq where hiertype=1 order by id",
              'get_sys_preschool_questions':"select * from tb_sys_displayq where hiertype=2 order by id",
              'get_programme_info':"select p.name,p.start,partner.name from tb_programme p,tb_partner partner where p.partnerid=partner.id and p.id =%s",
              'get_assessmentinfo_school':"select distinct p.name,p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_school_assessment_agg agg, tb_partner pn where agg.sid =%s  and ass.id = agg.assid and p.id = ass.pid and p.partnerid=pn.id",
              'get_assessmentinfo_preschool':"select distinct p.name,p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_preschool_assessment_agg agg, tb_partner pn where agg.sid =%s  and ass.id = agg.assid and p.id = ass.pid and p.partnerid=pn.id",
              'get_district_assessmentinfo':"select distinct p.name, p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_school_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2, tb_school s,tb_bhierarchy hier, tb_partner pn where b.id=%s and b1.parent = b.id and b2.parent=b1.id and b.hid=hier.id and b.type=1 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid and p.partnerid=pn.id",
              'get_block_assessmentinfo':"select distinct p.name, p.start,p.id ,pn.name from tb_programme p, tb_assessment ass, tb_school_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier, tb_partner pn where b.id = b1.parent and b1.id=b2.parent and b.hid=hier.id and b.type=1 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid and b1.id=%s  and p.partnerid=pn.id",
              'get_cluster_assessmentinfo':"select distinct p.name, p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_school_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier, tb_partner pn where b.id = b1.parent and b1.id=b2.parent and b.hid=hier.id and b.type=1 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid and b2.id=%s  and p.partnerid=pn.id",
              'get_preschooldistrict_assessmentinfo':"select distinct p.name, p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_preschool_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2, tb_school s,tb_bhierarchy hier, tb_partner pn where b.id=%s and b1.parent = b.id and b2.parent=b1.id and b.hid=hier.id and b.type=2 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid  and p.partnerid=pn.id",
              'get_project_assessmentinfo':"select distinct p.name, p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_preschool_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier, tb_partner pn where b.id = b1.parent and b1.id=b2.parent and b.hid=hier.id and b.type=2 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid and b1.id=%s  and p.partnerid=pn.id",
              'get_circle_assessmentinfo':"select distinct p.name, p.start,p.id,pn.name from tb_programme p, tb_assessment ass, tb_preschool_assessment_agg agg, tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s,tb_bhierarchy hier, tb_partner pn where b.id = b1.parent and b1.id=b2.parent and b.hid=hier.id and b.type=2 and s.bid=b2.id and agg.sid = s.id and ass.id = agg.assid and p.id = ass.pid and b2.id=%s and p.partnerid=pn.id",
              'get_basic_assessmentinfo_school':"select info.assid,cl.name,info.sex,s.name, sum(info.num),b.id,b1.id,b2.id from tb_class cl, tb_school_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=%s and s.id=info.sid and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and info.clid=cl.id group by info.sex,s.name,b.id,b1.id,b2.id, info.assid,cl.name",
              'get_basic_assessmentinfo_district':"select info.assid,cl.name,info.sex,b.name, sum(info.num) from tb_class cl, tb_school_basic_assessment_info info ,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b.id=%s and info.clid=cl.id group by info.sex,b.name,info.assid,cl.name",
              'get_basic_assessmentinfo_block':"select info.assid,cl.name,info.sex,b1.name, sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b1.id=%s and info.clid=cl.id group by info.sex,b1.name,info.assid,cl.name",
              'get_basic_assessmentinfo_cluster':"select info.assid,cl.name,info.sex,b2.name, sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b2.id=%s and info.clid=cl.id group by info.sex,b2.name,info.assid,cl.name",
              'get_basic_assessmentinfo_preschool':"select info.assid,info.agegroup,info.sex,s.name, sum(info.num),b2.id,b1.id,b.id from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=%s and s.id=info.sid and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id  group by info.sex,s.name,b.id,b1.id,b2.id, info.assid,info.agegroup",
              'get_basic_assessmentinfo_preschooldistrict':"select info.assid,info.agegroup,info.sex,b2.name, sum(info.num) from tb_preschool_basic_assessment_info info ,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by info.sex,b2.name,info.assid,info.agegroup",
              'get_basic_assessmentinfo_project':"select info.assid,info.agegroup,info.sex,b1.name, sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by info.sex,b1.name,info.assid,info.agegroup",
              'get_basic_assessmentinfo_circle':"select info.assid,info.agegroup,info.sex,b.name, sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_school s,tb_boundary b,tb_boundary b1, tb_boundary b2 where ass.pid=%s and info.assid=ass.id and info.sid=s.id  and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by info.sex,b.name,info.assid,info.agegroup",
              'get_assessmentpertext_school':"select agg.assid,cl.name,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s and agg.clid=cl.id group by agg.aggtext,agg.assid,cl.name",
              'get_assessmentpertext_district':"select agg.assid,cl.name,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b.id=%s and agg.clid=cl.id group by cl.name,agg.aggtext,agg.assid",
              'get_assessmentpertext_block':"select agg.assid,cl.name,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b1.id=%s and agg.clid=cl.id group by agg.aggtext,agg.assid,cl.name",
              'get_assessmentpertext_cluster':"select agg.assid,cl.name,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b2.id=%s and agg.clid=cl.id group by agg.aggtext,agg.assid,cl.name",
              'get_assessmentpertext_preschool':"select agg.assid,agg.agegroup,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s group by agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentpertext_preschooldistrict':"select agg.assid,agg.agegroup,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by agg.agegroup,agg.aggtext,agg.assid",
              'get_assessmentpertext_project':"select agg.assid,agg.agegroup,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentpertext_circle':"select agg.assid,agg.agegroup,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentgender_school':"select agg.assid,cl.name,agg.sex,agg.aggtext, sum(agg.aggval) from tb_class cl, tb_school_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s and cl.id=agg.clid group by agg.sex,agg.aggtext,agg.assid,cl.name",
              'get_assessmentgender_district':"select agg.assid,cl.name,agg.sex,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b.id=%s and cl.id=agg.clid group by agg.sex,agg.aggtext,agg.assid,cl.name",
              'get_assessmentgender_block':"select agg.assid,cl.name,agg.sex,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b1.id=%s and cl.id=agg.clid group by agg.sex,agg.aggtext,agg.assid,cl.name",
              'get_assessmentgender_cluster':"select agg.assid,cl.name,agg.sex,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b2.id=%s and cl.id=agg.clid group by agg.sex,agg.aggtext,agg.assid,cl.name",
              'get_assessmentgender_preschool':"select agg.assid,agg.agegroup,agg.sex,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s group by agg.sex,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentgender_preschooldistrict':"select agg.assid,agg.agegroup,agg.sex,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by agg.sex,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentgender_project':"select agg.assid,agg.agegroup,agg.sex,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by agg.sex,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentgender_circle':"select agg.assid,agg.agegroup,agg.sex,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by agg.sex,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentmt_count_school':"select info.assid,cl.name,info.mt,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass where ass.pid=%s and info.assid=ass.id and info.sid=%s and cl.id=info.clid group by info.mt,info.assid,cl.name",
              'get_assessmentmt_count_district':"select info.assid,cl.name,info.mt,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b.id=%s and cl.id=info.clid group by info.mt,info.assid,cl.name",
              'get_assessmentmt_count_block':"select info.assid,cl.name,info.mt,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b1.id=%s and cl.id=info.clid group by info.mt,info.assid,cl.name",
              'get_assessmentmt_count_cluster':"select info.assid,cl.name,info.mt,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b2.id=%s and cl.id=info.clid group by info.mt,info.assid,cl.name",
              'get_assessmentmt_count_preschool':"select info.assid,info.agegroup,info.mt,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass where ass.pid=%s and info.assid=ass.id and info.sid=%s group by info.mt,info.assid,info.agegroup",
              'get_assessmentmt_count_preschooldistrict':"select info.assid,info.agegroup,info.mt,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by info.mt,info.assid,info.agegroup",
              'get_assessmentmt_count_project':"select info.assid,info.agegroup,info.mt,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by info.mt,info.assid,info.agegroup",
              'get_assessmentmt_count_circle':"select info.assid,info.agegroup,info.mt,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by info.mt,info.assid,info.agegroup",
              'get_assessmentmt_school':"select agg.assid,cl.name,agg.mt,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s and cl.id=agg.clid group by agg.mt,agg.aggtext,agg.assid,cl.name",
              'get_assessmentmt_district':"select agg.assid,cl.name,agg.mt,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b.id=%s and cl.id=agg.clid group by agg.mt,agg.aggtext,agg.assid,cl.name",
              'get_assessmentmt_block':"select agg.assid,cl.name,agg.mt,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b1.id=%s and cl.id=agg.clid group by agg.mt,agg.aggtext,agg.assid,cl.name",
              'get_assessmentmt_cluster':"select agg.assid,cl.name,agg.mt,agg.aggtext, sum(agg.aggval) from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and b.id=b1.parent and b1.id=b2.parent and b2.id=s.bid and b2.id=%s and cl.id=agg.clid group by agg.mt,agg.aggtext,agg.assid,cl.name",
              'get_assessmentmt_preschool':"select agg.assid,agg.agegroup,agg.mt,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass where ass.pid=%s and agg.assid=ass.id and agg.sid=%s group by agg.mt,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentmt_preschooldistrict':"select agg.assid,agg.agegroup,agg.mt,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by agg.mt,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentmt_project':"select agg.assid,agg.agegroup,agg.mt,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by agg.mt,agg.aggtext,agg.assid,agg.agegroup",
              'get_assessmentmt_circle':"select agg.assid,agg.agegroup,agg.mt,agg.aggtext, sum(agg.aggval) from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by agg.mt,agg.aggtext,agg.assid,agg.agegroup",
              'get_progress_count_school':"select info.assid,cl.name,ass.name,sum(info.num),ass.start from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass where ass.pid=%s and info.assid=ass.id and info.sid=%s and cl.id=info.clid group by ass.name,ass.start,info.assid,cl.name order by ass.start,cl.name",
              'get_progress_count_district':"select info.assid,cl.name,ass.name,  sum(info.num),ass.start from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b2.id and b2.parent=b1.id and b1.parent=b.id and b.id=%s and cl.id=info.clid group by ass.name,ass.start,info.assid,cl.name  order by ass.start,cl.name",
              'get_progress_count_block':"select info.assid,cl.name,ass.name,  sum(info.num),ass.start from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b2.id and b2.parent=b1.id and b1.parent=b.id and b1.id=%s and cl.id=info.clid group by ass.name,ass.start,info.assid,cl.name order by ass.start,cl.name",
              'get_progress_count_cluster':"select info.assid,cl.name,ass.name,  sum(info.num),ass.start from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b2.id and b2.parent=b1.id and b1.parent=b.id and b2.id=%s and cl.id=info.clid group by ass.name,ass.start,info.assid,cl.name  order by ass.start,cl.name",
              'get_progress_count_preschool':"select info.assid,info.agegroup,ass.name,sum(info.num),ass.start from tb_preschool_basic_assessment_info info,tb_assessment ass where ass.pid=%s and info.assid=ass.id and info.sid=%s group by ass.name,ass.start,info.assid,info.agegroup order by ass.start,info.agegroup",
              'get_progress_count_preschooldistrict':"select info.assid,info.agegroup,ass.name,  sum(info.num),ass.start from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by ass.name,ass.start,info.assid,info.agegroup  order by ass.start,info.agegroup",
              'get_progress_count_project':"select info.assid,info.agegroup,ass.name,  sum(info.num),ass.start from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by ass.name,ass.start,info.assid,info.agegroup order by ass.start,info.agegroup",
              'get_progress_count_circle':"select info.assid,info.agegroup,ass.name,  sum(info.num),ass.start from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b,tb_boundary b1,tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by ass.name,ass.start,info.assid,info.agegroup  order by ass.start,info.agegroup",
              'get_progress_school':"select agg.assid,s.name,cl.name,agg.aggtext,ass.name,  sum(agg.aggval),ass.start from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=%s and s.id = agg.sid and cl.id=agg.clid group by s.name,agg.aggtext,ass.name,ass.start,agg.assid,cl.name  order by ass.start,cl.name",
              'get_progress_district':"select agg.assid,b.name,cl.name,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and agg.sid=s.id and b.id = %s and cl.id=agg.clid group by b.name,agg.aggtext,ass.name,ass.start,agg.assid,cl.name  order by ass.start,cl.name",
              'get_progress_block':"select agg.assid,b1.name,cl.name,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and agg.sid=s.id and b1.id = %s and cl.id=agg.clid group by b1.name,agg.aggtext,ass.name,ass.start,agg.assid,cl.name  order by ass.start,cl.name",
              'get_progress_cluster':"select agg.assid,b2.name,cl.name,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_class cl,tb_school_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and agg.sid=s.id and b2.id = %s and cl.id=agg.clid group by b2.name,agg.aggtext,ass.name,ass.start,agg.assid,cl.name  order by ass.start,cl.name",
              'get_progress_preschool':"select agg.assid,s.name,agg.agegroup,agg.aggtext,ass.name,  sum(agg.aggval),ass.start from tb_preschool_assessment_agg agg,tb_assessment ass,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=%s and s.id = agg.sid group by s.name,agg.aggtext,ass.name,ass.start,agg.assid,agg.agegroup  order by ass.start,agg.agegroup",
              'get_progress_preschooldistrict':"select agg.assid,b2.name,agg.agegroup,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by b2.name,agg.aggtext,ass.name,ass.start,agg.assid,agg.agegroup  order by ass.start,agg.agegroup",
              'get_progress_project':"select agg.assid,b1.name,agg.agegroup,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by b1.name,agg.aggtext,ass.name,ass.start,agg.assid,agg.agegroup  order by ass.start,agg.agegroup",
              'get_progress_circle':"select agg.assid,b.name,agg.agegroup,agg.aggtext,ass.name,   sum(agg.aggval),ass.start from tb_preschool_assessment_agg agg,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and agg.assid=ass.id and agg.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by b.name,agg.aggtext,ass.name,ass.start,agg.assid,agg.agegroup  order by ass.start,agg.agegroup",
              'get_assessmentinfo_district':"select b.name,cl.name,ass.name,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and info.sid=s.id and b.id = %s and cl.id=info.clid group by b.name,cl.name,ass.name",
              'get_assessmentinfo_block':"select b1.name,cl.name,ass.name,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and info.sid=s.id and b1.id = %s and cl.id=info.clid group by b1.name,cl.name,ass.name",
              'get_assessmentinfo_cluster':"select b2.name,cl.name,ass.name,sum(info.num) from tb_class cl,tb_school_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and b.id=b1.parent and b1.id = b2.parent and s.bid = b2.id and info.sid=s.id and b2.id = %s and cl.id=info.clid group by b2.name,cl.name,ass.name",
              'get_assessmentinfo_preschooldistrict':"select b2.name,info.agegroup,ass.name,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b2.id=%s group by b2.name,info.agegroup,ass.name",
              'get_assessmentinfo_project':"select b1.name,info.agegroup,ass.name,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b1.id=%s group by b1.name,info.agegroup,ass.name",
              'get_assessmentinfo_circle':"select b.name,info.agegroup,ass.name,sum(info.num) from tb_preschool_basic_assessment_info info,tb_assessment ass,tb_boundary b, tb_boundary b1, tb_boundary b2,tb_school s where ass.pid=%s and info.assid=ass.id and info.sid=s.id and s.bid=b.id and b.parent=b1.id and b1.parent=b2.id and b.id=%s group by b.name,info.agegroup,ass.name",
              'get_school_info':"select b.name, b1.name, b2.name, s.name,b.type,s.cat,s.sex,s.moi,s.mgmt,s.dise_code,s.status from tb_boundary b, tb_boundary b1, tb_boundary b2, tb_school s,tb_bhierarchy h where s.id = %s and b.id=b1.parent and b1.id=b2.parent and s.bid=b2.id and b.hid=h.id",
              'get_school_address_info':"select a.address,a.area,a.pincode,a.landmark,a.instidentification,a.instidentification2, a.bus from tb_address a,tb_school s where s.aid=a.id and s.id=%s",
              'get_sys_info':"select sys.dateofvisit,sys.comments,sys.id from tb_sys_data sys where sys.schoolid=%s",
              'get_sys_qans':"select q.qtext,a.answer from tb_sys_questions q, tb_sys_qans a where a.qid = q.id and a.sysid in %s",
              'get_school_point':"select ST_AsText(inst.coord) from vw_inst_coord inst where inst.instid=%s",
              'get_sys_nums':"select count(*) from tb_sys_data",
              'get_sys_image_nums':"select count(*) from tb_sys_images",
              'get_school_images':"select hash_file from tb_sys_images where schoolid=%s and verified='Y'",
              'get_school_mpmla':"select mla.const_ward_name, mp.const_ward_name,mla.current_elected_rep, mla.current_elected_party, mp.current_elected_rep, mp.current_elected_party from vw_school_electedrep se, vw_electedrep_master mla, vw_electedrep_master mp where se.sid=%s and mla.id=se.mla_const_id and mp.id= se.mp_const_id;",
}
render = web.template.render('templates/', base='base')
render_plain = web.template.render('templates/')

application = web.application(urls,globals()).wsgifunc()


class mainmap:
  """Returns the main template"""
  def GET(self):
    web.header('Content-Type','text/html; charset=utf-8')
    return render.llp()

class getPointInfo:
  def GET(self):
    pointInfo={"district":[],"block":[],"cluster":[],"school":[]}
    try:
      for type in pointInfo:
        cursor.execute(statements['get_'+type])
        result = cursor.fetchall()
        for row in result:
          try:
            match = re.match(r"POINT\((.*)\s(.*)\)",row[1])
          except:
            traceback.print_exc(file=sys.stderr)
            continue
          lon = match.group(1)
          lat = match.group(2)
          data={"lon":lon,"lat":lat,"name":row[2],"id":row[0]}
          pointInfo[type].append(data)
        connection.commit()

      pointInfo["village"]=[]
      cursor.execute(statements['get_village'])
      result = cursor.fetchall()
      for row in result:
        data={"lon":'',"lat":'',"name":row[0],"id":0}
        pointInfo["village"].append(data)
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(pointInfo)


class visualization:
  def GET(self):
    web.header('Content-Type','text/html; charset=utf-8')
    return render.visualization()



class getSYSInfo:
  def GET(self):
    sysinfo={"numstories":0,"numimages":0}
    try:
      syscursor.execute(statements['get_sys_nums'])
      result = syscursor.fetchall()
      for row in result:
        sysinfo["numstories"]=int(row[0])
      syscursor.execute(statements['get_sys_image_nums'])
      result = syscursor.fetchall()
      for row in result:
        sysinfo["numimages"]=int(row[0])
      sysconnection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(sysinfo)

    

class assessments:
  def GET(self,type,pid,id):
    data={}
    try:
       stype=""
       if pid in preschoolPids:
         stype="preschool"
       assess = assessmentData(type,pid,id,stype)
       data = assess.getData()
       connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type','text/html; charset=utf-8')
    return render_plain.chart(data)


class baseAssessment:
    def __init__(self,type,programmeid,id,stype):
      self.districtid=0
      self.blockid=0
      self.clusterid=0
      self.total={}
      self.count={}
      self.type = str(type)
      self.pid=programmeid
      self.id = id
      self.stype=stype
      self.data= {"programme":{"pid":int(self.pid),"name":"","year":"","partner":""},"type":self.type,"name":"","Boys":0,"Girls":0,"assessPerText":{},"baseline":{"gender":{},"mt":{},"class":{}},"progress":{},"analytics":{},"base":{}}

    def getProgramInfo(self):
      try:
        cursor.execute(statements['get_programme_info'],(self.pid,))
        result = cursor.fetchall()
        for row in result:
          self.data["programme"]["name"]=row[0]
          self.data["programme"]["year"]=str(row[1]).split("-")[0]
          self.data["programme"]["partner"]=row[2]
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getBasicAssessmentInfo(self):
      try:
        qtype=self.type
        query='get_basic_assessmentinfo_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          self.data["name"]=row[3].capitalize()
          if row[0] not in baseassess[self.pid]:
            continue
          classname=str(row[1]).strip()
          if classname not in self.data["base"]:
            self.data["base"][classname]={"Boys":0,"Girls":0}
          if row[2] == "female":
            gender="Girls"
          else:
            gender="Boys"
          if gender not in self.data["base"][classname]:
            self.data["base"][classname][gender]=int(row[4])
          else:
            self.data["base"][classname][gender]=self.data["base"][classname][gender]+int(row[4])

          if classname not in self.total:
            self.total[classname] = row[4]
          else:
            self.total[classname] =self.total[classname]+ row[4]

          if classname not in self.count:
            self.count[classname]={"Boys":0,"Girls":0}
          if gender not in self.count[classname]:
            self.count[classname][gender]=row[4]
          else:
            self.count[classname][gender]=self.count[classname][gender]+row[4]

          if qtype=='school' or qtype=='preschool':
            self.districtid=row[5]
            self.blockid=row[6]
            self.clusterid=row[7]


        for classname in self.data["base"]:
          for gender in self.data["base"][classname]:
            self.data[gender]=self.data[gender]+self.data["base"][classname][gender]
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getBaselineGeneral(self):
      try:
        qtype=self.type
        query='get_assessmentpertext_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          if row[0] not in baseassess[self.pid]:
            continue
          classname=str(row[1]).strip()
          if classname not in self.data["assessPerText"]:
             self.data["assessPerText"][classname]={}

          asstext=row[2]
          assval=row[3]
          if asstext not in self.data["assessPerText"][classname]:
            self.data["assessPerText"][classname][asstext]=assval
          else:
            self.data["assessPerText"][classname][asstext]=self.data["assessPerText"][classname][asstext]+assval

        for classname in  self.data["assessPerText"]:
          for asstext in self.data["assessPerText"][classname]:
               self.data["assessPerText"][classname][asstext]=round((float(self.data["assessPerText"][classname][asstext])/float(self.total[classname]))*100.0,2)
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getBaselineGender(self):
      try:
        qtype=self.type
        query='get_assessmentgender_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          if row[0] not in baseassess[self.pid]:
           continue
          classname=str(row[1]).strip()
          if row[2] =="female":
            gender="Girls"
          if row[2] =="male":
            gender="Boys"

          aggtext=row[3]
          aggval=row[4]
          if classname not in self.data["baseline"]["gender"]:
             self.data["baseline"]["gender"][classname]={}
          if gender not in self.data["baseline"]["gender"][classname]:
            self.data["baseline"]["gender"][classname][gender]={}
          if aggtext not in self.data["baseline"]["gender"][classname][gender]:
            self.data["baseline"]["gender"][classname][gender][aggtext]=aggval
          else:
              self.data["baseline"]["gender"][classname][gender][aggtext]=float(self.data["baseline"]["gender"][classname][gender][aggtext])+float(aggval)



        for classname in self.data["baseline"]["gender"]:
          for gender in self.data["baseline"]["gender"][classname]:
            for asstext in self.data["baseline"]["gender"][classname][gender]:
                self.data["baseline"]["gender"][classname][gender][asstext]=round((float(self.data["baseline"]["gender"][classname][gender][asstext])/float(self.count[classname][gender]))*100.0,2)
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getBaselineMTCount(self,type):
      try:
        type=self.type
        query='get_assessmentmt_count_'+type
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          if row[0] not in baseassess[self.pid]:
            continue
          classname=str(row[1]).strip()
          mt=row[2].capitalize()
          count=row[3]
          if classname not in self.count:
            self.count[classname]={}
          if mt not in self.count[classname]:
            self.count[classname][mt]=count
          else:
            self.count[classname][mt]=self.count[classname][mt]+count
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getBaselineMT(self,type=""):
      try:
        qtype=self.type
        self.getBaselineMTCount(qtype)
        query='get_assessmentmt_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          if row[0] not in baseassess[self.pid]:
            continue
          classname=str(row[1]).strip()
          mt=row[2].capitalize()
          aggtext=row[3]
          count=row[4]
          if classname not in self.data["baseline"]["mt"]:
            self.data["baseline"]["mt"][classname]={}
          if mt not in self.data["baseline"]["mt"][classname]:
            self.data["baseline"]["mt"][classname][mt]={}
          if aggtext not in self.data["baseline"]["mt"][classname][mt]:
            self.data["baseline"]["mt"][classname][mt][aggtext]=count
          else:
            self.data["baseline"]["mt"][classname][mt][aggtext]=self.data["baseline"]["mt"][classname][mt][aggtext]+count

        for classname in self.data["baseline"]["mt"]:
          for mt in self.data["baseline"]["mt"][classname]:
            for asstext in self.data["baseline"]["mt"][classname][mt]:
                self.data["baseline"]["mt"][classname][mt][asstext]=round((float(self.data["baseline"]["mt"][classname][mt][asstext])/float(self.count[classname][mt]))*100.0,2)
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getProgressCount(self,qtype):
      try:
        qtype=self.type
        query='get_progress_count_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          classname=str(row[1]).strip()
          assname=row[2]
          count=row[3]
          if classname not in self.count:
            self.count[classname]={}
          self.count[classname][assname]=count
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getProgressInfo(self,type=""):
      try:
        qtype=self.type
        self.getProgressCount(qtype)
        query='get_progress_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          classname=str(row[2]).strip()
          aggtext=row[3]
          assname=row[4]
          sum=row[5]
          starttime=str(row[6])

          if classname not in self.data["progress"]:
            self.data["progress"][classname]={}
          if starttime not in self.data["progress"][classname]:
            self.data["progress"][classname][starttime]={}
          if assname not in self.data["progress"][classname][starttime]:
            self.data["progress"][classname][starttime][assname]={}
          if aggtext not in self.data["progress"][classname][starttime][assname]:
            self.data["progress"][classname][starttime][assname][aggtext]=sum
          else:
            self.data["progress"][classname][starttime][assname][aggtext]=self.data["progress"][classname][starttime][assname][aggtext]+sum


        for classname in self.data["progress"]:
          for starttime in self.data["progress"][classname]:
            for assname in self.data["progress"][classname][starttime]:
              for aggtext in self.data["progress"][classname][starttime][assname]:
                  self.data["progress"][classname][starttime][assname][aggtext]=round((float(self.data["progress"][classname][starttime][assname][aggtext])/float(self.count[classname][assname]))*100.0,2)
        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()

    def getAnalyticsInfo(self):
      name=self.data["name"].capitalize()+" (School)"
      try:
        qtype=self.type
        query='get_progress_'+qtype
        cursor.execute(statements[query],(self.pid,self.id,))
        result = cursor.fetchall()
        for row in result:
          sname=row[1].capitalize()
          classname=str(row[2]).strip()
          aggtext=row[3]
          assname=row[4]
          aggsum=row[5]
          starttime=str(row[6])

          if classname not in self.data["analytics"]:
            self.data["analytics"][classname]={}
          if starttime not in self.data["analytics"][classname]:
            self.data["analytics"][classname][starttime]={}
          if assname not in self.data["analytics"][classname][starttime]:
            self.data["analytics"][classname][starttime][assname]={}
          if "School" not in self.data["analytics"][classname][starttime][assname]:
            self.data["analytics"][classname][starttime][assname]["School"]={"name":sname}
          if aggtext not in self.data["analytics"][classname][starttime][assname]["School"]:
            self.data["analytics"][classname][starttime][assname]["School"][aggtext]=aggsum
          else:
            self.data["analytics"][classname][starttime][assname]["School"][aggtext]=self.data["analytics"][classname][starttime][assname]["School"][aggtext]+float(aggsum)


        for classname in self.data["analytics"]:
          for starttime in self.data["analytics"][classname]:
            for assname in self.data["analytics"][classname][starttime]:
              for aggtext in self.data["analytics"][classname][starttime][assname]["School"]:
                if aggtext=="name":
                  continue
                self.data["analytics"][classname][starttime][assname]["School"][aggtext]=round((float(self.data["analytics"][classname][starttime][assname]["School"][aggtext])/float(self.count[classname][assname]))*100.0,2)
 

        schoolboundaries={"district":self.districtid,"block":self.blockid,"cluster":self.clusterid}
        preschoolboundaries={"preschooldistrict":self.districtid,"project":self.blockid,"circle":self.clusterid}

        boundaries=schoolboundaries
        if self.type=="preschool":
          boundaries=preschoolboundaries

        for boundary in boundaries:
          boundarytotal={}
          btype=boundary
          query='get_assessmentinfo_'+btype
          cursor.execute(statements[query],(self.pid,boundaries[boundary],))
          result = cursor.fetchall()
          bname=""
          for row in result:
            classname=str(row[1]).strip()
            assname=row[2]
            classsum=row[3]
            if classname not in boundarytotal:
              boundarytotal[classname]={}
            boundarytotal[classname][assname]=classsum


        for boundary in boundaries:
          btype=boundary
          query='get_progress_'+btype
          cursor.execute(statements[query],(self.pid,boundaries[boundary],))
          result = cursor.fetchall()
          for row in result:
            boundary=boundary.capitalize()
            bname=row[1].capitalize()
            classname=str(row[2]).strip()
            aggtext=row[3]
            assname=row[4]
            aggsum=row[5]
            starttime=str(row[6])
            if classname not in self.data["analytics"]:
              continue
            if starttime not in self.data["analytics"][classname]:
              continue
            if assname not in self.data["analytics"][classname][starttime]:
              continue
            if boundary not in self.data["analytics"][classname][starttime][assname]:
              self.data["analytics"][classname][starttime][assname][boundary]={"name":bname}
            if aggtext not in self.data["analytics"][classname][starttime][assname][boundary]:
              if aggsum==0:
                self.data["analytics"][classname][starttime][assname][boundary][aggtext]=round(float(aggsum),2)
              else:
                self.data["analytics"][classname][starttime][assname][boundary][aggtext]=round((float(aggsum)/float(boundarytotal[classname][assname]))*100,2)

        connection.commit()
      except:
        traceback.print_exc(file=sys.stderr)
        connection.rollback()


class assessmentData(baseAssessment):
    def getBaselineAssessmentInfo(self):
      self.getBaselineGeneral()
      self.getBaselineGender()
      self.getBaselineMT()

    def getData(self):
      self.getProgramInfo()
      self.getBasicAssessmentInfo()
      self.getBaselineAssessmentInfo()
      self.getProgressInfo()
      if self.type =="school" or self.type=="preschool":
        self.getAnalyticsInfo()
      connection.commit()
      return self.data


class schoolpage:
  def GET(self,type,id):
    data={'name':'','type':'','id':'','sysdate':[]}
    data["type"]=str(type)
    data["id"]=int(id)
    try:
      cursor.execute(statements['get_school_info'],(id,))
      result = cursor.fetchall()
      for row in result:
        data["b"]=row[0].capitalize()
        data["b1"]=row[1].capitalize()
        data["b2"]=row[2].capitalize()
        data["name"]=row[3].capitalize()
        data["type"]=self.checkEmpty(row[4],'-')
        data["cat"]=self.checkEmpty(row[5],'-')
        data["sex"]=self.checkEmpty(row[6],'-')
        data["moi"]=self.checkEmpty(row[7],'Kannada')
        data["mgmt"]=self.checkEmpty(row[8],'-')
        data["dise_code"]=self.checkEmpty(row[9],'-')
        data["status"]=row[10]
      connection.commit()

      cursor.execute(statements['get_school_address_info'],(id,))
      result = cursor.fetchall()
      data["address"]='-'
      for row in result:
        data["address"]=self.checkEmpty(row[0],'-')
        data["area"]=self.checkEmpty(row[1],'-')
        data["postcode"]=self.checkEmpty(row[2],'-')
        data["landmark_1"]=self.checkEmpty(row[3],'-')
        data["inst_id_1"]=self.checkEmpty(row[4],'-')
        data["inst_id_2"]=self.checkEmpty(row[5],'-')
        data["bus_no"]=self.checkEmpty(row[6],'-')
      connection.commit()

      """cursor.execute(statements['get_school_mpmla'],(id,))
      result = cursor.fetchall()
      for row in result:
        data["mla"] = self.checkEmpty(row[0],'Not available')
        data["mp"] = self.checkEmpty(row[1],'Not available')
        data["mlaname"] = self.checkEmpty(row[2]+' ('+row[3]+')','Not available')
        data["mpname"] = self.checkEmpty(row[4]+' ('+row[5]+')','Not available')
      connection.commit()
    
      query='get_assessmentinfo_'+type
      cursor.execute(statements[query],(id,))
      result = cursor.fetchall()
      assessments= ""
      first=1
      for row in result:
        if first:
          assessments=assessments+row[0]+"|"+str(row[1]).split("-")[0]+"|"+str(row[2])+"|"+str(row[3])
          first=0
        else:
          assessments=assessments+","+row[0]+"|"+str(row[1]).split("-")[0]+"|"+str(row[2])+"|"+str(row[3])
      data["assessments"]=assessments
      connection.commit()
      """

      #Added to query images from tb_sys_images
      from ConfigParser import SafeConfigParser
      config = SafeConfigParser()
      config.read(os.path.join(os.getcwd(),'config/llpconfig.ini'))
      imgpath = config.get('Pictures','htmlpicpath')
      data["image_dir"] = "/" + imgpath
      syscursor.execute(statements['get_school_images'],(id,))
      result = syscursor.fetchall()
      if len(result)>0:
        data["images"]=[]
      for row in result:
        data["images"].append(row[0])
      sysconnection.commit()

      cursor.execute(statements['get_school_gender'],(id,))
      result = cursor.fetchall()
      for row in result:
        if row[1] == "female":
          data["numGirls"]=int(row[2])
        if row[1] == "male":
          data["numBoys"]=int(row[2])
      if "numGirls" not in data.keys():
        data["numGirls"] = 0
      if "numBoys" not in data.keys():
        data["numBoys"] = 0
      data["numStudents"]= data["numBoys"]+data["numGirls"]
      connection.commit()

      cursor.execute(statements['get_school_mt'],(id,))
      result = cursor.fetchall()
      tabledata = {}
      invertdata = {}
      order_lst = []
      for row in result:
        invertdata[int(row[2])] = str(row[1].strip().title())
      if len(invertdata.keys()) > 0:
        checklist = sorted(invertdata)
        others = 0
        for i in checklist[0:len(checklist)-4]:
          others = others + i
          del invertdata[i]
        invertdata[others] = 'Others'
        tabledata = dict(zip(invertdata.values(),invertdata.keys()))
        if 'Other' in tabledata.keys():
          tabledata['Others'] = tabledata['Others'] + tabledata['Other']
          del tabledata['Other']
      for i in sorted(tabledata,key=tabledata.get,reverse=True):
        order_lst.append(i)
      if len(tabledata.keys()) > 0:
        data["school_mt_tb"] = tabledata
        data["school_mt_ord"] = order_lst
      connection.commit()

      syscursor.execute(statements['get_sys_info'],(id,))
      result = syscursor.fetchall()
      sysdates =  []
      syscomments = []
      sysids = []
      data["syscount"]=0
      for row in result:
        if row[0] != None:
          if row[0].strip().replace('/','-') not in sysdates:
            sysdates.append(row[0].strip().replace('/','-'))
          data["syscount"]=data["syscount"]+1
        if row[1] != None:
          syscomments.append(row[1].strip())
        sysids.append(row[2])
      data["sysdate"] = sysdates
      data["syscomment"] = syscomments
      sysconnection.commit()

      if len(sysids)>0:
        syscursor.execute(statements['get_sys_qans'],[tuple(sysids)])
        result = syscursor.fetchall()
        sysdata = {}
        pos_ans = ["yes","available and functional","available but not functional"]
        for row in result:
          if row[0] in sysdata.keys():
            if row[1].lower() not in pos_ans:
              sysdata[row[0]] = "No or Not known"
          else:
            if row[1].lower() in pos_ans:
              sysdata[row[0]] = "Yes" 
            else:
              sysdata[row[0]] = "No or Not known"
        for (k,v) in sysdata.items():
          data["sysdata"].append(k +'|'+v);
        sysconnection.commit()

      print "before lat long"
      cursor.execute(statements['get_school_point'],(id,))
      result = cursor.fetchall()
      for row in result:
        match = re.match(r"POINT\((.*)\s(.*)\)",row[0])
        data["lon"] = match.group(1)
        data["lat"] = match.group(2)
      connection.commit()
      print data
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
      sysconnection.rollback()
      print >> sys.stderr, data
    web.header('Content-Type','text/html; charset=utf-8')
    return render_plain.schoolpage(data)

  def checkEmpty(self,data,rpldata):
    if data == None:
      return rpldata
    else:
      return str(data).capitalize()

class shareyourstory:
  def GET(self,type):
    questions=[]
    try:
      syscursor.execute(statements['get_sys_'+type+'_questions'])
      result = syscursor.fetchall()
      for row in result:
        questions.append({"id":row[0],"text":row[2],"field":row[3],"type":row[4],"options":row[5]})
      sysconnection.commit()
    except:
      sysconnection.rollback()
      traceback.print_exc(file=sys.stderr)
    web.header('Content-Type','text/html; charset=utf-8')
    return render_plain.shareyourstory(questions)

class text:
  def GET(self, name):
    web.header('Content-Type','text/html; charset=utf-8')
    textlinks = {'library': 'library', 'maths': 'maths', 'preschool': 'preschool', 'reading': 'reading', 'partners': 'partners','aboutus':'aboutus','credits':'credits', 'reports':'reports'}

    try:
      return eval('render.' + textlinks[name] + '()')
    except KeyError:
      return web.badrequest()

class getBoundaryInfo:
  def GET(self,type,id):
    print type
    print id
    boundaryInfo ={}
    boundaryInfo["id"]=id
    boundaryInfo["numBoys"]=0
    boundaryInfo["numGirls"]=0
    boundaryInfo["numSchools"]=0
    boundaryInfo["assessments"]=""

    try:

      cursor.execute(statements['get_'+type+'_assessmentinfo'],(id,))
      result = cursor.fetchall()
      assessments= ""
      first=1
      for row in result:
        if first:
          assessments=assessments+row[0]+"|"+str(row[1]).split("-")[0]+"|"+str(row[2])+"|"+str(row[3])
          first=0
        else:
          assessments=assessments+","+row[0]+"|"+str(row[1]).split("-")[0]+"|"+str(row[2])+"|"+str(row[3])
      boundaryInfo["assessments"]=str(assessments)
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()

    try:
      cursor.execute(statements['get_'+type+'_info'],(id,))
      result = cursor.fetchall()
      for row in result:
        boundaryInfo["numSchools"]=str(row[0])
        boundaryInfo["name"]=str(row[1])
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
   
    try:
      cursor.execute(statements['get_'+type+'_gender'],(id,))
      result = cursor.fetchall()
      for row in result:
        if row[0] == "female":
          boundaryInfo["numGirls"]=row[1]
        if row[0] == "male":
          boundaryInfo["numBoys"]=row[1]
      boundaryInfo["numStudents"]= boundaryInfo["numBoys"]+boundaryInfo["numGirls"]
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(boundaryInfo)

class getSchoolInfo:
  def GET(self,id):
    schoolInfo={}
    schoolInfo["id"]=id
    schoolInfo["numStories"]=0
    schoolInfo["numBoys"]=0
    schoolInfo["numGirls"]=0
    schoolInfo["numStudents"]=0
    encodedschoolInfo=""


    try:
      cursor.execute(statements['get_school_gender'],(id,))
      result = cursor.fetchall()
      for row in result:
        schoolInfo["name"]=row[0]
        if row[1] == "female":
          schoolInfo["numGirls"]=row[2]
        if row[1] == "male":
          schoolInfo["numBoys"]=row[2]

      schoolInfo["numStudents"]= schoolInfo["numBoys"]+schoolInfo["numGirls"]
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    
    try:
      syscursor.execute(statements['get_num_stories'],(id,))
      result = syscursor.fetchall()
      for row in result:
        schoolInfo["numStories"]=row[0]
      sysconnection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()
    web.header('Content-Type', 'application/json; charset=utf-8')
    return jsonpickle.encode(schoolInfo)


class getVillagePoints: 
  def GET(self,name):
    boundaryInfo =[]
    try:
      print name
      cursor.execute(statements['get_village_points'],(name,))
      result = cursor.fetchall()
      for row in result:
        data={"id":row[0],"name":row[1].capitalize()}
        boundaryInfo.append(data)
      connection.commit()
      print boundaryInfo
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(boundaryInfo)
 

class getBoundaryPoints: 
  def GET(self,type,id):
    boundaryInfo =[]
    try:
      cursor.execute(statements['get_'+type+'_points'],(id,))
      result = cursor.fetchall()
      for row in result:
        data={"id":row[0],"name":row[1].capitalize()}
        boundaryInfo.append(data)
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(boundaryInfo)
 
class getSchoolBoundaryInfo:
  def GET(self,id):
    schoolInfo = {"district":"","block":"","cluster":"","schoolname":"","type":""}
    try:
      cursor.execute(statements['get_school_boundary_info'],(id,))
      result = cursor.fetchall()
      for row in result:
        schoolInfo ={"district":row[0].capitalize(),"block":row[1].capitalize(),"cluster":row[2].capitalize(),"schoolname":row[3].capitalize(),"type":row[4]}
      connection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      connection.rollback()
    web.header('Content-Type', 'application/json')
    return jsonpickle.encode(schoolInfo)

class insertSYS:
  def GET(self,query):
    try:
      syscursor.execute(query)
      sysconnection.commit()
    except:
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()


class postSYS:

  def getQuestionDict(self):
    qidsdict = {}
    try:
      syscursor.execute(statements['get_sys_qids'])
      result = syscursor.fetchall()
      for row in result:
        qidsdict[row[1]] = row[0]
      sysconnection.commit()
      return qidsdict
    except:
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()
      return None

  def sendMail(self, recipient, sub, body, file = None):
    #cc = [recipient]
    to = [recipient]
    subject = sub
    from ConfigParser import SafeConfigParser
    config = SafeConfigParser()
    config.read(os.path.join(os.getcwd(),'config/llpconfig.ini'))
    sender = config.get('Mail','senderid')
    smtpport = config.get('Mail','smtpport') 
    smtpserver = config.get('Mail','smtpserver')

    # create html email
    html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
    html +='"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml">'
    html +='<body style="font-size:14px;font-family:Verdana"><p>' + body + '</p>'
    html += "</body></html>"
 
    emailMsg = email.MIMEMultipart.MIMEMultipart('alternative')
    emailMsg['Subject'] = subject
    emailMsg['From'] = sender
    emailMsg['To'] = ', '.join(to)
    #emailMsg['Cc'] = ", ".join(cc)
    emailMsg.attach(email.mime.text.MIMEText(html,'html'))
      
    if file != None: 
      ctype, encoding = mimetypes.guess_type(file)

      if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        fp = open(file)
        fileMsg = email.mime.text.MIMEText(fp.read(), _subtype=subtype)
        fp.close()
        email.encoders.encode_base64(fileMsg)
        fileMsg.add_header('Content-Disposition','attachment;filename='+file.lstrip(filedir))
        emailMsg.attach(fileMsg)

    server = smtplib.SMTP(smtpserver,smtpport)
    server.sendmail(sender,to,emailMsg.as_string())
    server.quit()

  def populateImages(self,selectedfile,schoolid,sysid):
      #Getting path to picture files from the config file
      from ConfigParser import SafeConfigParser
      import hashlib
      config = SafeConfigParser()
      config.read(os.path.join(os.getcwd(),'config/llpconfig.ini'))
      savepath = config.get('Pictures','origpicpath')
      #hashpath = config.get('Pictures','hashpicpath')
      hashed_filename = ''
      if selectedfile.filename != "":
        try:
          if(os.path.exists(savepath+selectedfile.filename)):
            savefilename = selectedfile.filename.split('.')[0] + '-' + schoolid + '.jpg'
          else:
            savefilename = selectedfile.filename
          wf=open(savepath + savefilename,'w')
          wf.write(selectedfile.file.read())
          wf.close()
          hashed_filename = hashlib.md5(open(savepath +savefilename,'r').read()).hexdigest() + '.jpg'
          import shutil
          shutil.move(savepath + savefilename,savepath + hashed_filename)
        except IOError:
          traceback.print_exc(file=sys.stderr)
          print "Error occurred during processing this file: " + savefilename
        imagequery = "insert into tb_sys_images(schoolid,original_file,hash_file,sysid,verified) values( %s , %s, %s, %s, %s)"
        try:
          syscursor.execute(imagequery,(schoolid,savefilename,hashed_filename,sysid,'N')) #Images coming in from this flow are yet to be verified
          sysconnection.commit()
        except:
          traceback.print_exc(file=sys.stderr)
          sysconnection.rollback()

  def POST(self,type):
    success = True
    recipient = None
    try:
      schoolid=0
      if type=="school":
        form = mySchoolform()
        #print >> sys.stderr, "Type is school"
      else:
        form = myPreSchoolform()
        #print >> sys.stderr, "Type is preschool :"+type
      if not form.validates(): 
         for k in form.inputs: 
           return "id = ", k.id
      count=0
      sysid = None
      query="insert into tb_sys_data"
      qansquery = "insert into tb_sys_qans(sysid,qid,answer) values( %(sysid)s,%(qid)s,%(answer)s)"
      data={}
      qdata={}
      qarray=[]
      qiddict = self.getQuestionDict()
      for k in form.inputs: 
        if not(k.id.startswith('file')) and k.value != '' and k.value != None:
          if k.id in ('schoolid','name','email','telephone','dateofvisit','comments'):
            data[k.id] = k.value.strip('\n\r\t')
            if k.id == 'email':
              recipient = k.value 
          else:
            if k.id == 'chkboxes':
              qarray = k.value.split(',')
              for q in qarray:
                iparr = q.split('|')
                qdata[qiddict[iparr[0]]]=iparr[1]
              print >> sys.stderr, str(qdata)

      fields = ', '.join(data.keys())
      values = ', '.join(['%%(%s)s' % x for x in data])
      query=query+"("+fields+") values("+values+")"
      #print >> sys.stderr, str(query)
      #print >> sys.stderr, "Questions:-"+str(qdata)
      #return query+" Data:"+str(data)
      syscursor.execute("BEGIN")
      syscursor.execute("LOCK TABLE tb_sys_data IN ROW EXCLUSIVE MODE");
      syscursor.execute(query,data)
      syscursor.execute("select currval('tb_sys_data_id_seq')")
      result = syscursor.fetchall()
      syscursor.execute("COMMIT")
      for row in result:
        sysid=row[0]
      for q in qdata.keys():
        syscursor.execute(qansquery,{'sysid':sysid,'qid':q,'answer':qdata[q]})
      sysconnection.commit()
    except:
      print >> sys.stderr, str(query)
      print >> sys.stderr, "Questions:-"+str(qdata)
      print >> sys.stderr, "Other:-"+str(data)
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()
      success = False
   
    #add photos
    try:
      schoolid= form['schoolid'].value
      x = web.input(file1={})
      self.populateImages(x.file1,schoolid,sysid)
      x = web.input(file2={})
      self.populateImages(x.file2,schoolid,sysid)
      x = web.input(file3={})
      self.populateImages(x.file3,schoolid,sysid)
      x = web.input(file4={})
      self.populateImages(x.file4,schoolid,sysid)
      x = web.input(file5={})
      self.populateImages(x.file5,schoolid,sysid)
    except:
      traceback.print_exc(file=sys.stderr)
      sysconnection.rollback()
      success = False
 
    if success:
      body = "Thank you for taking the time and sharing your experience. Your inputs have been successfully recorded."
      body = body + "<br/><br/> We appreciate your continued help in ensuring that every"
      body = body + " child is in school and learning well."
      sub = "Thank you for sharing your story on KLP"
    else:
      body = "Thank you for taking the time and sharing your experience.<br/>However, there an error occurred because "
      body = body + "of which you form did not get saved. It would be of great help if you could e-mail dev@klp.org.in "
      body = body + "to notify them of this error immediately, if possible."
      sub = "Error while sharing your story on KLP"
    if recipient != None:
      self.sendMail(recipient, sub, body)
      #pass

    web.header('Content-Type','text/html; charset=utf-8')
    return render_plain.sys_submitted()
   
class listFiles:
  def GET(self,type):
    fileList = {}
    if len(type) > 1:
      reqp = type.split('|')
      type = reqp[0]
      mp = reqp[1]
      mla = reqp[2]
    path = ""
    if (int(type) == 1 or int(type) == 3):
      mpfilenames = []
      mlafilenames = []
      path = "/reports"
      fileList["subdir1"] = "/Kannada"
      fileList["subdir2"] = "/English"
      fileList["directory"] = path
      try:
        dirList=os.listdir(os.getcwd() + path + "/English")
        if int(type) == 3:
          fname = difflib.get_close_matches('mp_' + mp.replace(' ','_').lower(), dirList)
          mpfilenames.append(fname[0])
          fname = difflib.get_close_matches('mla_' + mla.replace(' ','_').lower(), dirList)
          mlafilenames.append(fname[0])
          fileList["listtype"] = '3'
        else:
          for fname in dirList:
            if '.zip' in fname:
              pass
            else:
              if 'MP_' in fname:
                mpfilenames.append(fname)
              else:
                mlafilenames.append(fname)
          fileList["listtype"] = '1'
        fileList["mpnames"] = mpfilenames
        fileList["mlanames"] = mlafilenames
      except:
        traceback.print_exc(file=sys.stderr)
    if (int(type) == 2):
      path = "/rawdata"
      rawfilenames =[]
      try:
        dirList=os.listdir(os.getcwd() + path)
        for fname in dirList:
          rawfilenames.append(fname)
        fileList["directory"] = path
        fileList["rawfiles"] = rawfilenames
        fileList["listtype"] = '2'
      except:
        traceback.print_exc(file=sys.stderr)
      
    web.header('Content-Type','text/html; charset=utf-8')
    return render_plain.listFiles(fileList)

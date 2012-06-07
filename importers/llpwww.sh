#!/bin/sh

DBNAME=$(basename $0 .sh)
OWNER=klp

sudo -u postgres dropdb ${DBNAME}
sudo -u postgres createdb -O ${OWNER} -E UTF8 ${DBNAME}
# Setup dblink
sudo -u postgres psql -d ${DBNAME} -f /usr/share/postgresql/8.4/contrib/dblink.sql


sudo -u postgres createlang plpgsql ${DBNAME}
sudo -u postgres psql -d ${DBNAME} -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql
sudo -u postgres psql -d ${DBNAME} -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql
# Grant privileges
sudo -u postgres psql -d ${DBNAME} -f grants.sql

# Create schema
psql -U ${OWNER} -d ${DBNAME} -f ${DBNAME}.sql

echo "Loading data"
psql -U ${OWNER} -d ${DBNAME} -f load/tb_boundary.sql
psql -U ${OWNER} -d ${DBNAME} -f load/tb_address.sql
psql -U ${OWNER} -d ${DBNAME} -f load/tb_school.sql

echo "Creating aggs"
psql -U ${OWNER} -d ${DBNAME} -f agg.sql
echo "Finished"

#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres --set=kcpass="$KEYCLOAK_DB_PASSWORD" <<'SQL'
CREATE USER keycloak WITH PASSWORD :'kcpass';
CREATE DATABASE keycloak OWNER keycloak;
SQL

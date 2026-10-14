#!/bin/sh
set -eu
cp /config/init-keycloak.sh /docker-entrypoint-initdb.d/init-keycloak.sh
chmod 644 /docker-entrypoint-initdb.d/init-keycloak.sh
mkdir -p /tmp/db-tls
cp /certs/postgres.crt /tmp/db-tls/server.crt
cp /certs/postgres.key /tmp/db-tls/server.key
chown -R postgres:postgres /tmp/db-tls
chmod 600 /tmp/db-tls/server.key
exec docker-entrypoint.sh postgres -c ssl=on -c ssl_cert_file=/tmp/db-tls/server.crt -c ssl_key_file=/tmp/db-tls/server.key

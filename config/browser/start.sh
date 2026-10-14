#!/bin/sh
set -eu
cp /lab-ca/ca.crt /usr/local/share/ca-certificates/sso-lab.crt
update-ca-certificates >/dev/null
for db in /root/.pki/nssdb /root/.local/share/pki/nssdb; do
 mkdir -p "$db"
 test -f "$db/cert9.db" || certutil -N --empty-password -d "sql:$db"
 certutil -A -d "sql:$db" -n sso-lab -t 'C,,' -i /lab-ca/ca.crt
done
touch /tmp/lab-browser-ready
exec sleep infinity

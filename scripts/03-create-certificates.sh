#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
umask 077
mkdir -p secrets/ca secrets/tls
if [ ! -f secrets/ca/ca.crt ]; then
  openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 365 \
    -keyout secrets/ca/ca.key -out secrets/ca/ca.crt \
    -subj '/CN=Kubernetes SSO Local Lab CA' \
    -addext 'basicConstraints=critical,CA:TRUE' \
    -addext 'keyUsage=critical,keyCertSign,cRLSign'
fi
for name in sso rancher postgres; do
  if [ -f "secrets/tls/$name.crt" ]; then continue; fi
  openssl req -new -newkey rsa:2048 -nodes \
    -keyout "secrets/tls/$name.key" -out "secrets/tls/$name.csr" \
    -subj "/CN=$name.lab.test"
  openssl x509 -req -in "secrets/tls/$name.csr" \
    -CA secrets/ca/ca.crt -CAkey secrets/ca/ca.key -CAcreateserial \
    -out "secrets/tls/$name.crt" -days 90 -sha256 \
    -extfile "config/tls/$name.ext"
done
openssl verify -CAfile secrets/ca/ca.crt secrets/tls/sso.crt secrets/tls/rancher.crt

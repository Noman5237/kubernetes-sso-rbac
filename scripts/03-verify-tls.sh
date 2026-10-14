#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for name in sso rancher; do
  curl --fail --silent --show-error --cacert secrets/ca/ca.crt \
    --resolve "$name.lab.test:8443:127.0.0.1" "https://$name.lab.test:8443/__lab_tls_probe"
  set +e
  curl --silent --show-error --resolve "$name.lab.test:8443:127.0.0.1" "https://$name.lab.test:8443/__lab_tls_probe" >/dev/null 2>&1
  rc=$?
  set -e
  test "$rc" = 60
  echo "PASS: host rejects $name certificate without explicit CA (curl 60)."
  for cluster in mngmt cluster-a cluster-b; do
    docker exec "$cluster-control-plane" curl --fail --silent --show-error "https://$name.lab.test:8443/__lab_tls_probe"
  done
done

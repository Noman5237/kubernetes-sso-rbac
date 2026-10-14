#!/bin/sh
set -eu
# Run with administrator privileges. Preserve all existing hosts entries.
if ! /usr/bin/grep -Eq '^127\.0\.0\.1[[:space:]]+sso\.lab\.test[[:space:]]+rancher\.lab\.test([[:space:]]|$)' /etc/hosts; then
  if /usr/bin/grep -Eq '(^|[[:space:]])(sso|rancher)\.lab\.test([[:space:]]|$)' /etc/hosts; then
    echo 'Existing lab hostname entry found; review it instead of adding a duplicate.' >&2
    exit 1
  fi
  /usr/bin/printf '\n# kubernetes-sso-rbac local lab\n127.0.0.1 sso.lab.test rancher.lab.test\n' >> /etc/hosts
fi
/usr/bin/dscacheutil -flushcache
/usr/bin/killall -HUP mDNSResponder
echo 'Lab hostnames configured; no CA trust changes.'

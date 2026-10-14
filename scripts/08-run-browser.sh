#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose -f compose.browser.yaml up -d --build
# CA initialization must finish before Chromium opens.
for attempt in {1..30}; do
 if docker exec sso-lab-browser test -f /tmp/lab-browser-ready; then break; fi
 sleep 1
done
docker exec sso-lab-browser test -f /tmp/lab-browser-ready
docker exec sso-lab-browser node /scripts/08-browser-check.cjs

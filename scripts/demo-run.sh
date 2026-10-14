#!/bin/sh
# Re-recording replaces the existing demo and refreshes Alice's one-hour lab kubeconfigs.
set -eu
cd "$(dirname "$0")/.."
mkdir -p artifacts/demo
python3 scripts/08-generate-kubeconfigs.py
python3 scripts/demo-capture-kubectl.py
python3 scripts/demo-narration.py
docker compose -f compose.demo.yaml up -d
trap 'docker compose -f compose.demo.yaml down' EXIT
for n in $(seq 1 30); do
 if docker exec sso-lab-demo test -f /tmp/lab-browser-ready; then break; fi
 sleep 1
done
docker exec sso-lab-demo test -f /tmp/lab-browser-ready
docker exec sso-lab-demo sh -c 'apt-get update -qq && apt-get install -y --no-install-recommends ffmpeg >/tmp/ffmpeg-install.log && cd /opt/lab-browser && npx playwright install ffmpeg'
docker exec sso-lab-demo node /scripts/demo-prepare.cjs
# Explicitly discard the resume index when starting a new full recording.
rm -f artifacts/demo/recording.json
docker exec sso-lab-demo node /scripts/demo-record.cjs
python3 scripts/demo-render.py

#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p artifacts/gif demo
cp artifacts/step-09/results.json artifacts/gif/evidence.json
cp artifacts/step-10/results.json artifacts/gif/reliability-evidence.json
docker compose -f compose.gif.yaml up -d
trap 'docker compose -f compose.gif.yaml down' EXIT
docker exec sso-lab-gif sh -c 'apt-get update -qq && apt-get install -y --no-install-recommends ffmpeg gifsicle >/tmp/media-install.log'
docker exec sso-lab-gif node /scripts/demo-gif.cjs

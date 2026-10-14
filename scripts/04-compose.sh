#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export LAB_GATEWAY_IP="$(docker inspect sso-lab-gateway --format '{{(index .NetworkSettings.Networks "kind").IPAddress}}')"
exec docker compose --env-file secrets/keycloak/runtime.env -f compose.network.yaml -f compose.keycloak.yaml "$@"

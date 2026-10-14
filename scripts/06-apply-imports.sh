#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# First prepare and review with 06-prepare-imports.py and 06-review-imports.py.
for cluster in cluster-a cluster-b; do
  kubectl --kubeconfig "kubeconfigs/$cluster-admin.yaml" apply -f "secrets/rancher/imports/$cluster.yaml"
done

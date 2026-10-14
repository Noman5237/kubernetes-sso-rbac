#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$LAB_ROOT/config/versions.env"
mkdir -p "$LAB_ROOT/artifacts/preflight"
command -v docker kind helm kubectl
kind version
helm version --short
kubectl version --client
docker info --format 'Server={{.ServerVersion}} OS={{.OSType}} Arch={{.Architecture}} CPUs={{.NCPU}} MemoryBytes={{.MemTotal}}'
docker compose version
helm show chart rancher --repo "$RANCHER_CHART_REPO" --version "$RANCHER_VERSION" > "$LAB_ROOT/artifacts/preflight/rancher-chart.yaml"
helm template rancher rancher --repo "$RANCHER_CHART_REPO" --version "$RANCHER_VERSION" \
  --namespace cattle-system --kube-version "${KUBERNETES_VERSION#v}" \
  --set hostname=rancher.lab.test --set replicas=1 \
  --set ingress.tls.source=secret --set privateCA=true \
  > "$LAB_ROOT/artifacts/preflight/rancher-rendered.yaml"
printf 'PASS: local chart rendering; no Kubernetes resources applied.\n'

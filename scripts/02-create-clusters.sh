#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$LAB_ROOT/config/versions.env"
mkdir -p "$LAB_ROOT/kubeconfigs" "$LAB_ROOT/artifacts/step-02"
chmod 700 "$LAB_ROOT/kubeconfigs"
for cluster in mngmt cluster-a cluster-b; do
  if kind get clusters 2>/dev/null | grep -Fxq "$cluster"; then
    echo "Refusing to overwrite existing cluster: $cluster" >&2
    exit 1
  fi
done
for cluster in mngmt cluster-a cluster-b; do
  kind create cluster --config "$LAB_ROOT/config/kind/$cluster.yaml" \
    --image "$KIND_NODE_IMAGE" --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" --wait 180s
  chmod 600 "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml"
  kubectl --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" wait --for=condition=Ready nodes --all --timeout=180s
  kubectl --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" get --raw=/readyz
  kubectl --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" get nodes -o wide
  if [ "$cluster" != mngmt ]; then
    kubectl --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" create namespace demo
    kubectl --kubeconfig "$LAB_ROOT/kubeconfigs/$cluster-admin.yaml" get pods -n demo
  fi
done

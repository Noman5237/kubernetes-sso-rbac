#!/usr/bin/env bash
set -euo pipefail
LAB_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for cluster in mngmt cluster-a cluster-b; do
  cfg="$LAB_ROOT/kubeconfigs/$cluster-admin.yaml"
  echo "=== $cluster ==="
  kubectl --kubeconfig "$cfg" wait --for=condition=Ready nodes --all --timeout=180s
  kubectl --kubeconfig "$cfg" get --raw=/readyz
  echo
  kubectl --kubeconfig "$cfg" get nodes -o wide
  kubectl --kubeconfig "$cfg" auth can-i '*' '*' --all-namespaces
  kubectl --kubeconfig "$cfg" get pods -A
  test "$(kubectl --kubeconfig "$cfg" get nodes -o name | wc -l | tr -d ' ')" = 1
  if [ "$cluster" != mngmt ]; then
    test -z "$(kubectl --kubeconfig "$cfg" get pods -n demo -o name)"
    echo 'PASS: demo has no pods.'
  fi
done
python3 - <<'PY'
import json,subprocess
info=json.loads(subprocess.check_output(['docker','info','--format','{{json .}}']))
assert info['MemTotal'] > 15*1024**3
print('PASS: Docker usable memory exceeds 15 GiB (16 GiB configured).')
PY

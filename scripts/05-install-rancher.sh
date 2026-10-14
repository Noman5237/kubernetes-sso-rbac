#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source config/versions.env
export KUBECONFIG="$PWD/kubeconfigs/mngmt-admin.yaml"
mkdir -p artifacts/step-05
kubectl create namespace cattle-system --dry-run=client -o yaml | kubectl apply -f -
kubectl -n cattle-system create secret generic tls-ca --from-file=cacerts.pem=secrets/ca/ca.crt --dry-run=client -o yaml | kubectl apply -f -
kubectl -n cattle-system create secret generic tls-ca-additional --from-file=ca-additional.pem=secrets/ca/ca.crt --dry-run=client -o yaml | kubectl apply -f -
# Let the chart generate bootstrap credentials. Never render or print that Secret.
helm upgrade --install rancher rancher --repo "$RANCHER_CHART_REPO" --version "$RANCHER_VERSION" --namespace cattle-system -f config/rancher/values.yaml --wait --timeout 15m
python3 - <<'PY'
import base64,json,os,subprocess
from pathlib import Path
p=Path('secrets/rancher');p.mkdir(exist_ok=True,mode=0o700);p.chmod(0o700)
data=json.loads(subprocess.check_output(['kubectl','-n','cattle-system','get','secret','bootstrap-secret','-o','json']))
f=p/'bootstrap-password'
fd=os.open(f,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
with os.fdopen(fd,'wb') as out: out.write(base64.b64decode(data['data']['bootstrapPassword']))
print('Bootstrap password retained in secrets/rancher/bootstrap-password (not printed).')
PY

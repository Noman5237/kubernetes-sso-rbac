#!/usr/bin/env python3
import json, ssl, subprocess, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
K=['kubectl','--kubeconfig',str(ROOT/'kubeconfigs/mngmt-admin.yaml')]
def obj(*args): return json.loads(subprocess.check_output(K+list(args)+['-o','json']))
ctx=ssl.create_default_context(cafile=str(ROOT/'secrets/ca/ca.crt'))
base='https://rancher.lab.test:8443'
def get(path):
    with urllib.request.urlopen(base+path,context=ctx,timeout=30) as r:
        assert r.status==200
        return r.read()
assert get('/ping').decode().strip()=='pong'
print('PASS: Rancher HTTPS ping through hostname and explicit CA')
get('/dashboard/')
print('PASS: dashboard HTML reachable')
ca=json.loads(get('/v3/settings/cacerts'))['value']
assert ca.strip()==(ROOT/'secrets/ca/ca.crt').read_text().strip()
print('PASS: Rancher publishes the correct agent CA')
d=obj('-n','cattle-system','get','deployment','rancher')
assert d['spec']['replicas']==1 and d['status'].get('availableReplicas')==1
assert obj('get','settings.management.cattle.io','agent-tls-mode')['value']=='strict'
assert obj('get','settings.management.cattle.io','server-url')['value']==base
print('PASS: one available replica, strict agent TLS, correct server URL')
for namespace,name in [('cattle-fleet-system','fleet-controller'),('cattle-fleet-system','gitjob'),('cattle-fleet-system','helmops'),('cattle-system','rancher-webhook')]:
    item=obj('-n',namespace,'get','deployment',name)
    assert item['status'].get('availableReplicas',0)==item['spec']['replicas'], name+' is not ready'
print('PASS: default Fleet controllers and Rancher webhook are available')
subprocess.run(K+['-n','cattle-system','exec','deployment/rancher','--','curl','--fail','--silent','--show-error','--output','/dev/null','https://sso.lab.test:8443/realms/master/.well-known/openid-configuration'],check=True)
print('PASS: Rancher container resolves and trusts Keycloak using its CA store')
for name in ('mngmt','cluster-a','cluster-b'):
    value=subprocess.check_output(['docker','exec',name+'-control-plane','curl','--fail','--silent','--show-error',base+'/ping'],text=True)
    assert value.strip()=='pong'
print('PASS: all three kind nodes resolve and trust Rancher')
try:
    urllib.request.urlopen(base+'/ping',context=ssl.create_default_context(),timeout=10)
except urllib.error.URLError as e:
    assert isinstance(e.reason,ssl.SSLCertVerificationError)
    print('PASS: default host trust rejects lab CA; no host trust installed')
else: raise AssertionError('Expected default trust to reject lab CA')

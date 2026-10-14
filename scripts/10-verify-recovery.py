#!/usr/bin/env python3
"""Verify recovery, temporary-credential cleanup, and host/TLS trust boundaries."""
import base64,hashlib,json,re,socket,ssl,subprocess,urllib.request
from pathlib import Path
from rancher_api import Rancher,ROOT
out=ROOT/'artifacts/step-10'
r=json.loads((out/'results.json').read_text());assert r['testsCompleted'] and r['restored'] and r['testCredentialsRevoked']
def kube(cluster,*args):return subprocess.check_output(['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{cluster}-admin.yaml'),*args],text=True)
checks=[]
for name in ['mngmt','cluster-a','cluster-b']:
 assert kube(name,'auth','can-i','*','*','--all-namespaces').strip()=='yes'
 nodes=json.loads(kube(name,'get','nodes','-o','json'))['items'];assert len(nodes)==1
 assert any(c['type']=='Ready' and c['status']=='True' for c in nodes[0]['status']['conditions'])
 if name!='mngmt':assert not json.loads(kube(name,'get','pods','-n','demo','-o','json'))['items']
 checks.append({'cluster':name,'nativeAdmin':True,'singleNodeReady':True})
d=json.loads(kube('mngmt','-n','cattle-system','get','deployment','rancher','-o','json'))
assert d['spec']['replicas']==1 and d['status'].get('readyReplicas')==1
for container in ['sso-lab-keycloak','sso-lab-postgres','sso-lab-gateway']:
 assert subprocess.check_output(['docker','inspect',container,'--format','{{.State.Running}}'],text=True).strip()=='true'
assert subprocess.check_output(['docker','inspect','sso-lab-postgres','--format','{{.State.Health.Status}}'],text=True).strip()=='healthy'
existing={x['metadata']['name'] for x in json.loads(kube('mngmt','get','tokens.management.cattle.io','-o','json'))['items']}
assert not existing.intersection(r['testSessionIds'])
with Rancher() as admin:
 for item in r['testKubeconfigs']:
  for path in ['/apis/ext.cattle.io/v1/kubeconfigs/'+item['name']]+['/apis/ext.cattle.io/v1/tokens/'+t for t in item['tokens']]:
   try:admin.call(path)
   except RuntimeError as e:assert '404' in str(e)
   else:raise AssertionError('Disposable credential still exists')
trusted=ssl.create_default_context(cafile=str(ROOT/'secrets/ca/ca.crt'))
http_ready={}
for label,url in {'rancherDashboard':'https://rancher.lab.test:8443/dashboard/','keycloakDiscovery':'https://sso.lab.test:8443/realms/kubernetes/.well-known/openid-configuration'}.items():
 with urllib.request.urlopen(url,context=trusted,timeout=10) as response:
  assert response.status==200;http_ready[label]=response.status
with socket.create_connection(('sso.lab.test',8443),timeout=5) as sock:
 with trusted.wrap_socket(sock,server_hostname='sso.lab.test') as secure:tls_version=secure.version()
config=json.loads(kube('mngmt','config','view','--raw','--minify','-o','json'))
wrong=ssl.create_default_context(cadata=base64.b64decode(config['clusters'][0]['cluster']['certificate-authority-data']).decode())
try:
 with socket.create_connection(('sso.lab.test',8443),timeout=5) as sock:
  with wrong.wrap_socket(sock,server_hostname='sso.lab.test'):pass
except ssl.SSLCertVerificationError:pass
else:raise AssertionError('Wrong CA unexpectedly trusted lab endpoint')
public_ca=(ROOT/'secrets/ca/ca.crt').read_text();lab_hash=hashlib.sha256(ssl.PEM_cert_to_DER_cert(public_ca)).hexdigest()
keychains=re.findall(r'"([^\"]+)"',subprocess.check_output(['security','list-keychains','-d','user'],text=True))
keychains+=['/Library/Keychains/System.keychain','/System/Library/Keychains/SystemRootCertificates.keychain']
checked=[]
for path in dict.fromkeys(keychains):
 p=subprocess.run(['security','find-certificate','-a','-c','Kubernetes SSO Local Lab CA','-p',path],capture_output=True,text=True)
 assert p.returncode in (0,44), 'Could not inspect targeted certificate in '+path
 certs=re.findall(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',p.stdout,re.S)
 assert all(hashlib.sha256(ssl.PEM_cert_to_DER_cert(cert)).hexdigest()!=lab_hash for cert in certs)
 checked.append(path)
result={'httpReady':http_ready,'nativeClusters':checks,'rancherReplicas':1,'rancherReady':True,'keycloakAndGatewayRunning':True,'postgresHealthy':True,'testCredentialsDeleted':True,'trustedTLS':tls_version,'wrongCARejected':True,'labCANotInCheckedMacKeychains':checked}
(out/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: services recovered, native admins intact, demo namespaces empty, test credentials revoked')
print('PASS: trusted TLS works, wrong CA fails, lab CA absent from checked Mac keychains')

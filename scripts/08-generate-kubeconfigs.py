#!/usr/bin/env python3
import os,json,subprocess,base64
from rancher_api import Rancher,ROOT,BASE
from oidc_login import authorization_code
api=Rancher();provider=api.call('/v3-public/authProviders/keycloakoidc')
code=authorization_code(api,provider['redirectUrl'],'alice')
api.token=api.call(provider['actions']['login'],{'code':code,'responseType':'json'})['token']
records=[]
try:
 for assignment in json.loads((ROOT/'artifacts/step-07/assignments.json').read_text()):
  name=assignment['cluster'];cid=assignment['clusterId']
  for old in api.call('/apis/ext.cattle.io/v1/kubeconfigs')['items']:
   if old.get('spec',{}).get('description')=='Local POC Alice '+name:
    api.call('/apis/ext.cattle.io/v1/kubeconfigs/'+old['metadata']['name'],method='DELETE')
  result=api.call('/apis/ext.cattle.io/v1/kubeconfigs',{'apiVersion':'ext.cattle.io/v1','kind':'Kubeconfig','spec':{'clusters':[cid],'currentContext':cid,'ttl':3600,'description':'Local POC Alice '+name}})
  path=ROOT/f'kubeconfigs/alice-{name}.yaml'
  fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
  with os.fdopen(fd,'w') as f:f.write(result['status']['value'])
  config=json.loads(subprocess.check_output(['kubectl','--kubeconfig',str(path),'config','view','--raw','-o','json']))
  assert {c['name'] for c in config['clusters']}=={name,'rancher'}
  assert config['current-context']==name
  cluster=next(c['cluster'] for c in config['clusters'] if c['name']==name)
  assert cluster['server']==BASE+'/k8s/clusters/'+cid
  assert not cluster.get('insecure-skip-tls-verify')
  assert base64.b64decode(cluster['certificate-authority-data']).strip()==(ROOT/'secrets/ca/ca.crt').read_bytes().strip()
  assert result['spec']['ttl']==3600
  records.append({'cluster':name,'resource':result['metadata']['name'],'ttlSeconds':result['spec']['ttl'],'context':config['current-context'],'server':cluster['server'],'created':result['metadata']['creationTimestamp']})
  token_records=[]
  for token_name in result['status']['tokens']:
   t=api.call('/apis/ext.cattle.io/v1/tokens/'+token_name)
   assert t['spec']['ttl']==3600000
   token_records.append({'id':token_name,'ttlMilliseconds':t['spec']['ttl'],'expiresAt':t['status']['expiresAt']})
  records[-1]['tokens']=token_records
  print('PASS:',name,'Rancher-generated Alice kubeconfig; proxy URL, CA data, 1-hour TTL verified')
 (ROOT/'artifacts/step-08/kubeconfigs.json').write_text(json.dumps(records,indent=2)+'\n')
finally:api.call('/v3/tokens?action=logout',{},method='POST')

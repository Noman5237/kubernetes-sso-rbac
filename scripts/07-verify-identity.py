#!/usr/bin/env python3
import json,time
from rancher_api import Rancher,ROOT
from oidc_login import authorization_code

def login(username):
 api=Rancher()
 provider=api.call('/v3-public/authProviders/keycloakoidc')
 code=authorization_code(api,provider['redirectUrl'],username)
 result=api.call(provider['actions']['login'],{'code':code,'responseType':'json'})
 api.token=result['token'];return api

alice=login('alice')
try:
 clusters=alice.call('/v3/clusters')['data']
 assert all(c['id']!='local' for c in clusters),'Alice sees management cluster'
 print('PASS: actual Alice OIDC+PKCE login; management cluster not visible',flush=True)
 assignments=json.loads((ROOT/'artifacts/step-07/assignments.json').read_text())
 matrix=[]
 for assignment in assignments:
  cid=assignment['clusterId'];name=assignment['cluster'];admin=name=='cluster-b'
  cases=[('get','pods','','demo',True),('list','deployments','apps','demo',True),('create','deployments','apps','demo',admin),('delete','deployments','apps','demo',admin),('get','secrets','','demo',admin),('create','rolebindings','rbac.authorization.k8s.io','demo',admin),('get','pods','','kube-system',False),('get','nodes','',None,False),('create','clusterrolebindings','rbac.authorization.k8s.io',None,False),('create','nodes','',None,False),('create','persistentvolumes','',None,False),('create','storageclasses','storage.k8s.io',None,False),('create','apiservices','apiregistration.k8s.io',None,False)]
  for verb,resource,group,namespace,expected in cases:
   attrs={'verb':verb,'resource':resource,'group':group}
   if namespace:attrs['namespace']=namespace
   body={'apiVersion':'authorization.k8s.io/v1','kind':'SelfSubjectAccessReview','spec':{'resourceAttributes':attrs}}
   for attempt in range(12):
    r=alice.call('/k8s/clusters/'+cid+'/apis/authorization.k8s.io/v1/selfsubjectaccessreviews',body)
    allowed=r['status']['allowed']
    if allowed==expected:break
    time.sleep(5)
   matrix.append({'cluster':name,**attrs,'expected':expected,'allowed':allowed})
   assert allowed==expected, str(matrix[-1])
  assert alice.call('/k8s/clusters/'+cid+'/api/v1/namespaces/demo/pods')['items']==[]
  try:alice.call('/k8s/clusters/'+cid+'/api/v1/namespaces/kube-system/pods')
  except RuntimeError as e:assert '403' in str(e)
  else:raise AssertionError('Outside-project read allowed')
  print('PASS: '+name+' permission matrix and real allowed/forbidden reads',flush=True)
 (ROOT/'artifacts/step-07/alice-permissions.json').write_text(json.dumps(matrix,indent=2)+'\n')
finally:
 alice.call('/v3/tokens?action=logout',{},method='POST')
try:
 denied=login('no-role')
except RuntimeError as e:
 assert '401' in str(e) or '403' in str(e),str(e)
 print('PASS: no-role authenticates at Keycloak but Rancher denies site access',flush=True)
else:
 denied.call('/v3/tokens?action=logout',{},method='POST')
 raise AssertionError('No-role user entered Rancher')
with Rancher() as recovery:
 assert any(c['id']=='local' for c in recovery.call('/v3/clusters')['data'])
 print('PASS: local Rancher administrator recovery login preserved',flush=True)

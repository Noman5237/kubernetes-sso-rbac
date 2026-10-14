#!/usr/bin/env python3
import json,subprocess
from rancher_api import Rancher,ROOT
with Rancher() as api:
 uid=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())['users']['alice']
 alice=next(u for u in api.call('/v3/users')['data'] if 'keycloakoidc_user://'+uid in u.get('principalIds',[]))
 grants=[g for g in api.call('/v3/globalRoleBindings')['data'] if g.get('userId')==alice['id']]
 assert {g['globalRoleId'] for g in grants}=={'user-base'}
 print('PASS: Alice global role is user-base only')
for a in json.loads((ROOT/'artifacts/step-07/assignments.json').read_text()):
 k=['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{a["cluster"]}-admin.yaml')]
 out={}
 for kind in ('rolebindings','clusterrolebindings'):
  items=json.loads(subprocess.check_output(k+['get',kind,'-A','-o','json']))['items']
  assert not any(s.get('name','').startswith('keycloakoidc_group://') for x in items for s in x.get('subjects',[])), 'Obsolete group binding remains'
  out[kind]=[{'namespace':x['metadata'].get('namespace'),'name':x['metadata']['name'],'roleRef':x['roleRef'],'subjects':x.get('subjects',[])} for x in items if any(s.get('kind')=='User' and s.get('name')==a['userId'] for s in x.get('subjects',[]))]
 assert any(r.get('namespace')=='demo' and r['roleRef']['name']==a['roleTemplateId'] for r in out['rolebindings'])
 assert not any(r['roleRef']['name'].endswith('-promoted') for r in out['clusterrolebindings'])
 namespaces=json.loads(subprocess.check_output(k+['get','namespaces','-o','json']))['items']
 assert [n['metadata']['name'] for n in namespaces if n['metadata'].get('annotations',{}).get('field.cattle.io/projectId')==a['projectId']]==['demo']
 (ROOT/f'artifacts/step-07/{a["cluster"]}-generated-rbac.json').write_text(json.dumps(out,indent=2)+'\n')
 print('PASS:',a['cluster'],'direct user binding, demo-only project, no promoted role binding')

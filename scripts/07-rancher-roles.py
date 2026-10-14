#!/usr/bin/env python3
"""Reusable role definitions + explicit user/project bindings, entirely in Rancher."""
import json,subprocess,time
from rancher_api import Rancher,ROOT
from oidc_login import authorization_code
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
with Rancher() as a:
 for g in a.call('/v3/globalRoles')['data']:
  wanted=g['id']=='user-base'
  if g.get('newUserDefault',False)!=wanted:
   a.call('/v3/globalRoles/'+g['id'],{'newUserDefault':wanted},method='PUT')
 # Retire only the old POC group bindings and cluster-named custom roles.
 oldroles={r['id'] for r in a.call('/v3/roleTemplates')['data'] if r['name'] in ('lab-a-developer','lab-b-namespace-admin')}
 for b in a.call('/v3/projectRoleTemplateBindings')['data']:
  if b.get('roleTemplateId') in oldroles and b.get('groupPrincipalId') in ('keycloakoidc_group://cluster-a-dev','keycloakoidc_group://cluster-b-admin'):
   a.call('/v3/projectRoleTemplateBindings/'+b['id'],method='DELETE')
 for rid in oldroles:
  for attempt in range(30):
   refs=[b for b in a.call('/v3/projectRoleTemplateBindings')['data'] if b.get('roleTemplateId')==rid]
   if not refs:break
   time.sleep(1)
  assert not refs,'Old role has unexpected bindings; review before deleting'
  a.call('/v3/roleTemplates/'+rid,method='DELETE')
 roles={}
 for desired in json.loads((ROOT/'config/rancher/project-roles.json').read_text()):
  found=[r for r in a.call('/v3/roleTemplates')['data'] if r['name']==desired['name']]
  role=a.call('/v3/roleTemplates/'+found[0]['id'],desired,method='PUT') if found else a.call('/v3/roleTemplates',desired)
  roles[desired['name']]=role['id']
 result=[]
 for member in json.loads((ROOT/'config/rancher/project-members.json').read_text()):
  name=member['cluster'];cid=(ROOT/f'artifacts/step-06/{name}-id.txt').read_text().strip()
  found=[p for p in a.call('/v3/projects?clusterId='+cid)['data'] if p['name']==member['project']]
  p=found[0] if found else a.call('/v3/projects',{'type':'project','name':member['project'],'clusterId':cid,'description':'Only demo namespace; authentication POC'})
  pid=p['id'];principal='keycloakoidc_user://'+ids['users'][member['user']]
  subprocess.run(['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{name}-admin.yaml'),'patch','namespace',member['namespace'],'--type=merge','-p',json.dumps({'metadata':{'annotations':{'field.cattle.io/projectId':pid},'labels':{'field.cattle.io/projectId':pid.split(':')[-1]}}})],check=True)
  users=[u for u in a.call('/v3/users')['data'] if principal in u.get('principalIds',[])]
  if not users:
   # First real login establishes the external identity without IdP directory search.
   session=Rancher();provider=session.call('/v3-public/authProviders/keycloakoidc')
   code=authorization_code(session,provider['redirectUrl'],member['user'])
   session.token=session.call(provider['actions']['login'],{'code':code,'responseType':'json'})['token']
   session.call('/v3/tokens?action=logout',{},method='POST')
   users=[u for u in a.call('/v3/users')['data'] if principal in u.get('principalIds',[])]
  assert len(users)==1,'Expected one Rancher record for external identity'
  user_id=users[0]['id']
  found=[b for b in a.call('/v3/projectRoleTemplateBindings?projectId='+pid)['data'] if b.get('userId')==user_id and b.get('roleTemplateId')==roles[member['role']]]
  if not found:a.call('/v3/projectRoleTemplateBindings',{'type':'projectRoleTemplateBinding','projectId':pid,'roleTemplateId':roles[member['role']],'userId':user_id})
  result.append({'cluster':name,'clusterId':cid,'projectId':pid,'namespace':member['namespace'],'user':member['user'],'userId':user_id,'userPrincipalId':principal,'role':member['role'],'roleTemplateId':roles[member['role']]})
 (ROOT/'artifacts/step-07/assignments.json').write_text(json.dumps(result,indent=2)+'\n')
 print('PASS: reusable roles and direct user/project assignments; old group roles/bindings removed.')

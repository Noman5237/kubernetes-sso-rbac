#!/usr/bin/env python3
import json
from keycloak_api import Keycloak
from rancher_api import Rancher,ROOT
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
with Keycloak() as k:
 base='/admin/realms/kubernetes'
 assert k.request(base+'/groups')==[], 'POC realm still contains groups'
 for uid in ids['users'].values():assert k.request(base+'/users/'+uid+'/groups')==[]
 mappers=k.request(base+'/clients/'+ids['clientId']+'/protocol-mappers/models')
 assert not any(m['protocolMapper']=='oidc-group-membership-mapper' for m in mappers)
 print('PASS: no Keycloak groups, user memberships, or group claim mappers')
with Rancher() as a:
 config=a.call('/v3/authConfigs/keycloakoidc')
 expected={'keycloakoidc_user://'+ids['users'][u] for u in json.loads((ROOT/'config/rancher/login-users.json').read_text())}
 assert set(config['allowedPrincipalIds'])==expected and config['accessMode']=='restricted'
 roles=a.call('/v3/roleTemplates')['data']
 assert not any(r['name'] in ('lab-a-developer','lab-b-namespace-admin') for r in roles)
 allbindings=a.call('/v3/projectRoleTemplateBindings')['data']
 assert not any((b.get('groupPrincipalId') or '').startswith('keycloakoidc_group://') for b in allbindings)
 for assignment in json.loads((ROOT/'artifacts/step-07/assignments.json').read_text()):
  found=[b for b in allbindings if b.get('projectId')==assignment['projectId'] and b.get('roleTemplateId')==assignment['roleTemplateId'] and b.get('userId')==assignment['userId']]
  assert len(found)==1
 print('PASS: user-only admission, reusable roles, exactly one direct Alice binding per demo project; legacy roles/bindings gone')

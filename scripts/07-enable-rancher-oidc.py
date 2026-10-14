#!/usr/bin/env python3
import json
from rancher_api import Rancher,ROOT
from oidc_login import authorization_code
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
config=json.loads((ROOT/'config/rancher/oidc.json').read_text())
config['allowedPrincipalIds']=['keycloakoidc_user://'+ids['users'][name] for name in json.loads((ROOT/'config/rancher/login-users.json').read_text())]
config['clientSecret']=(ROOT/'secrets/keycloak/rancher-client-secret').read_text().strip()
with Rancher() as api:
 if api.call('/v3/authConfigs/keycloakoidc').get('enabled'):
  # Update admission only; retain the tested client secret, PKCE, and recovery linkage.
  api.call('/v3/keyCloakOIDCConfigs/keycloakoidc',{'accessMode':'restricted','allowedPrincipalIds':config['allowedPrincipalIds'],'groupSearchEnabled':False},method='PUT')
  print('PASS: restricted admission now lists users, not groups.')
 else:
  result=api.call('/v3/keyCloakOIDCConfigs/keycloakoidc?action=configureTest',config)
  code=authorization_code(api,result['redirectUrl'],'rancher-admin')
  result=api.call('/v3/keyCloakOIDCConfigs/keycloakoidc?action=testAndApply',{'code':code,'enabled':True,'oidcConfig':config})
  # testAndApply issues its own session token; revoke that separate session too.
  if result.get('token'):
   old=api.token;api.token=result['token']
   api.call('/v3/tokens?action=logout',{},method='POST');api.token=old
  print('PASS: OIDC enabled using actual code+PKCE login; dedicated setup identity linked to admin.')
 print('Global role defaults:',[{k:g.get(k) for k in ('id','name','newUserDefault')} for g in api.call('/v3/globalRoles')['data'] if g.get('newUserDefault') or g['id']=='user-base'])

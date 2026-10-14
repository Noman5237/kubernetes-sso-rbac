#!/usr/bin/env python3
import os,secrets
from keycloak_api import Keycloak,ROOT
p=ROOT/'secrets/keycloak/recovery-password'
# Create the permanent account using the currently working administrator.
with Keycloak() as current:
 if not p.exists():
  value=secrets.token_urlsafe(24)
  current.request('/admin/realms/master/users',{'username':'recovery-admin','enabled':True,'credentials':[{'type':'password','value':value,'temporary':False}]})
  uid=current.request('/admin/realms/master/users?username=recovery-admin&exact=true')[0]['id']
  role=current.request('/admin/realms/master/roles/admin')
  current.request('/admin/realms/master/users/'+uid+'/role-mappings/realm',[role])
  fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(fd,'w') as f:f.write(value)
# Verify actual login and administrative access before removing temporary bootstrap user.
with Keycloak() as recovery:
 assert any(r['realm']=='kubernetes' for r in recovery.request('/admin/realms'))
 for old in recovery.request('/admin/realms/master/users?username=lab-admin&exact=true'):
  recovery.request('/admin/realms/master/users/'+old['id'],method='DELETE')
print('PASS: permanent Keycloak recovery admin verified; temporary bootstrap user removed.')

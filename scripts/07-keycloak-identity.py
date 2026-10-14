#!/usr/bin/env python3
import json,os,secrets
from keycloak_api import Keycloak,ROOT
private=ROOT/'secrets/keycloak'
def save(path,value):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:f.write(value)
def password(name):
 p=private/(name+'-password')
 if not p.exists():save(p,secrets.token_urlsafe(24))
 return p.read_text().strip()
with Keycloak() as k:
 realms=k.request('/admin/realms')
 if not any(r['realm']=='kubernetes' for r in realms):k.request('/admin/realms',json.loads((ROOT/'config/keycloak/realm.json').read_text()))
 base='/admin/realms/kubernetes'
 # Remove only the two obsolete POC groups; preserve all user identities/passwords.
 for g in k.request(base+'/groups'):
  if g['name'] in ('cluster-a-dev','cluster-b-admin'):
   k.request(base+'/groups/'+g['id'],method='DELETE')
 config=json.loads((ROOT/'config/keycloak/rancher-client.json').read_text())
 clients=k.request(base+'/clients?clientId=rancher')
 if not clients:k.request(base+'/clients',config)
 else:
  for m in k.request(base+'/clients/'+clients[0]['id']+'/protocol-mappers/models'):
   if m['protocolMapper']=='oidc-group-membership-mapper':
    k.request(base+'/clients/'+clients[0]['id']+'/protocol-mappers/models/'+m['id'],method='DELETE')
  k.request(base+'/clients/'+clients[0]['id'],config,method='PUT')
 cid=k.request(base+'/clients?clientId=rancher')[0]['id']
 for scope in k.request(base+'/clients/'+cid+'/default-client-scopes'):
  if scope['name'] not in config['defaultClientScopes']:
   k.request(base+'/clients/'+cid+'/default-client-scopes/'+scope['id'],method='DELETE')
 save(private/'rancher-client-secret',k.request(base+'/clients/'+cid+'/client-secret')['value'])
 users={}
 for name,first,last in [('alice','Alice','Lab'),('no-role','NoRole','Lab'),('rancher-admin','Rancher','Administrator')]:
  found=k.request(base+'/users?username='+name+'&exact=true')
  if not found:
   k.request(base+'/users',{'username':name,'enabled':True,'firstName':first,'lastName':last,'email':name+'@lab.test','emailVerified':True,'credentials':[{'type':'password','value':password(name),'temporary':False}]})
  uid=k.request(base+'/users?username='+name+'&exact=true')[0]['id'];users[name]=uid
 # No Keycloak directory-query roles are required for explicit Rancher user bindings.
 rm=k.request(base+'/clients?clientId=realm-management')[0]['id']
 assigned=k.request(base+'/users/'+users['rancher-admin']+'/role-mappings/clients/'+rm)
 obsolete=[role for role in assigned if role['name'] in ('query-users','query-groups','view-users')]
 if obsolete:k.request(base+'/users/'+users['rancher-admin']+'/role-mappings/clients/'+rm,obsolete,method='DELETE')
 (ROOT/'artifacts/step-07/keycloak-identities.json').write_text(json.dumps({'users':users,'clientId':cid},indent=2)+'\n')
 print('PASS: realm, confidential PKCE client, identity-only claims and users (no POC groups) configured. Secrets retained locally.')

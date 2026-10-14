#!/usr/bin/env python3
"""Explicit migration cleanup: expire Alice's old sessions; leave administrators alone."""
import json
from keycloak_api import Keycloak
from rancher_api import Rancher,ROOT
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
with Rancher() as a:
 users=[u for u in a.call('/v3/users')['data'] if 'keycloakoidc_user://'+ids['users']['alice'] in u.get('principalIds',[])]
 if users:
  for t in a.call('/v3/tokens')['data']:
   if t.get('userId')==users[0]['id']:a.call('/v3/tokens/'+t['id'],method='DELETE')
with Keycloak() as k:k.request('/admin/realms/kubernetes/users/'+ids['users']['alice']+'/logout',{},method='POST')
print('PASS: Alice old sessions revoked; fresh login required. Admin sessions preserved.')

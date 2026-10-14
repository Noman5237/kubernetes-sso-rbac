"""Keycloak administration using explicit CA and local credentials."""
import json,ssl,urllib.request,urllib.parse,urllib.error
from rancher_api import ROOT
SSO='https://sso.lab.test:8443'
class Keycloak:
 def __init__(self):
  self.ctx=ssl.create_default_context(cafile=str(ROOT/'secrets/ca/ca.crt'))
  self.token=None
 def request(self,path,data=None,method=None,form=False):
  headers={}
  if self.token:headers['Authorization']='Bearer '+self.token
  if data is not None:
   data=(urllib.parse.urlencode(data).encode() if form else json.dumps(data).encode())
   headers['Content-Type']='application/x-www-form-urlencoded' if form else 'application/json'
  try:
   with urllib.request.urlopen(urllib.request.Request(SSO+path,data=data,headers=headers,method=method),context=self.ctx,timeout=30) as r:
    b=r.read();return json.loads(b) if b else None
  except urllib.error.HTTPError as e:raise RuntimeError('Keycloak HTTP '+str(e.code)) from None
 def __enter__(self):
  permanent=ROOT/'secrets/keycloak/recovery-password'
  if permanent.exists(): username='recovery-admin';password=permanent.read_text().strip()
  else:
   env=dict(line.split('=',1) for line in (ROOT/'secrets/keycloak/runtime.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
   username='lab-admin';password=env['KC_BOOTSTRAP_ADMIN_PASSWORD']
  t=self.request('/realms/master/protocol/openid-connect/token',{'client_id':'admin-cli','grant_type':'password','username':username,'password':password},form=True)
  self.token=t['access_token'];self.refresh=t['refresh_token'];return self
 def __exit__(self,*args):
  self.request('/realms/master/protocol/openid-connect/logout',{'client_id':'admin-cli','refresh_token':self.refresh},form=True)

#!/usr/bin/env python3
"""Live lifecycle tests. Restore mutated identity/admission/binding state in finally.
Use --restore after a hard interruption. Never prints tokens or passwords.
"""
import argparse, datetime, http.cookiejar, json, os, re, secrets, subprocess, time
import urllib.request, urllib.parse, urllib.error
from rancher_api import Rancher,ROOT,BASE
from keycloak_api import Keycloak,SSO
from oidc_login import LoginForm,StopCallback
class RenewingKeycloak(Keycloak):
 def request(self,path,data=None,method=None,form=False):
  try:return super().request(path,data,method,form)
  except RuntimeError as e:
   if str(e)!='Keycloak HTTP 401' or not getattr(self,'refresh',None):raise
   t=super().request('/realms/master/protocol/openid-connect/token',{'client_id':'admin-cli','grant_type':'refresh_token','refresh_token':self.refresh},form=True)
   self.token=t['access_token'];self.refresh=t['refresh_token']
   return super().request(path,data,method,form)

OUT=ROOT/'artifacts/step-09';PRIVATE=ROOT/'secrets/lifecycle'
OUT.mkdir(exist_ok=True);PRIVATE.mkdir(exist_ok=True,mode=0o700)
assignments=json.loads((ROOT/'artifacts/step-07/assignments.json').read_text())
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
uid=ids['users']['alice'];principal='keycloakoidc_user://'+uid
user_path='/admin/realms/kubernetes/users/'+uid
cfg_path='/v3/keyCloakOIDCConfigs/keycloakoidc'
report={'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observations':[],'createdKubeconfigs':[],'restored':False}
sessions=[]
def save(): (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
def note(name,**data):
 report['observations'].append({'test':name,**data});save();print(name,json.dumps(data),flush=True)
def status(api,path):
 try:api.call(path);return 200
 except RuntimeError as e:
  m=re.fullmatch('Rancher API HTTP status (401|403|404)',str(e))
  if not m:raise
  return int(m[1])
def login():
 """Fresh cookies + real password/code/PKCE flow; report which service rejects it."""
 api=Rancher();p=api.call('/v3-public/authProviders/keycloakoidc');state=secrets.token_urlsafe(24)
 url=p['redirectUrl']+('&' if '?' in p['redirectUrl'] else '?')+urllib.parse.urlencode({'scope':'openid profile email','state':state})
 opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=api.context),urllib.request.HTTPCookieProcessor(api.cookies),StopCallback())
 with opener.open(url,timeout=30) as r:page=r.read().decode()
 form=LoginForm();form.feed(page);assert form.action and form.action.startswith(SSO+'/')
 form.fields.update(username='alice',password=(ROOT/'secrets/keycloak/alice-password').read_text().strip())
 req=urllib.request.Request(form.action,data=urllib.parse.urlencode(form.fields).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
 try:
  with opener.open(req,timeout=30) as r:body=r.read().decode()
  if re.search('account is disabled|account disabled',body,re.I):return None,{'allowed':False,'stage':'keycloak','reason':'Account is disabled'}
  if re.search('invalid username or password',body,re.I):return None,{'allowed':False,'stage':'keycloak','reason':'Invalid username or password'}
  raise AssertionError('Unexpected Keycloak response; no code and no recognized denial')
 except urllib.error.HTTPError as e:
  assert e.code==302,'Unexpected login HTTP status'
  target=e.headers['Location'];assert target.startswith(BASE+'/verify-auth?')
  q=urllib.parse.parse_qs(urllib.parse.urlparse(target).query);assert q.get('state')==[state] and q.get('code')
 try:api.token=api.call(p['actions']['login'],{'code':q['code'][0],'responseType':'json'})['token']
 except RuntimeError as e:
  assert re.fullmatch('Rancher API HTTP status (401|403)',str(e)),str(e)
  return None,{'allowed':False,'stage':'rancher','keycloakCodeReturned':True,'httpStatus':int(str(e).split()[-1])}
 current=[t for t in api.call('/v3/tokens')['data'] if t.get('current')];assert len(current)==1
 report.setdefault('testSessionIds',[]).append(current[0]['id']);save()
 sessions.append(api);return api,{'allowed':True,'stage':'rancher','keycloakCodeReturned':True}
def fresh():
 a,r=login();assert a,r;return a
def token_only(api):
 a=Rancher();a.token=api.token;return a
def create_config(api,label,ttl,clusters):
 r=api.call('/apis/ext.cattle.io/v1/kubeconfigs',{'apiVersion':'ext.cattle.io/v1','kind':'Kubeconfig','spec':{'clusters':clusters,'currentContext':clusters[0],'ttl':ttl,'description':'Step 09 lifecycle '+label}})
 path=PRIVATE/('alice-'+label+'.yaml');fd=os.open(path,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w') as f:f.write(r['status']['value'])
 entry={'name':r['metadata']['name'],'label':label,'ttlSeconds':r['spec']['ttl'],'created':r['metadata']['creationTimestamp'],'tokens':r['status']['tokens']}
 report['createdKubeconfigs'].append(entry);save();assert entry['ttlSeconds']==ttl
 return path,entry
def probe(path,cluster='cluster-a',require_anonymous=False):
 p=subprocess.run(['kubectl','--kubeconfig',str(path),'--context',cluster,'--request-timeout=10s','get','--raw=/api/v1/namespaces/demo/pods'],capture_output=True,text=True,timeout=20)
 if p.returncode==0:
  x=json.loads(p.stdout);assert x['kind']=='PodList' and x['items']==[];return 200
 if re.search('Unauthorized|must be logged in',p.stderr,re.I):return 401
 if re.search('Forbidden',p.stderr,re.I):
  if require_anonymous:assert 'system:unauthenticated' in p.stderr,'Denial was authorization, not anonymous authentication'
  return 403
 raise AssertionError('Unexpected kubectl failure (not authentication/authorization denial)')
def until(fn,wanted,seconds=45):
 start=time.monotonic();samples=[]
 while True:
  value=fn();elapsed=round(time.monotonic()-start,3);samples.append({'elapsedSeconds':elapsed,'httpStatus':value})
  if value in wanted:return {'observedWithinSeconds':elapsed,'samples':samples}
  if elapsed>=seconds:raise AssertionError('Expected status not observed: '+json.dumps(samples))
  time.sleep(2)
def observe(path,session,seconds=20):
 start=time.monotonic();samples=[]
 while True:
  samples.append({'elapsedSeconds':round(time.monotonic()-start,3),'kubeconfigStatus':probe(path),'sessionStatus':status(token_only(session),'/v3/clusters')})
  if time.monotonic()-start>=seconds:return samples
  time.sleep(5)
def bindings(admin):return admin.call('/v3/projectRoleTemplateBindings')['data']
def matches(b,x):return all(b.get(k)==x[k] for k in ['projectId','roleTemplateId','userId'])
def restore(admin,k,baseline):
 k.request(user_path,{'enabled':baseline['keycloakEnabled']},method='PUT')
 admin.call(cfg_path,baseline['admission'],method='PUT')
 x=baseline['binding'];found=[b for b in bindings(admin) if matches(b,x)]
 if not found:
  # Wait until the old binding's finalizers have completed before reusing its name.
  deadline=time.monotonic()+30
  while any(b['id']==x['id'] for b in bindings(admin)):
   assert time.monotonic()<deadline,'Binding deletion still pending';time.sleep(1)
  admin.call('/v3/projectRoleTemplateBindings',{k:x[k] for k in ['type','name','projectId','roleTemplateId','userId']})
 assert k.request(user_path)['enabled']==baseline['keycloakEnabled']
 c=admin.call('/v3/authConfigs/keycloakoidc')
 assert all(c.get(key)==value for key,value in baseline['admission'].items())
 assert len([b for b in bindings(admin) if matches(b,x)])==1

def run():
 with Rancher() as admin,RenewingKeycloak() as k:
  a=assignments[0];bs=[b for b in bindings(admin) if matches(b,a)];assert len(bs)==1
  c=admin.call('/v3/authConfigs/keycloakoidc')
  baseline={'keycloakEnabled':k.request(user_path)['enabled'],'admission':{key:c[key] for key in ['accessMode','allowedPrincipalIds','groupSearchEnabled']},'binding':{key:bs[0][key] for key in ['id','type','name','projectId','roleTemplateId','userId']}}
  assert baseline['keycloakEnabled'] and principal in baseline['admission']['allowedPrincipalIds']
  (OUT/'restore-state.json').write_text(json.dumps(baseline,indent=2)+'\n')
  control=None
  try:
   session=fresh();control,control_resource=create_config(session,'control',900,[x['clusterId'] for x in assignments])
   assert probe(control)==200 and probe(control,'cluster-b')==200
   note('baseline',aliceFreshOIDC=True,clusterA=200,clusterB=200)

   revoked,entry=create_config(session,'revocation',300,[a['clusterId']]);assert probe(revoked)==200
   session.call('/apis/ext.cattle.io/v1/kubeconfigs/'+entry['name'],method='DELETE')
   timing=until(lambda:probe(revoked,require_anonymous=True),{401,403})
   token_checks={name:status(admin,'/apis/ext.cattle.io/v1/tokens/'+name) for name in entry['tokens']};assert all(v==404 for v in token_checks.values())
   assert probe(control)==200
   note('kubeconfigDeletion',**timing,associatedTokens=token_checks,independentKubeconfigStatus=200)

   expiring,entry=create_config(session,'expiry',20,[a['clusterId']]);assert probe(expiring)==200
   token=admin.call('/apis/ext.cattle.io/v1/tokens/'+entry['tokens'][0]);expires=token['status']['expiresAt']
   timing=until(lambda:probe(expiring,require_anonymous=True),{401,403},seconds=40)
   note('tokenExpiry',requestedTTLSeconds=20,expiresAt=expires,**timing)

   logout_session=fresh();logout_config,_=create_config(logout_session,'logout',600,[a['clusterId']]);old=token_only(logout_session)
   assert status(old,'/v3/clusters')==200 and probe(logout_config)==200
   logout_session.call('/v3/tokens?action=logout',{},method='POST');sessions.remove(logout_session)
   timing=until(lambda:status(old,'/v3/clusters'),{401,403})
   assert probe(logout_config)==200
   note('rancherLogout',**timing,independentlyIssuedKubeconfigStatus=200)

   admin.call('/v3/projectRoleTemplateBindings/'+baseline['binding']['id'],method='DELETE')
   timing=until(lambda:probe(control),{403},seconds=60);assert probe(control,'cluster-b')==200
   note('projectBindingRemoval',**timing,clusterBStatus=200)
   restore(admin,k,baseline);timing=until(lambda:probe(control),{200},seconds=60)
   note('projectBindingRestored',**timing)

   k.request(user_path,{'enabled':False},method='PUT');assert k.request(user_path)['enabled'] is False
   blocked,decision=login();assert blocked is None and decision['stage']=='keycloak',decision
   note('keycloakDisabled',newLogin=decision,existingCredentials=observe(control,session))
   restore(admin,k,baseline);fresh();note('keycloakReenabled',newLoginAllowed=True)

   admission=dict(baseline['admission']);admission['allowedPrincipalIds']=[p for p in admission['allowedPrincipalIds'] if p!=principal]
   admin.call(cfg_path,admission,method='PUT')
   assert principal not in admin.call('/v3/authConfigs/keycloakoidc')['allowedPrincipalIds']
   decisions=[]
   for i in range(3):
    client,decision=login();decisions.append({'attempt':i+1,**decision})
    if client:client.call('/v3/tokens?action=logout',{},method='POST');sessions.remove(client)
    if i<2:time.sleep(5)
   note('loginAllowListRemoval',accessMode=admission['accessMode'],newLogins=decisions,existingCredentials=observe(control,session))
   restore(admin,k,baseline);fresh();note('loginAllowListRestored',newLoginAllowed=True)
   report['testsCompleted']=True
  finally:
   restore(admin,k,baseline)
   if control:
    until(lambda:probe(control),{200},seconds=60);assert probe(control,'cluster-b')==200
   report['restored']=True;save()
   for entry in report['createdKubeconfigs']:
    path='/apis/ext.cattle.io/v1/kubeconfigs/'+entry['name']
    if status(admin,path)!=404:admin.call(path,method='DELETE')
   for session in sessions[:]:
    if status(token_only(session),'/v3/clusters')==200:session.call('/v3/tokens?action=logout',{},method='POST')
   report['testCredentialsRevoked']=True;report['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
   print('RESTORED: Alice enabled, original admission and A binding restored; disposable credentials revoked',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--restore',action='store_true');args=parser.parse_args()
 if args.restore:
  with Rancher() as a,Keycloak() as k:restore(a,k,json.loads((OUT/'restore-state.json').read_text()))
  print('RESTORED: identity, admission and A binding')
 else:run()

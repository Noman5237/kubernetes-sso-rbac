#!/usr/bin/env python3
"""Controlled Keycloak/Rancher outages; restore services and revoke test credentials.
No cluster, database, volume, or application-resource deletion. --restore recovers
from a hard interruption using the saved original replica count.
"""
import argparse,base64,datetime,json,os,re,socket,ssl,subprocess,time,urllib.error,urllib.request
from pathlib import Path
from http.client import RemoteDisconnected
from rancher_api import Rancher,ROOT,BASE
from keycloak_api import Keycloak,SSO
from oidc_login import authorization_code
OUT=ROOT/'artifacts/step-10';PRIVATE=ROOT/'secrets/reliability'
OUT.mkdir(exist_ok=True);PRIVATE.mkdir(exist_ok=True,mode=0o700)
assignments=json.loads((ROOT/'artifacts/step-07/assignments.json').read_text())
ids=json.loads((ROOT/'artifacts/step-07/keycloak-identities.json').read_text())
ctx=ssl.create_default_context(cafile=str(ROOT/'secrets/ca/ca.crt'))
report={'startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'observations':[],'testSessionIds':[],'testKubeconfigs':[]}
def save(): (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
def note(name,**data):
 report['observations'].append({'test':name,**data});save();print(name,json.dumps(data),flush=True)
def command(args,timeout=45):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 if p.returncode:raise RuntimeError('Command failed: '+args[0]+' '+str(p.returncode))
 return p.stdout

def kube(name,*args,timeout=45):return command(['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{name}-admin.yaml'),*args],timeout)
def http(url,token=None,timeout=6):
 headers={'Authorization':'Bearer '+token} if token else {}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),context=ctx,timeout=timeout) as r:return r.status
 except urllib.error.HTTPError as e:return e.code
 except (urllib.error.URLError,TimeoutError,socket.timeout,RemoteDisconnected):return 'network-unavailable'
def wait_for(fn,predicate,limit=240):
 start=time.monotonic();last_print=-30
 while True:
  result=fn();elapsed=time.monotonic()-start
  if predicate(result):return {'elapsedSeconds':round(elapsed,3),'result':result}
  if elapsed>=limit:raise RuntimeError('Recovery condition timed out; last status '+str(result))
  if elapsed-last_print>=20:print('Waiting for readiness:',round(elapsed),'seconds; status',result,flush=True);last_print=elapsed
  time.sleep(3)
def alice_login():
 api=Rancher();p=api.call('/v3-public/authProviders/keycloakoidc')
 code=authorization_code(api,p['redirectUrl'],'alice')
 api.token=api.call(p['actions']['login'],{'code':code,'responseType':'json'})['token']
 current=[t['id'] for t in api.call('/v3/tokens')['data'] if t.get('current')];assert len(current)==1
 report['testSessionIds'].extend(current);save();return api

def kubeconfig(api):
 r=api.call('/apis/ext.cattle.io/v1/kubeconfigs',{'apiVersion':'ext.cattle.io/v1','kind':'Kubeconfig','spec':{'clusters':[x['clusterId'] for x in assignments],'currentContext':assignments[0]['clusterId'],'ttl':1800,'description':'Step 10 reliability only'}})
 path=PRIVATE/'alice-outages.yaml';fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,'w') as f:f.write(r['status']['value'])
 report['testKubeconfigs'].append({'name':r['metadata']['name'],'tokens':r['status']['tokens'],'ttlSeconds':r['spec']['ttl']});save();return path

def proxy(path,cluster):
 p=subprocess.run(['kubectl','--kubeconfig',str(path),'--context',cluster,'--request-timeout=6s','get','--raw=/api/v1/namespaces/demo/pods'],text=True,capture_output=True,timeout=12)
 if not p.returncode:
  data=json.loads(p.stdout);assert data['kind']=='PodList' and not data['items'];return 200
 if re.search('Unauthorized|must be logged in',p.stderr,re.I):return 401
 if 'Forbidden' in p.stderr:return 403
 if re.search('BadGateway|Bad Gateway|ServiceUnavailable|Service Unavailable|Gateway Timeout|timed out|deadline exceeded|refused|unable to handle|error on the server|InternalError|502|503|504',p.stderr,re.I):return 'service-unavailable'
 message=re.sub(r'token-[a-z0-9]+:[A-Za-z0-9._-]+','[redacted token]',p.stderr.strip())[:700]
 report.setdefault('proxyStartupResponses',[]).append({'cluster':cluster,'exitCode':p.returncode,'message':message});save()
 return 'proxy-not-ready'

def native_access(service_accounts=False):
 rows=[]
 for name in ['mngmt','cluster-a','cluster-b']:
  assert kube(name,'auth','can-i','*','*','--all-namespaces').strip()=='yes'
  nodes=json.loads(kube(name,'get','nodes','-o','json'));assert len(nodes['items'])==1
  item={'cluster':name,'nativeAdministrator':True}
  if name!='mngmt':
   assert not json.loads(kube(name,'get','pods','-n','demo','-o','json'))['items']
   if service_accounts:
    token=kube(name,'-n','demo','create','token','default','--duration=10m').strip()
    cluster=json.loads(kube(name,'config','view','--raw','--minify','-o','json'))['clusters'][0]['cluster']
    ca=ssl.create_default_context(cadata=base64.b64decode(cluster['certificate-authority-data']).decode())
    req=urllib.request.Request(cluster['server']+'/apis/authentication.k8s.io/v1/selfsubjectreviews',data=json.dumps({'apiVersion':'authentication.k8s.io/v1','kind':'SelfSubjectReview'}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,context=ca,timeout=10) as response:identity=json.load(response)
    assert identity['status']['userInfo']['username']=='system:serviceaccount:demo:default'
    item['nativeServiceAccount']=True
    del token
  rows.append(item)
 return rows

def snapshot():
 with Keycloak() as k:
  realm=k.request('/admin/realms/kubernetes');user=k.request('/admin/realms/kubernetes/users/'+ids['users']['alice']);client=k.request('/admin/realms/kubernetes/clients/'+ids['clientId'])
  keycloak={'realmId':realm['id'],'realmEnabled':realm['enabled'],'aliceId':user['id'],'aliceEnabled':user['enabled'],'groups':k.request('/admin/realms/kubernetes/groups'),'client':{key:client.get(key) for key in ['id','clientId','enabled','redirectUris','standardFlowEnabled','directAccessGrantsEnabled','implicitFlowEnabled','publicClient']}}
 with Rancher() as a:
  auth=a.call('/v3/authConfigs/keycloakoidc')
  bindings=a.call('/v3/projectRoleTemplateBindings')['data'];roles=[];members=[]
  for x in assignments:
   role=a.call('/v3/roleTemplates/'+x['roleTemplateId']);roles.append({key:role.get(key) for key in ['id','name','context','rules']})
   found=[b for b in bindings if all(b.get(key)==x[key] for key in ['projectId','roleTemplateId','userId'])];assert len(found)==1
   members.append({key:found[0].get(key) for key in ['id','projectId','roleTemplateId','userId']})
  rancher={'auth':{key:auth.get(key) for key in ['enabled','accessMode','allowedPrincipalIds','groupSearchEnabled']},'roles':roles,'bindings':members,'serverUrl':a.call('/v3/settings/server-url')['value']}
 return {'keycloak':keycloak,'rancher':rancher}

def restore_services(baseline):
 running=command(['docker','inspect','sso-lab-keycloak','--format','{{.State.Running}}']).strip()
 if running!='true':command(['docker','start','sso-lab-keycloak'])
 replicas=int(kube('mngmt','-n','cattle-system','get','deployment','rancher','-o','jsonpath={.spec.replicas}'))
 if replicas!=baseline['rancherReplicas']:kube('mngmt','-n','cattle-system','scale','deployment/rancher','--replicas='+str(baseline['rancherReplicas']))
 wait_for(lambda:http(SSO+'/realms/kubernetes/.well-known/openid-configuration'),lambda x:x==200)
 wait_for(lambda:http(BASE+'/ping'),lambda x:x==200)
 command(['kubectl','--kubeconfig',str(ROOT/'kubeconfigs/mngmt-admin.yaml'),'-n','cattle-system','rollout','status','deployment/rancher','--timeout=240s'],timeout=250)

def cleanup(data):
 with Rancher() as a:
  for x in data.get('testKubeconfigs',[]):
   try:a.call('/apis/ext.cattle.io/v1/kubeconfigs/'+x['name'],method='DELETE')
   except RuntimeError as e:
    if '404' not in str(e):raise
 for name in data.get('testSessionIds',[]):
  assert re.fullmatch(r'token-[a-z0-9]+',name)
  kube('mngmt','delete','tokens.management.cattle.io',name,'--ignore-not-found=true')

def run():
 deployment=json.loads(kube('mngmt','-n','cattle-system','get','deployment','rancher','-o','json'))
 baseline={'rancherReplicas':deployment['spec']['replicas'],'keycloakRunning':command(['docker','inspect','sso-lab-keycloak','--format','{{.State.Running}}']).strip()=='true'}
 assert baseline['rancherReplicas']==1 and deployment['status'].get('readyReplicas')==1 and baseline['keycloakRunning']
 baseline['config']=snapshot();(OUT/'restore-state.json').write_text(json.dumps(baseline,indent=2)+'\n')
 control=None
 try:
  alice=alice_login();control=kubeconfig(alice)
  assert all(proxy(control,x['cluster'])==200 for x in assignments)
  note('baseline',dashboardStatus=http(BASE+'/dashboard/'),native=native_access())

  print('Stopping Keycloak only',flush=True);command(['docker','stop','--time','15','sso-lab-keycloak'])
  assert command(['docker','inspect','sso-lab-keycloak','--format','{{.State.Running}}']).strip()=='false'
  discovery=http(SSO+'/realms/kubernetes/.well-known/openid-configuration');assert discovery in [502,503,504,'network-unavailable']
  try:alice_login()
  except urllib.error.HTTPError as e:
   assert e.code in [502,503,504];new_login={'allowed':False,'httpStatus':e.code}
  except (urllib.error.URLError,TimeoutError):new_login={'allowed':False,'reason':'network-unavailable'}
  else:raise AssertionError('Fresh login unexpectedly succeeded with Keycloak stopped')
  with Rancher() as local_admin:assert any(c['id']=='local' for c in local_admin.call('/v3/clusters')['data'])
  start=time.monotonic();samples=[]
  while True:
   samples.append({'elapsedSeconds':round(time.monotonic()-start,3),'rancherSession':http(BASE+'/v3/clusters',alice.token),'clusterA':proxy(control,'cluster-a'),'clusterB':proxy(control,'cluster-b')})
   if time.monotonic()-start>=20:break
   time.sleep(5)
  dashboard=http(BASE+'/dashboard/');assert dashboard==200
  note('keycloakOutage',discoveryStatus=discovery,newLogin=new_login,dashboardStatus=dashboard,localRancherAdminLogin=True,existingCredentials=samples)
  print('Starting Keycloak',flush=True);start=time.monotonic();command(['docker','start','sso-lab-keycloak'])
  ready=wait_for(lambda:http(SSO+'/realms/kubernetes/.well-known/openid-configuration'),lambda x:x==200)
  alice_login();assert snapshot()==baseline['config']
  note('keycloakRecovered',recoverySeconds=round(time.monotonic()-start,3),freshOIDCLogin=True,configurationPreserved=True,preOutageKubeconfig={x['cluster']:proxy(control,x['cluster']) for x in assignments})

  print('Scaling Rancher to zero; Kubernetes APIs stay up',flush=True)
  kube('mngmt','-n','cattle-system','scale','deployment/rancher','--replicas=0')
  wait_for(lambda:len(json.loads(kube('mngmt','-n','cattle-system','get','pods','-l','app=rancher','-o','json'))['items']),lambda x:x==0,limit=180)
  dashboard=http(BASE+'/dashboard/');assert dashboard in [502,503,504,'network-unavailable']
  failures={x['cluster']:proxy(control,x['cluster']) for x in assignments};assert all(v=='service-unavailable' for v in failures.values())
  native=native_access(service_accounts=True)
  kc=http(SSO+'/realms/kubernetes/.well-known/openid-configuration');assert kc==200
  note('rancherOutage',dashboardStatus=dashboard,proxyResults=failures,native=native,keycloakDiscoveryStatus=kc)

  print('Restoring Rancher replica',flush=True);start=time.monotonic()
  kube('mngmt','-n','cattle-system','scale','deployment/rancher','--replicas='+str(baseline['rancherReplicas']))
  wait_for(lambda:http(BASE+'/ping'),lambda x:x==200)
  wait_for(lambda:proxy(control,'cluster-a'),lambda x:x==200)
  wait_for(lambda:proxy(control,'cluster-b'),lambda x:x==200)
  alice_login();assert snapshot()==baseline['config']
  with Rancher() as admin:
   states=[]
   for x in assignments:
    def cluster_state():return admin.call('/v3/clusters/'+x['clusterId']).get('state')
    wait_for(cluster_state,lambda state:state=='active')
    agent=json.loads(kube(x['cluster'],'-n','cattle-system','get','deployment','cattle-cluster-agent','-o','json'))
    assert agent['status'].get('availableReplicas',0)>=1
    states.append({'cluster':x['cluster'],'state':'active','agentAvailable':True})
  note('rancherRecovered',recoverySeconds=round(time.monotonic()-start,3),freshOIDCLogin=True,preOutageKubeconfigWorks=True,configurationPreserved=True,clusters=states)
  report['testsCompleted']=True;save()
 finally:
  print('Restoring services and removing test credentials',flush=True)
  restore_services(baseline)
  assert snapshot()==baseline['config'];report['restored']=True;save()
  cleanup(report);report['testCredentialsRevoked']=True;report['finishedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
  print('RESTORED: Keycloak running; Rancher original replica count; configuration intact; test credentials revoked',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--restore',action='store_true');args=parser.parse_args()
 if args.restore:
  baseline=json.loads((OUT/'restore-state.json').read_text());data=json.loads((OUT/'results.json').read_text())
  restore_services(baseline);cleanup(data);print('RESTORED: services and test-credential cleanup complete')
 else:run()

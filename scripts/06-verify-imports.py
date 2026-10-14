#!/usr/bin/env python3
import base64,json,ssl,subprocess,time,urllib.request
from rancher_api import Rancher,ROOT
with Rancher() as api:
    for name in ('cluster-a','cluster-b'):
        cid=(ROOT/f'artifacts/step-06/{name}-id.txt').read_text().strip()
        for attempt in range(60):
            c=api.call('/v3/clusters/'+cid)
            if c.get('state')=='active':break
            if attempt%6==0:print(name+': waiting for Rancher Active',flush=True)
            time.sleep(5)
        assert c['state']=='active',name+' not Active'
        print('PASS: '+name+' is Active in Rancher',flush=True)
        k=['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{name}-admin.yaml')]
        deployment=json.loads(subprocess.check_output(k+['-n','cattle-system','get','deployment','cattle-cluster-agent','-o','json']))
        assert deployment['status'].get('availableReplicas',0)>=1
        env={e['name']:e.get('value') for e in deployment['spec']['template']['spec']['containers'][0]['env']}
        assert env.get('STRICT_VERIFY')=='true' and env.get('CATTLE_CA_CHECKSUM')
        result=api.call('/k8s/clusters/'+cid+'/api/v1/namespaces/demo/pods')
        assert result['items']==[]
        print('PASS: '+name+' strict-TLS agent and real admin request through Rancher proxy; demo empty',flush=True)
        assert subprocess.check_output(k+['auth','can-i','*','*'],text=True).strip()=='yes'
        # Test native Kubernetes SA authentication without persisting or printing the token.
        token=subprocess.check_output(k+['-n','demo','create','token','default','--duration=10m'],text=True).strip()
        config=json.loads(subprocess.check_output(k+['config','view','--raw','--minify','-o','json']))['clusters'][0]['cluster']
        ctx=ssl.create_default_context(cadata=base64.b64decode(config['certificate-authority-data']).decode())
        body=json.dumps({'apiVersion':'authentication.k8s.io/v1','kind':'SelfSubjectReview'}).encode()
        req=urllib.request.Request(config['server']+'/apis/authentication.k8s.io/v1/selfsubjectreviews',data=body,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req,context=ctx,timeout=20) as response: identity=json.load(response)
        assert identity['status']['userInfo']['username']=='system:serviceaccount:demo:default'
        print('PASS: '+name+' native admin and actual ServiceAccount authentication preserved',flush=True)
        summary={'name':name,'id':cid,'state':c['state'],'conditions':[{k:v for k,v in x.items() if k in ('type','status')} for x in c.get('conditions',[])],'agentImage':deployment['spec']['template']['spec']['containers'][0]['image'],'strictTLS':True,'proxyReadPassed':True,'nativeServiceAccountAuthPassed':True}
        (ROOT/f'artifacts/step-06/{name}-verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print('PASS: setup API session logged out')

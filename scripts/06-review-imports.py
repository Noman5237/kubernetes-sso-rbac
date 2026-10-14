#!/usr/bin/env python3
import hashlib,json,subprocess
from rancher_api import ROOT,BASE
for name in ('cluster-a','cluster-b'):
    raw=subprocess.check_output(['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/{name}-admin.yaml'),'create','--dry-run=client','--validate=false','-f',str(ROOT/f'secrets/rancher/imports/{name}.yaml'),'-o','json'])
    remaining=raw.decode().lstrip();items=[];summary=[]
    while remaining:
        data,end=json.JSONDecoder().raw_decode(remaining)
        items.extend(data.get('items',[data]));remaining=remaining[end:].lstrip()
    for item in items:
        kind=item['kind'];entry={'kind':kind,'name':item['metadata']['name']}
        if kind in ('ClusterRole','Role'):entry['rules']=item.get('rules')
        if kind in ('ClusterRoleBinding','RoleBinding'):
            entry['roleRef']=item['roleRef'];entry['subjects']=item['subjects']
        if kind in ('Deployment','DaemonSet'):
            spec=item['spec']['template']['spec'];entry['serviceAccountName']=spec.get('serviceAccountName');entry['hostNetwork']=spec.get('hostNetwork',False);entry['containers']=[]
            for c in spec['containers']:
                env={e['name']:e.get('value') for e in c.get('env',[]) if e['name'] in ('CATTLE_SERVER','CATTLE_CA_CHECKSUM','CATTLE_INSECURE','STRICT_VERIFY')}
                entry['containers'].append({'name':c['name'],'image':c['image'],'securityContext':c.get('securityContext',{}),'trustEnv':env})
                if 'CATTLE_SERVER' in env:assert env['CATTLE_SERVER']==BASE
                if 'CATTLE_CA_CHECKSUM' in env:
                    ca=(ROOT/'secrets/ca/ca.crt').read_bytes()
                    assert env['CATTLE_CA_CHECKSUM'] in [hashlib.sha256(ca).hexdigest(),hashlib.sha256(ca.rstrip()).hexdigest()]
            entry['volumes']=[{'name':v['name'],'type':next(k for k in v if k!='name')} for v in spec.get('volumes',[])]
        summary.append(entry)
    path=ROOT/f'artifacts/step-06/{name}-manifest-review.json';path.write_text(json.dumps(summary,indent=2)+'\n')
    print(name, json.dumps(summary,indent=2))

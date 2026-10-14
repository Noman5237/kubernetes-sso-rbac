#!/usr/bin/env python3
import json, os, time
from rancher_api import Rancher, ROOT
out=ROOT/'secrets/rancher/imports';out.mkdir(mode=0o700,exist_ok=True);out.chmod(0o700)
def save(name,data):
    fd=os.open(out/name,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'wb') as f:f.write(data)
with Rancher() as api:
    for config in json.loads((ROOT/'config/rancher/import-clusters.json').read_text()):
        name=config['name']
        matches=[c for c in api.call('/v3/clusters')['data'] if c['name']==name]
        assert len(matches)<=1, 'Duplicate cluster names'
        cluster=matches[0] if matches else api.call('/v3/clusters',config)
        cid=cluster['id']
        tokens=api.call('/v3/clusterregistrationtokens?clusterId='+cid)['data']
        token=tokens[0] if tokens else api.call('/v3/clusterregistrationtokens',{'type':'clusterRegistrationToken','clusterId':cid})
        for _ in range(30):
            token=api.call('/v3/clusterregistrationtokens/'+token['id'])
            if token.get('manifestUrl'):break
            time.sleep(2)
        manifest=api.call(token['manifestUrl'],raw=True)
        save(name+'.yaml',manifest)
        (ROOT/f'artifacts/step-06/{name}-id.txt').write_text(cid+'\n')
        print(name+': registration '+cid+'; credential-bearing manifest saved privately')

#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def run(*args): return subprocess.check_output(args,text=True)
ip=run('docker','inspect','sso-lab-gateway','--format','{{(index .NetworkSettings.Networks "kind").IPAddress}}').strip()
for cluster in ['mngmt','cluster-a','cluster-b']:
 node=f'{cluster}-control-plane'
 subprocess.run(['docker','cp',str(root/'secrets/ca/ca.crt'),node+':/usr/local/share/ca-certificates/sso-lab.crt'],check=True)
 subprocess.run(['docker','exec',node,'update-ca-certificates'],check=True,stdout=subprocess.DEVNULL)
 base=['kubectl','--kubeconfig',str(root/f'kubeconfigs/{cluster}-admin.yaml'),'-n','kube-system']
 cm=json.loads(run(*base,'get','configmap','coredns','-o','json'))
 backup=root/f'artifacts/step-03/{cluster}-coredns-before.json'
 if not backup.exists(): backup.write_text(json.dumps(cm,indent=2)+'\n')
 original=json.loads(backup.read_text())['data']['Corefile']
 block=f'    hosts {{\n        {ip} sso.lab.test rancher.lab.test\n        fallthrough\n    }}\n'
 core=original.replace('.:53 {\n','.:53 {\n'+block,1)
 patch={'data':{'Corefile':core}}
 (root/f'config/network/{cluster}-coredns-patch.json').write_text(json.dumps(patch,indent=2)+'\n')
 subprocess.run(base+['patch','configmap','coredns','--type=merge','--patch-file',str(root/f'config/network/{cluster}-coredns-patch.json')],check=True)
 subprocess.run(base+['rollout','restart','deployment/coredns'],check=True)
 subprocess.run(base+['rollout','status','deployment/coredns','--timeout=120s'],check=True)
print('Gateway IP:',ip)

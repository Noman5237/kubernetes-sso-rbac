#!/usr/bin/env python3
import json,subprocess
from rancher_api import ROOT
matrix=json.loads((ROOT/'artifacts/step-07/alice-permissions.json').read_text())
results=[]
for row in matrix:
 k=['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/alice-{row["cluster"]}.yaml'),'--request-timeout=20s']
 resource=row['resource']+('.'+row['group'] if row['group'] else '')
 args=k+['auth','can-i',row['verb'],resource]
 if row.get('namespace'):args+=['-n',row['namespace']]
 r=subprocess.run(args,capture_output=True,text=True)
 answer=r.stdout.strip()
 assert answer in ('yes','no'),r.stderr
 assert (answer=='yes')==row['expected'], str(row)
 results.append({**row,'kubectl':answer})
 print('PASS:',row['cluster'],row['verb'],resource,row.get('namespace','cluster-scope'),answer,flush=True)
for name in ('cluster-a','cluster-b'):
 k=['kubectl','--kubeconfig',str(ROOT/f'kubeconfigs/alice-{name}.yaml'),'--request-timeout=20s']
 for resource in ('pods','deployments'):
  data=json.loads(subprocess.check_output(k+['get',resource,'-n','demo','-o','json']))
  assert data['items']==[]
 r=subprocess.run(k+['get','pods','-n','kube-system'],capture_output=True,text=True)
 assert r.returncode!=0 and 'Forbidden' in r.stderr
 if name=='cluster-a':
  r=subprocess.run(k+['get','secrets','-n','demo'],capture_output=True,text=True)
  assert r.returncode!=0 and 'Forbidden' in r.stderr
 print('PASS:',name,'actual empty reads and Forbidden outside scope',flush=True)
(ROOT/'artifacts/step-08/kubectl-matrix.json').write_text(json.dumps(results,indent=2)+'\n')

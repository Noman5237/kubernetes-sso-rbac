#!/usr/bin/env python3
"""Capture real, read-only Alice commands for the narrated terminal playback."""
import json, subprocess, datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1]
checks=[('get pods -n demo',0,'No resources found'),('auth can-i create deployments -n demo',None,None),('auth can-i get secrets -n demo',None,None),('auth can-i get pods -n kube-system',1,'no'),('auth can-i get nodes',1,'no')]
records={}
for cluster in ['cluster-a','cluster-b']:
 rows=[]
 for args,code,contains in checks:
  p=subprocess.run(['kubectl','--kubeconfig',str(root/f'kubeconfigs/alice-{cluster}.yaml'),*args.split()],text=True,capture_output=True)
  out=(p.stdout+p.stderr).strip()
  expected=code if code is not None else (1 if cluster=='cluster-a' else 0)
  assert p.returncode==expected,(cluster,args,p.returncode,out)
  if contains:assert contains in out
  rows.append({'command':f'kubectl --kubeconfig kubeconfigs/alice-{cluster}.yaml '+args,'output':out,'exitCode':p.returncode})
 records[cluster]=rows
result={'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':records}
(root/'artifacts/demo/kubectl-results.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS: ten actual kubectl commands; expected allowed and denied results in both clusters')

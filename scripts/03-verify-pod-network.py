#!/usr/bin/env python3
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for cluster in ['mngmt','cluster-a','cluster-b']:
 b=['kubectl','--kubeconfig',str(root/f'kubeconfigs/{cluster}-admin.yaml'),'-n','kube-system']
 cm={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'lab-tls-probe-ca'},'data':{'ca.crt':(root/'secrets/ca/ca.crt').read_text()}}
 pod={'apiVersion':'v1','kind':'Pod','metadata':{'name':'lab-tls-probe'},'spec':{'restartPolicy':'Never','automountServiceAccountToken':False,'containers':[{'name':'probe','image':'curlimages/curl:8.12.1','command':['sh','-ec','for name in sso rancher; do curl --fail --silent --show-error --cacert /ca/ca.crt https://$name.lab.test:8443/__lab_tls_probe; done'],'volumeMounts':[{'name':'ca','mountPath':'/ca','readOnly':True}]}],'volumes':[{'name':'ca','configMap':{'name':'lab-tls-probe-ca'}}]}}
 try:
  for obj in [cm,pod]: subprocess.run(b+['apply','-f','-'],input=json.dumps(obj),text=True,check=True)
  subprocess.run(b+['wait','--for=jsonpath={.status.phase}=Succeeded','pod/lab-tls-probe','--timeout=120s'],check=True)
  subprocess.run(b+['logs','lab-tls-probe'],check=True)
  print('PASS pod DNS and TLS:',cluster,flush=True)
 finally:
  subprocess.run(b+['delete','pod/lab-tls-probe','configmap/lab-tls-probe-ca','--ignore-not-found=true','--wait=true'],check=True)

#!/usr/bin/env python3
import json,subprocess,time
from pathlib import Path
r=Path(__file__).resolve().parents[1]
url='https://sso.lab.test:8443/realms/master/.well-known/openid-configuration'
cmd=['curl','--fail','--silent','--show-error','--cacert',str(r/'secrets/ca/ca.crt'),'--resolve','sso.lab.test:8443:127.0.0.1',url]
for n in range(60):
 p=subprocess.run(cmd,capture_output=True,text=True)
 if p.returncode==0: break
 time.sleep(2)
else: raise SystemExit('FAIL: discovery not available after 120 seconds')
d=json.loads(p.stdout)
assert d['issuer']=='https://sso.lab.test:8443/realms/master'
assert d['token_endpoint'].startswith(d['issuer']+'/')
print('PASS: HTTPS discovery, issuer, token endpoint')
for c in ['mngmt','cluster-a','cluster-b']:
 p=subprocess.run(['docker','exec',c+'-control-plane','curl','-fsS',url],capture_output=True,text=True,check=True)
 assert json.loads(p.stdout)['issuer']==d['issuer']
 print('PASS: discovery from',c)
ip=subprocess.check_output(['docker','inspect','sso-lab-keycloak','--format','{{(index .NetworkSettings.Networks "kind").IPAddress}}'],text=True).strip()
p=subprocess.run(['docker','exec','mngmt-control-plane','curl','-fsS','--resolve',f'sso.lab.test:9000:{ip}','https://sso.lab.test:9000/health/ready'],capture_output=True,text=True,check=True)
assert json.loads(p.stdout)['status']=='UP'
print('PASS: Keycloak readiness UP (private management endpoint)')
sql="select count(*) from pg_stat_activity join pg_stat_ssl using(pid) where usename='keycloak' and ssl=true;"
p=subprocess.check_output(['docker','exec','sso-lab-postgres','psql','-U','postgres','-d','keycloak','-Atc',sql],text=True)
assert int(p.strip())>0
print('PASS: PostgreSQL sees encrypted Keycloak sessions')
p=subprocess.check_output(['docker','exec','sso-lab-postgres','psql','-U','postgres','-d','postgres','-Atc',"select rolsuper from pg_roles where rolname='keycloak';"],text=True)
assert p.strip()=='f'
print('PASS: Keycloak database user is not superuser')

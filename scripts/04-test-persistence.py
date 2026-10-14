#!/usr/bin/env python3
import subprocess
from pathlib import Path
r=Path(__file__).resolve().parents[1]
admin_name='recovery-admin' if (r/'secrets/keycloak/recovery-password').exists() else 'lab-admin'
def state():
 return subprocess.check_output(['docker','exec','sso-lab-postgres','psql','-U','postgres','-d','keycloak','-Atc',f"select id from realm where name='master'; select id from user_entity where username='{admin_name}';"],text=True).strip()
before=state()
assert len(before.splitlines())==2
subprocess.run([str(r/'scripts/04-compose.sh'),'stop','keycloak'],check=True)
subprocess.run([str(r/'scripts/04-compose.sh'),'restart','postgres'],check=True)
subprocess.run([str(r/'scripts/04-compose.sh'),'up','-d','--force-recreate','keycloak'],check=True)
subprocess.run([str(r/'scripts/04-verify-keycloak.py')],check=True)
assert state()==before
print('PASS: master realm and current recovery administrator retained after database restart and Keycloak container recreation.')

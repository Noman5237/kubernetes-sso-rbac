#!/usr/bin/env python3
from pathlib import Path
import secrets,os,shutil
r=Path(__file__).resolve().parents[1]
p=r/'secrets/keycloak/runtime.env'
if not p.exists():
 p.write_text('POSTGRES_PASSWORD='+secrets.token_hex(24)+'\nKEYCLOAK_DB_PASSWORD='+secrets.token_hex(24)+'\nKC_BOOTSTRAP_ADMIN_PASSWORD='+secrets.token_hex(24)+'\n')
 p.chmod(0o600)
for name in ['sso.crt','sso.key','postgres.crt','postgres.key']:
 shutil.copyfile(r/'secrets/tls'/name,r/'secrets/keycloak'/name)
 (r/'secrets/keycloak'/name).chmod(0o644)
shutil.copyfile(r/'secrets/ca/ca.crt',r/'secrets/keycloak/ca.crt')
(r/'secrets/keycloak/ca.crt').chmod(0o644)
(r/'secrets/keycloak').chmod(0o700)
print('Runtime credentials retained locally; not printed. TLS copies readable inside mounts; host directory restricted.')

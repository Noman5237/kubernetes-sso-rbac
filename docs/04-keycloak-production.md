# Step 4 — Login cave runs in production mode

Date: 14 October 2026.

Caveman: Keycloak checks people. PostgreSQL remembers people. Both speak through trusted certificates. No dev mode. No HA.

## What runs

- Keycloak 26.8.0, built with PostgreSQL and health support; command `start --optimized`.
- PostgreSQL 17.6, persistent named volume, separate non-superuser `keycloak` database owner.
- Existing gateway forwards SSO traffic over verified HTTPS to Keycloak.
- Keycloak verifies PostgreSQL's certificate and hostname using JDBC `sslmode=verify-full`.
- PostgreSQL is on an internal Docker network only; neither it nor Keycloak publishes a direct host port. Management port 9000 stays internal.

URL: `https://sso.lab.test:8443`. Current discovery uses the built-in `master` realm. The `kubernetes` realm, Rancher client, test users/groups, and browser login are separate later steps.

## Files

- [Compose services](../compose.keycloak.yaml): database, Keycloak, networks, mounts, runtime settings.
- [Keycloak Dockerfile](../config/keycloak/Dockerfile): immutable optimized image from digest-pinned upstream image; no credentials baked in.
- [PostgreSQL startup](../config/postgres/start.sh): installs TLS files with correct database-user ownership.
- [Database initialization](../config/postgres/init-keycloak.sh): creates application user/database on first initialization.
- [Credential/TLS preparation](../scripts/04-prepare-keycloak.py): retains generated passwords in `secrets/keycloak/runtime.env` with mode 0600; never prints them.
- [Compose wrapper](../scripts/04-compose.sh): reads runtime secrets and current gateway IP. Avoid `config` output when sharing, as Compose may resolve secrets into it.
- [Gateway route](../config/network/nginx.conf): validates backend certificate, overwrites forwarded headers; Keycloak trusts proxy headers only from the gateway IP.

The host `secrets/keycloak` directory is mode 0700. Individual mounted TLS copies are readable to the container's non-root process; the restricted parent directory protects them on the Mac. The CA private key is not copied into any service mount. Credentials are kept locally as requested; nothing was committed or pushed.

## Reproduce

From `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/03-create-certificates.sh
python3 scripts/04-prepare-keycloak.py
./scripts/04-compose.sh up -d --build postgres keycloak
docker exec sso-lab-gateway nginx -t
docker exec sso-lab-gateway nginx -s reload
./scripts/04-verify-keycloak.py
```

The certificate script now also creates `postgres.lab.test` TLS material. The preparation script preserves existing passwords. Existing PostgreSQL volumes do not rerun initialization scripts; changing an env-file password alone does not rotate a database password.

No Mac CA installation or hosts-file change. Example trusted request:

```bash
curl --cacert secrets/ca/ca.crt \
  --resolve sso.lab.test:8443:127.0.0.1 \
  https://sso.lab.test:8443/realms/master/.well-known/openid-configuration
```

Bootstrap administrator username: `lab-admin`. Password remains in the local env file. This is Keycloak's temporary bootstrap administrator; replace/remove it when configuring permanent recovery access later.

## Tests

- [Verification script](../scripts/04-verify-keycloak.py) and [results](../artifacts/step-04/verify.log): correct issuer/endpoints through trusted HTTPS; discovery from all three nodes; readiness UP; encrypted PostgreSQL sessions; database user is not superuser.
- [Persistence script](../scripts/04-test-persistence.py) and [results](../artifacts/step-04/persistence.log): stops Keycloak, restarts PostgreSQL, recreates Keycloak, then checks readiness and unchanged master-realm/bootstrap-user IDs. This is disruptive; run only deliberately.
- Production profile activation was confirmed in Keycloak's startup log. Rancher remains undeployed.

## Fix encountered

The initial bind-mounted initialization script could not execute (`bad interpreter: Permission denied`). Startup now copies it into the container and makes it non-executable so the official entrypoint sources it. The partially initialized volume was retained; the missing application role/database were initialized with `docker exec sso-lab-postgres sh /config/init-keycloak.sh`. That recovery command is not an idempotent routine setup step.

## Limits and next step

Production startup mode is not a production-ready HA installation. This is a local, single-instance lab. No application-user login or Rancher OIDC integration has been tested yet. If the gateway IP changes, recreate Keycloak through the wrapper so its trusted-proxy address updates, and rerun cluster DNS configuration.

Do not use Compose `down -v` unless intentionally deleting database contents. Stop services while preserving data with `./scripts/04-compose.sh stop keycloak postgres`.

Wait for confirmation before Rancher installation.

Sources: [Keycloak containers](https://www.keycloak.org/server/containers), [database configuration](https://www.keycloak.org/server/db), [reverse proxy](https://www.keycloak.org/server/reverseproxy), [TLS](https://www.keycloak.org/server/enabletls).

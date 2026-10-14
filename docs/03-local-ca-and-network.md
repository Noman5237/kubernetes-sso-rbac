# Step 3 — Make cave seal. Teach caves to trust seal.

Date: 14 October 2026. Result: CA/network foundation completed; all six pod endpoint tests and six node endpoint tests passed. Both host endpoints passed with explicit CA and failed without it (curl exit 60).

Caveman: CA makes seal. Two servers wear seal. Three caves trust seal. Mac trusts seal only when command explicitly points at file. No Mac CA installation.

## Endpoints

- Keycloak base URL: `https://sso.lab.test:8443`
- Planned realm issuer: `https://sso.lab.test:8443/realms/kubernetes`
- Rancher URL: `https://rancher.lab.test:8443`
- OIDC callback path is deferred until the version-specific Rancher integration is configured.

A small Docker NGINX gateway answers both names with separate certificates. It publishes only Mac loopback port 8443 and has both Docker DNS aliases on the kind network. CoreDNS hosts entries let pods resolve the gateway too. At this step only `/__lab_tls_probe` returns 200; application routes deliberately return 503 because the applications are not deployed.

No Mac hosts-file change was made. Use curl `--resolve` on the Mac. Future browser login uses a containerized browser on this network, with its own CA trust. Browser configuration and Keycloak/Rancher upstream routes are still pending.

## Files and commands

Run from `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/03-create-certificates.sh
docker compose -f compose.network.yaml up -d
./scripts/03-configure-cluster-trust.py
./scripts/03-verify-tls.sh
./scripts/03-verify-pod-network.py
```

- [Certificate script](../scripts/03-create-certificates.sh) and extensions: [SSO](../config/tls/sso.ext), [Rancher](../config/tls/rancher.ext).
- [Compose](../compose.network.yaml) and [gateway configuration](../config/network/nginx.conf).
- [Cluster trust/DNS script](../scripts/03-configure-cluster-trust.py): adds CA to each node and patches CoreDNS; backs up its previous configuration.
- [Host/node TLS checks](../scripts/03-verify-tls.sh).
- [Pod DNS/TLS checks](../scripts/03-verify-pod-network.py): creates one short-lived diagnostic pod and public CA ConfigMap per cluster in kube-system, then removes both. It mounts no ServiceAccount token. No app workloads remain.

Public CA: `secrets/ca/ca.crt`. CA private key: `secrets/ca/ca.key`. Server certificates/keys: `secrets/tls/{sso,rancher}.{crt,key}`. Retained locally as requested, not printed or pushed. Only server keys are mounted into the gateway; the CA private key never enters a container. Generated files use restrictive permissions.

CA validity is 365 days; server certificates 90 days with matching DNS SANs and serverAuth usage. The generation script preserves existing certificates; it is not a rotation script.

## Follow one request

```bash
curl --cacert secrets/ca/ca.crt \
  --resolve sso.lab.test:8443:127.0.0.1 \
  https://sso.lab.test:8443/__lab_tls_probe
```

Expected: `sso TLS OK`. Without `--cacert`, this lab certificate is rejected. No insecure flags are used.

## Evidence and boundaries

Logs: [certificates](../artifacts/step-03/certificates.log), [cluster trust](../artifacts/step-03/cluster-trust.log), [host/node TLS](../artifacts/step-03/tls-tests.log), [pod networking](../artifacts/step-03/pod-tests.log).

Node trust and successful diagnostic pod tests do not automatically configure application trust. Rancher, Keycloak, agents, and the browser need explicit trust during their deployment steps. Existing Kubernetes API CAs/authentication are unchanged.

If the gateway is recreated and its Docker IP changes, rerun the cluster trust/DNS script. Generated CoreDNS patches are in `config/network/`; backups in `artifacts/step-03/`. The script rebuilds patches from those backups; review before rerunning if CoreDNS is independently changed later.

Cleanup: stop the gateway with `docker compose -f compose.network.yaml down`; remove the lab hosts stanza using the saved CoreDNS data; remove `/usr/local/share/ca-certificates/sso-lab.crt` from each node and rerun its `update-ca-certificates --fresh`. Preserve other CAs. Keep local keys unless intentionally resetting the lab.

References: [Kubernetes DNS customization](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/), [Keycloak hostname configuration](https://www.keycloak.org/server/hostname).

## Stop

Wait for confirmation before deploying production-mode Keycloak with PostgreSQL and wiring its HTTPS upstream. Rancher and browser deployment follow separately.

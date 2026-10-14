# Kubernetes SSO and RBAC lab

Local proof of concept: **Keycloak authenticates Alice; Rancher assigns her permissions; Kubernetes enforces RBAC.**

## Demo

**[Watch the narrated demo — 2 minutes 58 seconds](demo/kubernetes-sso-rbac-demo.mp4)**

Real Keycloak and Rancher pages with callouts, followed by playback of actual kubectl results. [Transcript and chapters](artifacts/demo/transcript.md) · [Recording procedure](docs/08b-narrated-demo.md).

## Current model — Plan B

```text
Keycloak (Docker, production mode, PostgreSQL, HTTPS)
  └─ Alice identity — no Keycloak groups
      └─ Rancher (kind: mngmt)
          ├─ cluster-a / demo → lab-developer
          │                    read pods + deployments
          └─ cluster-b / demo → lab-namespace-admin
                               explicit namespaced resources

Alice dashboard + kubectl → Rancher proxy → app-cluster Kubernetes APIs
```

Three single-node kind clusters; no application workloads. Kubernetes system components and Rancher agents still run. Role templates are reusable; direct user-to-project bindings supply their scope. Native administrator and ServiceAccount authentication remain available.

[Plan B](plan-b.md) is implemented through Step 8. [Plan A](plan.md) is the separate direct Kubernetes OIDC alternative. [Current TODO](todo.md).

## Completed and tested

- Docker allocated 16 GiB; three minimal kind clusters created.
- Local CA, fixed hostnames, production-mode Keycloak, and single-replica Rancher configured.
- App clusters imported; direct Alice role assignments configured without Keycloak groups.
- Actual Alice OIDC login, dashboard restrictions, kubectl permissions, and native administrator access verified.
- A permits reads but denies deployment creation and Secret reads. B permits those actions inside `demo`. Both deny node and `kube-system` pod access.
- Narrated demonstration recorded and exported with verified video/audio.

**Pending:** credential expiry/revocation, account and binding removal, restart/outage tests, and final cleanup instructions. Execution pauses for confirmation between steps.

## Follow the steps

| Step | Guide |
| --- | --- |
| 1 | [Helm](docs/01-install-helm.md), [Docker and versions](docs/01b-docker-and-versions.md) |
| 2 | [Three minimal clusters](docs/02-minimal-clusters.md) |
| 3 | [Local CA and networking](docs/03-local-ca-and-network.md) |
| 4 | [Keycloak in production mode](docs/04-keycloak-production.md), [Mac hostnames](docs/04b-mac-hostnames.md) |
| 5 | [Rancher installation](docs/05-rancher-install.md) |
| 6 | [Import app clusters](docs/06-import-clusters.md) |
| 7 | [Identity and direct role assignments](docs/07-identity-and-roles.md) |
| 8 | [kubectl and dashboard verification](docs/08-kubectl-and-dashboard.md) |
| Demo | [Recording and rerun procedure](docs/08b-narrated-demo.md) |

Use the ordered documents and their referenced scripts. This repository captures the current local lab; Docker volumes and running cluster state are not Git backups. Generated IDs and credentials describe that lab instance.

## Local endpoints and credentials

- Keycloak: `https://sso.lab.test:8443`
- Rancher: `https://rancher.lab.test:8443`
- Hostnames resolve to localhost on the Mac; Docker networking handles container access.
- No CA is installed in macOS or host browsers. CLI clients use explicit CA trust; the isolated demo browser trusts the lab CA inside its container.
- Local POC secrets, private keys, registration manifests, and kubeconfigs are intentionally retained in this private repository at the owner's request.
- Alice's generated kubeconfig tokens currently last **one hour**. Six-month tokens were discussed but not enabled. Regeneration replaces the matching previous lab kubeconfigs.

## Files

- `config/`, `compose.*.yaml`: declarative lab configuration.
- `scripts/`: setup, verification, and recording tools.
- `docs/`: concise procedures and observed results.
- `artifacts/`: captured test evidence and recording source material.
- `demo/`: final narrated video.
- `secrets/`, `kubeconfigs/`: retained local lab credentials.

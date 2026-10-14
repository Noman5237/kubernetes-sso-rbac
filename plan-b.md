# Plan B — Keycloak identity, Rancher authorization

Updated: 14 October 2026. Current implementation model; Steps 1–8 are complete. Credential lifecycle and outage verification remain in [TODO](todo.md). [Plan A](plan.md) remains the separate direct-Kubernetes-OIDC alternative.

## Architecture

```text
Keycloak: “This is Alice” (stable OIDC subject)
                       │
                       ▼
Rancher: resolves Alice's user record
 ├─ Alice → lab-developer       → cluster-a / demo project
 └─ Alice → lab-namespace-admin → cluster-b / demo project
                       │
                 Generated Kubernetes RBAC

Dashboard / kubectl → Rancher authentication proxy → downstream API
Direct admin / native ServiceAccounts              → downstream API
```

Keycloak authenticates users. All login admission, role definitions, and user-to-project bindings live in Rancher. No Keycloak groups or group claim mappers are used. Role definitions are reusable across projects and clusters; bindings supply the scope. Rancher supports assigning project roles directly to external users. [Project membership](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/add-users-to-projects)

## Local topology and trust

- `mngmt`: one-node kind cluster with one Helm-deployed Rancher replica and standard management controllers.
- `cluster-a`, `cluster-b`: one-node kind clusters registered with Rancher. Each contains an empty `demo` namespace plus system components/agents.
- Separate Docker Keycloak in production mode with TLS and persistent PostgreSQL, also using verified TLS.
- Docker has 16 GiB allocated. No HA, application workloads, CRD experiments, or optional monitoring/logging stacks.

Stable endpoints: `https://sso.lab.test:8443` and `https://rancher.lab.test:8443`, exposed through the Docker gateway. Mac hosts entries resolve them to loopback; Docker aliases and explicit CoreDNS entries serve containers/pods. Keycloak issuer: `/realms/kubernetes`; Rancher callback: `/verify-auth` on the Rancher URL.

A local CA signs separate certificates. Rancher and Keycloak trust explicit CA material; Rancher agents use strict verification with the CA checksum. Existing Kubernetes CAs remain intact. Rancher TLS terminates at the gateway; the backend HTTP hop stays on Docker's kind network. Keycloak's backend connection uses verified HTTPS. No CA is installed in Mac trust stores. Automated clients use an explicit CA file; trusted rendered-browser testing passed in an isolated container.

## Identity and access model

Keycloak realm `kubernetes` has Alice, `no-role`, and dedicated setup identity `rancher-admin`. Client `rancher` is confidential, uses authorization code with S256 PKCE, profile/email scopes, and a Rancher audience. Implicit/password grants and client ServiceAccounts are disabled. No group membership carries permission.

Rancher's restricted login allow-list contains Alice and the setup administrator. Newly authenticated users receive only `user-base`; login admission itself does not grant project access. `no-role` remains outside the allow-list. The dedicated setup identity is attached to the existing Rancher administrator; Alice is never used for provider enablement.

| User | Role | Scope |
|---|---|---|
| Alice | lab-developer | A/demo: get/list/watch pods and deployments |
| Alice | lab-namespace-admin | B/demo: administer explicitly listed native namespaced resources |
| no-role | None | Rancher login denied |

All assignments are in [project-members.json](config/rancher/project-members.json); permissions are in [project-roles.json](config/rancher/project-roles.json); admission is in [login-users.json](config/rancher/login-users.json). [Step 7](docs/07-identity-and-roles.md) is the executable procedure.

Direct bindings use the Rancher user ID associated with Keycloak's stable subject. A new allowed user's first login establishes that record; no directory-query role or group search is required. Permission definitions are reused, but assignments are maintained per user/project.

The namespace-admin role avoids wildcard resources because testing found Rancher promoted wildcard project permissions to cluster scope. Secrets, ServiceAccount tokens, and namespace RBAC administration in B/demo are intentional; cluster-level administration and other namespaces remain denied. New CRDs would require explicit rules.

## Verification and remaining work

Completed: fresh OIDC/PKCE Alice login without groups; direct-user bindings; permission matrix; actual permitted and forbidden proxy reads; no-role denial; native admin and ServiceAccount access; recovery login checks. Old group bindings and roles were removed; Alice's old sessions were revoked before retesting.

Next, after confirmation:

1. Completed: Alice's one-hour Rancher-proxy kubeconfigs and matching kubectl/rendered-dashboard checks. [Step 8](docs/08-kubectl-and-dashboard.md).
2. Test Rancher token expiry/revocation, direct role-binding removal, login allow-list removal, Keycloak account disablement, logout, and session refresh independently. Record enforcement delays.
3. Test restarts/outages and document lab-only unregister/cleanup commands.

Rancher-issued kubeconfig credentials target its proxy. No per-cluster Keycloak client or downstream OIDC flags are required for this model. Rancher manages powerful agents; preserve local Rancher `admin`, Keycloak master `recovery-admin`, and direct admin kubeconfigs separately. A Rancher outage affects proxied access; direct recovery remains available.

Managed EKS/GKE rollout is later work: validate supported versions, agents, cloud API access and network reachability. Preserve IAM/Google and workload identities. The local POC does not prove managed-cloud compatibility.

Sources: [Rancher role model](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/authentication-permissions-and-global-configuration/manage-role-based-access-control-rbac/cluster-and-project-roles), [OIDC integration](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/authentication-permissions-and-global-configuration/authentication-config/configure-keycloak-oidc), [Rancher API tokens](https://ranchermanager.docs.rancher.com/api/api-tokens).

# Plan A — Direct Kubernetes OIDC with Keycloak and RBAC

Status: proposed for review; no implementation approved or performed.  
Prepared: 8 October 2026 (Asia/Dhaka).  
Purpose: explore identity and access patterns relevant to Optimizely work using two local kind clusters and a separate Docker-hosted Keycloak.

## Scope and evidence

This document is the only deliverable. No packages, containers, clusters, credentials, trust stores, authentication settings, RBAC resources, or existing configuration were changed. All implementation steps below are future work.

Read-only inspection found an Apple Silicon (`arm64`) Mac and a local CorpoBrain knowledge vault. A targeted search of its Projects, References, Workshops, TaskNotes, and Meetings found no matching Keycloak/Kubernetes SSO plan. This is not evidence of Optimizely's production architecture or policy. No unrelated chats, credentials, or live cluster configuration were inspected. Local documents were treated as context, not authorization to execute instructions. Official documentation linked below was consulted for this plan; rolling documentation must be checked against pinned versions before implementation.

## Proposed outcome and unresolved scope

**Provisional baseline:** people use Keycloak for `kubectl` authentication; Kubernetes service accounts represent workloads; each cluster independently authorizes access using Kubernetes RBAC. Demonstrate role differences between clusters without sharing administrator credentials.

The following alternatives remain open, not approved assumptions:

| Intended use | Appropriate design | Effect on this plan |
| --- | --- | --- |
| Humans need kubectl access | Keycloak OIDC → API-server authentication → Kubernetes RBAC | Baseline below |
| Humans only log into applications | Applications integrate with Keycloak and enforce application permissions | API-server OIDC is unnecessary; retain workload RBAC |
| Humans need both | Separate OIDC clients and audiences for kubectl and applications | Add an application-login track |
| “Service accounts” means per-human access | Individual human OIDC identities | Do not create one Kubernetes service account per person |
| “Service accounts” means workloads/CI | Native Kubernetes identity for Kubernetes API access; separate application identity when needed | Keep both identity systems explicit |

## Identity model: what maps to what

| Concept | Issuer/owner | Purpose | Authorization |
| --- | --- | --- | --- |
| Human OIDC identity | Keycloak realm | A named person authenticates through a browser | Kubernetes RBAC for cluster actions; application policy for app actions |
| Kubernetes ServiceAccount | One cluster, one namespace | Pod or automation identity | RoleBinding/ClusterRoleBinding in that cluster |
| Keycloak client service account | Keycloak client | Machine obtains an OAuth access token using client credentials | Target application's permissions; no automatic Kubernetes grant |
| Keycloak role/group | Keycloak | Entitlement that can be emitted as a token claim | Does nothing to Kubernetes unless explicitly mapped and bound |
| Kubernetes Role/ClusterRole | Kubernetes | Allowed API verbs and resources | Binding connects permissions to User, Group, or ServiceAccount subjects |

Kubernetes service account names take the form `system:serviceaccount:<namespace>:<name>`. Identically named accounts in the two clusters remain separate identities. Use short-lived projected tokens for pods and TokenRequest where appropriate for external automation. Do not create legacy permanent token Secrets. [Kubernetes service accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)

Keycloak client service accounts receive access tokens, with effective roles constrained by assignments and client scopes. They are not Kubernetes ServiceAccount objects. There is no automatic role synchronization or identity conversion. [Keycloak service accounts](https://www.keycloak.org/docs/latest/server_admin/index.html#_service_accounts)

Do not map an external username into `system:serviceaccount:...`, grant `system:masters`, or use impersonation as an identity bridge. If Kubernetes-token-to-Keycloak federation is an actual requirement, make it a separate experiment: verify support in the pinned Keycloak version, both cluster issuers/JWKS, audience restrictions, subject allowlists, and credential lifecycle before selecting a mechanism. Do not assume arbitrary Kubernetes JWTs can be exchanged for Keycloak tokens.

## Proposed architecture

```text
Mac browser + kubectl OIDC credential helper
        | browser login / authorization code + PKCE
        v
Docker: Keycloak, realm optimizely-lab
        | signed ID token for the selected cluster client
        +------------------------+------------------------+
                                 |                        |
                            kind lab-a                kind lab-b
                            API server                API server
                            audience A                audience B
                                 |                        |
                            local RBAC                local RBAC
                                 |                        |
                            namespace demo            namespace demo
                            SA demo-reader            SA demo-reader

Each API server fetches discovery/JWKS over trusted HTTPS.
Each workload's native Kubernetes token stays on its own cluster path.
Optional application login and machine-to-app tokens are separate paths.
```

Proposed inventory: two single-control-plane clusters (`lab-a`, `lab-b`), one independent Keycloak container, one test namespace and minimal workload per cluster. Add workers only if scheduling becomes part of the experiment. Use synthetic users and data. The shared Docker host is a lab boundary, not production tenant isolation.

Use one realm initially and distinct public clients `k8s-lab-a` and `k8s-lab-b`. A browser session may provide SSO across clients, while authorization stays cluster-specific. Keep Keycloak outside the clusters so rebuilding either cluster does not remove the identity provider. Pin kind, its supported Kubernetes node image/digest, Keycloak, kubectl, and the credential helper after compatibility review. Ensure images support ARM64. [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/), [Keycloak containers](https://www.keycloak.org/server/containers)

## Networking, issuer, and trust

Proposed canonical issuer: `https://sso.lab.test:8443/realms/optimizely-lab`. This is an illustrative local name, not an existing endpoint.

Use the same issuer string in tokens, discovery, both API-server configurations, and credential-helper settings. Set Keycloak's full hostname URL explicitly; hostname configuration does not itself create DNS, publish ports, or enable TLS. Prefer direct Keycloak HTTPS for the first experiment. [Keycloak hostname](https://www.keycloak.org/server/hostname), [Keycloak TLS](https://www.keycloak.org/server/enabletls)

Proposed routing, to validate before creating clusters:

| Caller | Proposed route to sso.lab.test:8443 | Trust required |
| --- | --- | --- |
| Mac browser/helper | Local name resolves to 127.0.0.1; Docker publishes Keycloak 8443 on loopback | Browser/system trust as needed; explicit helper CA support |
| Both kind control-plane nodes | Keycloak shares the nodes' Docker network with alias sso.lab.test; internal listener also 8443 | CA available inside each API-server container |
| Optional application pods | Explicit cluster DNS forwarding/record to a reachable Keycloak endpoint | Application runtime CA bundle |

This split DNS proposal preserves one hostname and port while allowing different routes. Docker aliases are not automatically Kubernetes pod DNS records. Host `/etc/hosts` entries do not propagate into containers. `localhost` inside a node refers to that node. Docker Desktop uses a VM/networking layer; do not assume the Mac can reach container IPs directly. [Docker Desktop networking](https://docs.docker.com/desktop/features/networking/)

Select a local CA and a certificate with `sso.lab.test` in its DNS SAN. Keep the CA private key out of containers and version control. Mount only the public CA into API servers; the Keycloak server key belongs only with Keycloak. Trust for Kubernetes API certificates remains separate from issuer trust. Never bypass TLS validation to make the lab pass.

Plan distinct loopback API ports, provisionally 16443 and 26443, after checking conflicts. Both API servers need discovery and JWKS connectivity at startup and after restart/key rotation. kind host-to-node mounts and kubeadm API-server volume configuration are separate layers; plan both for the authentication file and CA. Validate the chosen kubeadm schema against the node image. [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/)

## Claims and cluster access contract

Propose Authorization Code with PKCE and a maintained kubectl exec credential helper; choose and review the helper before installation. No password grant, embedded shared client secret, or manual token arguments in shell history. Use narrowly registered loopback callbacks matching the helper. Keycloak exposes standard discovery, authorization, token, and certificate endpoints. [Keycloak OIDC endpoints](https://www.keycloak.org/securing-apps/oidc-layers)

For Kubernetes, use the human ID token. Map `sub` to username with prefix `keycloak:` and a flat string-array claim `k8s_roles` to groups with prefix `keycloak:`. Require the configured HTTPS issuer and cluster-specific audience. Prefer structured `AuthenticationConfiguration` if supported by the pinned Kubernetes release; otherwise use the documented OIDC flags. Never configure both mechanisms together. Existing signed tokens can remain usable until expiration after logout or role removal. [Kubernetes authentication](https://kubernetes.io/docs/reference/access-authn-authz/authentication/)

Propose client-scoped Keycloak roles `lab-a-viewer`, `lab-a-operator`, `lab-b-viewer`, and `lab-b-operator`. Configure a mapper to emit only the applicable client's effective roles into `k8s_roles` **in the ID token**. Do not assume nested default access-token role claims appear there. Inspect each token's audience: an access token does not necessarily contain its requesting client ID as audience. [Keycloak role and audience mapping](https://www.keycloak.org/docs/latest/server_admin/index.html#_role_mappings)

| Cluster | Effective Kubernetes group | Proposed binding in demo | Intended permission |
| --- | --- | --- | --- |
| lab-a | keycloak:lab-a-viewer | RoleBinding → demo-viewer | get/list/watch pods and deployments |
| lab-a | keycloak:lab-a-operator | RoleBinding → demo-operator | Viewer plus get/update/patch deployments/scale |
| lab-b | keycloak:lab-b-viewer | RoleBinding → demo-viewer | Same read scope, only lab-b |
| lab-b | keycloak:lab-b-operator | RoleBinding → demo-operator | Same scale scope, only lab-b |
| Each cluster | ServiceAccount demo/demo-reader | RoleBinding → demo-pod-reader | get/list pods in its own demo namespace |

Use custom narrow Roles. Exclude Secrets, pod exec, workload creation, RBAC edits, token minting, impersonation, and cluster-wide administration. Kubernetes RBAC is additive; absence of a grant denies an action, and another binding can broaden access. A RoleBinding limits namespaced permissions to its namespace. [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

Separate audiences prevent replay of a token intended for A into B; they do not prevent a user from requesting B's client token. B must still deny unauthorized operations through RBAC. Do not give either token both cluster audiences. Proposed test users: A-only viewer; A operator plus B viewer; authenticated user with no lab roles.

## Workload and application alternatives

Baseline workloads call their own Kubernetes API with their own ServiceAccount. Disable automatic token mounting where API access is unnecessary; explicitly project tokens where needed and let clients reload rotated credentials. Test resource deletion and token expiration, not only successful calls. [Configure service accounts for pods](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)

For CI running outside a cluster, first decide how it authenticates to request short-lived credentials. TokenRequest is not a solution to bootstrap authentication by itself. Keep permissions and credentials separate per cluster; do not export kind administrator kubeconfigs to CI.

If a workload calls a Keycloak-protected application, it may additionally use a distinct confidential Keycloak client with minimal application roles and an application-specific access-token audience. That identity does not inherit its Kubernetes RBAC. Secret storage/rotation or a supported credential-free federation design becomes a separate decision. Client-credentials access tokens are not a drop-in replacement for the baseline human ID-token flow.

If humans need application login only, create application clients and implement application authorization instead of configuring API-server OIDC. For both use cases, keep client IDs, audiences, callbacks, and application roles distinct from kubectl clients.

## Phased implementation proposal

| Phase | Future work | Exit evidence |
| --- | --- | --- |
| 0 — Scope and compatibility | Answer review questions; inspect installed versions, Docker resources and free ports read-only; select pinned ARM64-compatible versions and helper | Reviewed inventory, role matrix, and version table |
| 1 — Network and issuer | Design explicit name resolution; prepare lab-only certificates/trust; deploy Keycloak with persistent storage and stable URL | Trusted discovery/JWKS from Mac and a node-equivalent Docker network context |
| 2 — Realm and claims | Create synthetic users, separate clients, roles, PKCE/callback settings, and narrow claim mappers | Redacted claim fixtures match issuer, audience, subject, and role contract |
| 3 — Clusters | Create lab-a first with API-server auth/CA mounts, then lab-b with distinct audience and API port | Both API servers healthy; discovery works from actual control planes |
| 4 — RBAC and human access | Add demo namespaces and narrow Roles/Bindings; prepare separate user kubeconfigs | Real OIDC user sessions pass allowed and denied tests |
| 5 — Workload identities | Add per-cluster ServiceAccounts and minimal pods; optional app/CI track only after scope decision | Native token rotation, namespace and cross-cluster denial demonstrated |
| 6 — Failure and recovery | Test expiry, role removal, restart, key rotation, outage, and explicit cleanup procedure | Completed evidence matrix with observed revocation delay and limitations |

Keep kind bootstrap administrator kubeconfigs separate from OIDC test kubeconfigs. Use explicit context and kubeconfig selection throughout. Proposed persistence is a lab-only Keycloak data volume with a reproducible realm definition; decide between embedded development storage and a separate PostgreSQL container before implementation. A more representative database adds a container beyond the original topology. Neither choice makes this a production deployment. [Keycloak container guidance](https://www.keycloak.org/server/containers)

## Verification checklist for implementation

All boxes are intentionally unchecked; none of these runtime checks has been performed.

- [ ] Version matrix, ARM64 compatibility, CPU/memory/disk budget, and port availability recorded.
- [ ] Identical issuer and trusted TLS verified from Mac, both API servers, and optional application pods; wrong CA/SAN fails.
- [ ] Discovery and advertised JWKS URLs resolve after container and Docker restarts.
- [ ] Human login uses PKCE; callback restrictions, token refresh, and local cache protection verified.
- [ ] Sanitized ID-token fields show correct issuer, audience, expiry, immutable subject, and string-array role claim; no raw JWTs saved.
- [ ] A-only viewer reads allowed resources in A but cannot mutate, read Secrets, exec, or access another namespace.
- [ ] A operator can scale the demo deployment but cannot edit its pod template or RBAC; B viewer remains read-only.
- [ ] Authenticated no-role user cannot access demo resources; default discovery permissions are not mistaken for a data-access grant.
- [ ] A token presented directly to B fails authentication because of audience; a freshly obtained B token without B roles fails authorization.
- [ ] Expired, incorrectly signed, and wrong-issuer tokens fail authentication.
- [ ] Actual user `auth whoami`, `auth can-i`, and real API requests agree. Admin `--as` tests alone do not establish OIDC success.
- [ ] ServiceAccount can read only intended resources; same-named account in the other cluster gains no access; cross-cluster token replay fails.
- [ ] Projected token rotation works and pods without API needs have no token mount.
- [ ] Role removal and logout measured against already-issued token expiry; fresh tokens lose removed entitlements. Record the observed delay.
- [ ] Keycloak outage blocks new login/refresh; observe existing-token behavior with cached signing keys rather than assuming immediate denial.
- [ ] Signing-key rotation and API-server restart recover with valid discovery/JWKS and CA trust.
- [ ] Recovery access works only through the separately protected bootstrap credential; no test uses admin accidentally.
- [ ] Evidence contains request outcomes and sanitized identities only; no tokens, passwords, private keys, or secret-bearing exports.
- [ ] Cleanup inventory names only lab clusters, containers, volumes, DNS/trust entries, helper caches, and kubeconfig files; preserve unrelated Docker and Kubernetes resources.

## Decisions and essential questions for later review

1. Do people need **kubectl access, application login, or both**? Baseline assumes kubectl only for planning.
2. Do service accounts represent **pods, external CI, machine-to-application clients, or per-human access**? If direct Kubernetes-to-Keycloak federation is desired, what target API should the resulting token access?
3. What should the two clusters represent, and which people should read or change which namespaces? The viewer/operator matrix is illustrative.
4. Is a lab-only local CA/name-resolution setup acceptable, and should Keycloak be disposable or persist across cluster rebuilds? Is a PostgreSQL container in scope?

No blocker prevents reviewing this plan. Implementation remains gated on those scope decisions, version compatibility, and proving issuer reachability/trust from all required network contexts. No production Optimizely identity integration is assumed.

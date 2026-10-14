# Kubernetes authentication and authorization POC — Plan B TODO

Updated: 14 October 2026. Execution has started; pause for user confirmation after each step.

- [x] Install Helm and verify its local CLI: `v4.3.0+gbec5b06`. [Step 1a record](docs/01-install-helm.md). Remaining compatibility and deployment tasks below are pending.

This checklist tracks [Plan B](plan-b.md): Keycloak identity plus direct user-to-role bindings in Rancher, without Keycloak groups. [Plan A](plan.md) remains a separate design.

## Scope

Three minimal kind clusters, each with one control-plane node and no workers:

```text
kind: mngmt     → Rancher installed with Helm, one server replica
kind: cluster-a → no application workloads; RBAC tests only
kind: cluster-b → no application workloads; RBAC tests only
Docker         → separate Keycloak instance
```

No HA, sample applications, custom CRDs, or dashboard extensions. Kubernetes system components and Rancher registration agents/controllers still run; the app clusters are empty of application workloads, not system pods. Roles and RoleBindings grant access; namespaces and Rancher role assignments support the tests.

- [x] Start Docker and validate core version pins plus local Rancher chart rendering. [Step 1b](docs/01b-docker-and-versions.md). Docker memory allocation is now complete; remaining service-image pins are pending.

- [x] Allocate Docker 16 GiB and verify three minimal clusters. [Step 2](docs/02-minimal-clusters.md).

## 1. Create baseline clusters

- [ ] Pin compatible ARM64 versions of kind/Kubernetes, Rancher/agents, Helm, Keycloak, and kubectl; check Mac resources and free ports.
- [x] Create `mngmt`, `cluster-a`, and `cluster-b` as single-node kind clusters without direct Keycloak OIDC configuration.
- [x] Keep separate direct administrator kubeconfigs and verify baseline API access to all three clusters.
- [x] Create empty `demo` namespaces in A/B; deploy no application workloads.

## 2. Configure lab-only CA and networking

- [x] Create TLS test gateway, configure CA trust in all three nodes and pod DNS, and verify trusted/rejected connections. [Step 3](docs/03-local-ca-and-network.md). Application/agent/browser trust and callback configuration below remain pending.

- [x] Configure Mac hosts entries for `sso.lab.test` and `rancher.lab.test`; verify Keycloak hostname access. No CA installed on Mac. [Step 4b](docs/04b-mac-hostnames.md).
- [x] Finalize stable HTTPS URLs, DNS, port 8443, and exact Rancher `/verify-auth` callback; actual OIDC login passed.
- [x] Create a local CA and separate server certificates; retain private keys locally outside containers. No commit/push performed.
- [x] Configure public CA trust in all three kind node environments, Keycloak, Rancher, and Rancher agents; existing Kubernetes CAs preserved.
- [x] Configure Rancher's outbound Keycloak trust and private-CA/strict agent verification. Rancher-to-Keycloak and actual downstream strict-TLS agent connections passed.
- [x] Use an isolated containerized browser with lab CA trust; no CA installation in macOS Keychain, system bundles, or host-browser trust stores.
- [x] Use explicit CA files or kubeconfig CA data for Mac CLI clients; never disable TLS verification.
- [x] Verify browser-to-Rancher/Keycloak, Rancher-to-Keycloak, and app-cluster-agent-to-Rancher DNS/TLS connectivity. Node trust/Docker DNS does not automatically configure pods.

## 3. Deploy Rancher and Keycloak

- [x] Deploy Keycloak separately in Docker in production mode (`start --optimized`), with PostgreSQL, persistent lab data, fixed hostname, and CA-signed HTTPS. Credentials retained locally. [Step 4 and tests](docs/04-keycloak-production.md).
- [x] Install Rancher with Helm in `mngmt`, one replica with standard management controllers, HTTPS exposure, strict agent TLS, and retained bootstrap credentials. [Step 5 and tests](docs/05-rancher-install.md). Permanent recovery login setup remains in the identity step.
- [x] Review registration manifests and import A/B; both Active with healthy cluster agents, Fleet agents, and webhooks. No optional application stacks installed. [Step 6 and tests](docs/06-import-clusters.md).
- [x] Recheck direct administrator access to all three clusters; verify actual native ServiceAccount authentication in A/B. API-server authentication settings unchanged. Step 6 passed.

## 4. Configure identity and permissions

- [x] Create Keycloak realm `kubernetes` and a Rancher OIDC client with identity-only claims, exact callback, S256 PKCE, and protected client secret; no group mappers.
- [x] Create Alice and a no-role test user; remove obsolete POC groups/memberships and group-claim mappers. Preserve stable user IDs.
- [x] Enable Keycloak login with Rancher `restricted` admission (project/cluster members plus explicitly allowed users), minimal user-base default, and protected recovery access.
- [x] Create one Rancher demo project per app cluster containing only `demo`.
- [x] Define reusable `lab-developer` and `lab-namespace-admin` roles. Use explicit namespaced resources; avoid wildcard promotion, global admin, and Cluster Owner.
- [x] Bind Alice directly to `lab-developer` in A/demo and `lab-namespace-admin` in B/demo. Remove old group bindings/roles and verify Rancher-generated User bindings in Kubernetes.

Rebuilt Step 7 with direct user bindings; fresh OIDC/PKCE login without groups, permission matrix, no-role denial, and recovery checks passed. [Step 7](docs/07-identity-and-roles.md). Full kubectl/dashboard and lifecycle steps remain below.

## 5. Verify permissions without deploying applications

- [x] Obtain Alice's Rancher-generated kubeconfigs for A/B; verify proxy endpoints, correct contexts, short token lifetimes, and CA trust. Keep recovery credentials separate.
- [x] Use actual Alice credentials with `kubectl auth can-i` for get/list pods, create/delete deployments, read Secrets, change RBAC, and cluster-wide actions in each context. Compare results to the reviewed role matrix.
- [x] Test outside `demo` and as the no-role user; distinguish Rancher login denial from cluster authorization denial.
- [x] Make permitted read/list requests against empty resource collections; an empty list is a successful authorized request. Verify forbidden reads return denial.
- [x] Confirm matching dashboard access and restrictions. Do not create workloads merely to test write permissions; use authorization checks for those verbs.
- [x] Verify Alice receives no unintended access to `mngmt`, and direct administrator access remains functional.

Completed with actual Alice kubeconfigs and an isolated trusted Chromium browser. [Step 8 and evidence](docs/08-kubectl-and-dashboard.md).

## Demo recording

- [x] Record a narrated walkthrough of Keycloak identity, reusable Rancher roles, direct project bindings, Alice dashboard access, and actual kubectl results. [Video procedure and evidence](docs/08b-narrated-demo.md). Duration: 2 minutes 58 seconds. Roles unchanged; one-hour kubeconfigs refreshed for the demo.

## 6. Verify credential lifecycle and finish

- [x] Test Rancher token expiry/revocation, Keycloak account disablement, direct Rancher user-role binding removal, login allow-list removal, and logout independently; record enforcement observations and bounds. [Step 9](docs/09-credential-lifecycle.md).
- [ ] If needed for rollout, test long-duration OIDC refresh/resync and browser single logout; the Step 9 existing-token observation windows were 20 seconds.
- [ ] Test Rancher/Keycloak restart and outage behavior, preserving direct recovery access.
- [ ] Verify invalid TLS trust fails and Mac trust stores remain unchanged.
- [ ] Save sanitized permission results and lab-only cleanup/unregistration steps; exclude tokens, client secrets, keys, and registration credentials.

Managed EKS/GKE rollout, workload identity tests, custom-resource UI, and HA are outside this minimal POC.

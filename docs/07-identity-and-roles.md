# Step 7 — Keycloak names person. Rancher gives access.

Updated: 14 October 2026. This replaces the previous group-based Step 7. Status: configured and tested.

## Model

```text
Keycloak: Alice's stable user ID
                │ OIDC login (authorization code + PKCE)
                ▼
Rancher: Alice's user record
 ├─ user binding → lab-developer       → cluster-a / project demo
 └─ user binding → lab-namespace-admin → cluster-b / project demo
                │
                ▼
Rancher creates Kubernetes Roles/ClusterRoles and bindings
```

No groups in the POC Keycloak realm. No group claim mappers. No group-based Rancher bindings. Keycloak handles identity/passwords; Rancher owns login admission, role definitions, and user-to-project assignments. Kubernetes API-server authentication remains unchanged.

A role says **what**. A binding says **who and where**. Both role definitions are reusable across clusters; their names contain no cluster name.

## Start or rerun this procedure

From `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/07-keycloak-identity.py
./scripts/07-enable-rancher-oidc.py
./scripts/07-rancher-roles.py
./scripts/07-verify-identity-model.py
./scripts/07-verify-identity.py
./scripts/07-verify-bindings.py
./scripts/07-keycloak-recovery.py
./scripts/02-verify-clusters.sh
```

1. **Make identities.** [Realm](../config/keycloak/realm.json), [client](../config/keycloak/rancher-client.json), and [identity script](../scripts/07-keycloak-identity.py) create/reuse `alice`, `no-role`, and privileged setup identity `rancher-admin`. Existing IDs/passwords are preserved. The script removes the two old lab groups, group mappers, and unnecessary directory-query grants.
2. **Connect login.** [OIDC config](../config/rancher/oidc.json) and [enable script](../scripts/07-enable-rancher-oidc.py) configure confidential-client login with required S256 PKCE. Callback: `https://rancher.lab.test:8443/verify-auth`. Access-token audience: `rancher`; default scopes: profile/email. [Login users](../config/rancher/login-users.json) lists Alice and the setup administrator. Admission alone grants no project permission; new users receive only `user-base`.
3. **Assign access in Rancher.** [Role definitions](../config/rancher/project-roles.json) define permissions. [Project members](../config/rancher/project-members.json) contains the entire user/role/cluster/project assignment table. [Apply script](../scripts/07-rancher-roles.py) creates reusable roles and user bindings, and retires the old group bindings and cluster-named roles. No hand-written downstream RBAC is applied.
4. **Test the result.** [Model checks](../scripts/07-verify-identity-model.py) prove groups are absent and bindings point to Alice. [Permission tests](../scripts/07-verify-identity.py) use fresh real Alice OIDC credentials. [Binding checks](../scripts/07-verify-bindings.py) inspect Rancher-generated Kubernetes User subjects and project boundaries.
5. **Keep recovery.** Local Rancher `admin` remains usable. [Recovery script](../scripts/07-keycloak-recovery.py) creates/verifies Keycloak master `recovery-admin` and removes temporary bootstrap `lab-admin` if present.

For migration from the previous setup, [reset Alice sessions](../scripts/07-reset-alice-sessions.py) was run once before verification. It revokes Alice's old Rancher and Keycloak sessions, preserving administrator sessions. Existing browser logins as Alice must sign in again.

The first OIDC setup login attaches its identity to the local Rancher administrator. We use `rancher-admin`, never Alice. When a new allowed user has no Rancher record, the assignment script performs that user's first real OIDC login, then binds the resulting `userId`. This avoids requiring Keycloak directory-search permissions. The stable OIDC subject identifies Alice; the display name is not the security key.

## Current assignments and tests

| User | Reusable role | Binding scope |
|---|---|---|
| Alice | lab-developer | cluster-a / demo project / demo namespace |
| Alice | lab-namespace-admin | cluster-b / demo project / demo namespace |
| no-role | None | Rancher site login denied |

| Action | A/demo | B/demo |
|---|---|---|
| Read pods/deployments | Allow | Allow |
| Create/delete deployments | Deny | Allow |
| Read Secrets / create RoleBindings | Deny | Allow |
| Read kube-system pods | Deny | Deny |
| Read/create nodes | Deny | Deny |
| Create PVs/storage classes/API services | Deny | Deny |
| Create ClusterRoleBindings | Deny | Deny |

Fresh Alice login, the full matrix, real allowed/forbidden reads, no-role denial, and local Rancher recovery login passed. No application workloads were created. Alice has only the global `user-base` role and cannot see `mngmt` in the Rancher cluster list. Both demo projects contain only namespace `demo`.

Evidence: [model](../artifacts/step-07/identity-model.log), [permissions](../artifacts/step-07/verify.log), [matrix](../artifacts/step-07/alice-permissions.json), [assignments and IDs](../artifacts/step-07/assignments.json), [bindings](../artifacts/step-07/bindings.log).

The B role explicitly lists native namespaced resources. Do not replace that list with wildcard resources: earlier tests showed Rancher promotes some wildcard permissions to cluster scope. B intentionally permits Secrets, ServiceAccount tokens, and RBAC changes within `demo`. It is not Cluster Owner or Project Owner. Custom CRDs require an explicit reviewed rule.

## Where to look

- **Keycloak → kubernetes → Users → alice:** identity details; Groups is empty.
- **Rancher → Users & Authentication → Role Templates → Project:** `lab-developer` and `lab-namespace-admin`.
- **Rancher → cluster-a or cluster-b → demo project → Members:** Alice directly assigned to the corresponding role; local admin remains Project Owner.

Password files remain under `secrets/keycloak/`: `alice-password`, `no-role-password`, `rancher-admin-password`, `recovery-password`. Local Rancher admin password is `secrets/rancher/admin-password`. They remain mode 0600; none are in the config JSON. No passwords were rotated during this model change.

No Mac CA was installed. Automated tests use the explicit CA file and real authorization-code/PKCE flow; rendered dashboard testing is still pending. Full kubectl verification and credential lifecycle/outage tests are the next steps. Stop and wait for confirmation.

Sources: [Rancher direct user/project assignments](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/add-users-to-projects), [login admission](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/authentication-permissions-and-global-configuration/authentication-config), [Keycloak Admin REST API](https://www.keycloak.org/docs-api/latest/rest-api/index.html).

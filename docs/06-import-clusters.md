# Step 6 — Two caves join Rancher

Date: 14 October 2026. Status: complete. Both clusters Active; all checks passed.

Caveman: Rancher sends agent into each cave. Agent phones home through HTTPS. Rancher now sees both caves. Alice gets no permissions yet.

## Code and flow

Run from `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/06-prepare-imports.py
./scripts/06-review-imports.py
./scripts/06-apply-imports.sh
./scripts/06-verify-imports.py
```

1. [Cluster definitions](../config/rancher/import-clusters.json) name A/B. [Prepare](../scripts/06-prepare-imports.py) creates or reuses registration entries through Rancher's API and downloads manifests with verified HTTPS.
2. [Review](../scripts/06-review-imports.py) parses manifests without applying them. It checks the Rancher URL and CA checksum, then saves summaries without Secret data.
3. [Apply](../scripts/06-apply-imports.sh) uses each cluster's separate direct admin kubeconfig. No kubeconfig default is changed.
4. [Verify](../scripts/06-verify-imports.py) waits for Active, checks strict TLS, performs real proxy requests, and checks native admin/ServiceAccount access.

[API helper](../scripts/rancher_api.py) reads the saved local admin password and CA file. Its temporary login session is explicitly logged out. Rancher applies its configured login-session TTL rather than the requested one-hour TTL; logout is the cleanup mechanism. Initial test sessions were removed; existing browser sessions were preserved.

## Manifest review

Each manifest creates a namespace, management ServiceAccount/credential Secret, agent Deployment and Service, and cluster-level RBAC:

- `cattle-admin` grants wildcard API and non-resource permissions to `cattle-system:cattle`. Rancher needs powerful management access to implement downstream administration and impersonation.
- `proxy-clusterrole-kubeapiserver` grants access to node proxy/metrics/log endpoints for the `kube-apiserver` identity.
- Agent image: `rancher/rancher-agent:v2.15.2`. Rancher manages the agent Deployment after registration.
- Agent URL: `https://rancher.lab.test:8443`; `STRICT_VERIFY=true`; CA checksum matches our public lab CA. No insecure TLS option is enabled.
- The agent mounts its registration Secret. No CA private key is copied into either cluster.

These are Rancher's management permissions. They are not Alice's future developer/admin permissions.

Review records: [A](../artifacts/step-06/cluster-a-manifest-review.json), [B](../artifacts/step-06/cluster-b-manifest-review.json). Full credential-bearing manifests remain in `secrets/rancher/imports`, mode 0600 inside directory 0700. Do not paste or commit them.

Rancher may automatically deploy its webhook and Fleet agents in system namespaces. These are management components. The `demo` namespaces remain empty of application workloads.

## Checks

The test performs a real read through `/k8s/clusters/<id>/api/v1/namespaces/demo/pods` using the local Rancher administrator. Empty list means success. This verifies the proxy path, not Alice's authorization.

It also creates a short-lived TokenRequest for the existing `demo/default` ServiceAccount and sends a real `SelfSubjectReview` directly to Kubernetes. The token stays in process memory, is not printed or saved, and expires after its requested ten-minute lifetime. No ServiceAccount role grant or application pod is needed.

[Results](../artifacts/step-06/verify.log) and per-cluster summaries are saved under `artifacts/step-06` without credentials.

Final checks: A/B are Active; cluster agents, Fleet agents, and webhooks are available; strict-TLS proxy reads and actual native ServiceAccount authentication passed; direct admin access to all three clusters passed; both `demo` namespaces remain empty.

## Stop here

Next: configure Keycloak identities/client and direct Rancher user-role bindings. No OIDC connection, Alice role assignment, or user permission test is part of this step. Native API-server authentication is unchanged; Mac CA stores are unchanged.

Sources: [Rancher cluster registration](https://ranchermanager.docs.rancher.com/v2.12/how-to-guides/new-user-guides/kubernetes-clusters-in-rancher-setup/register-existing-clusters), [private CA configuration](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/resources/add-tls-secrets). Registration resource fields and returned manifests were checked against the running Rancher 2.15.2 API.

# Step 8 — Same Alice, same rules, two doors

Date: 14 October 2026. Status: complete. kubectl and rendered-browser checks passed.

Caveman: Alice logs in once. Rancher gives short-lived kubeconfig. Terminal and browser ask same guards.

## Get fresh kubeconfigs

From `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/08-generate-kubeconfigs.py
./scripts/08-verify-kubectl.py
```

[Generator](../scripts/08-generate-kubeconfigs.py) performs Alice's real Keycloak authorization-code/PKCE login and calls Rancher's `kubeconfigs.ext.cattle.io` API as Alice. It requests one-hour credentials for each app cluster, verifies the endpoint and CA, saves files mode 0600, and logs out the temporary login session. Regenerating replaces/revokes previously generated Step 8 kubeconfig resources with the exact same lab descriptions.

Files:

- `kubeconfigs/alice-cluster-a.yaml`
- `kubeconfigs/alice-cluster-b.yaml`

Each Rancher-generated file contains its app-cluster context plus a `rancher` context for Rancher's own API. That extra context does **not** grant management-cluster access. The default context is the intended app cluster. No default kubeconfig is changed; direct admin files remain separate.

```bash
kubectl --kubeconfig kubeconfigs/alice-cluster-a.yaml get pods -n demo
kubectl --kubeconfig kubeconfigs/alice-cluster-a.yaml auth can-i create deployments -n demo
# no
kubectl --kubeconfig kubeconfigs/alice-cluster-b.yaml auth can-i create deployments -n demo
# yes
```

The files include the lab CA; no Mac trust-store installation or TLS bypass is needed. Credentials expire: regenerate when authentication fails after expiry.

## Actual checks

[Verifier](../scripts/08-verify-kubectl.py) runs the Step 7 permission matrix using real `kubectl auth can-i` calls with Alice's generated credentials. It also makes real reads: pods/deployments in demo return empty lists; kube-system reads fail Forbidden; A/demo Secret reads fail Forbidden. It does not create workloads.

Results: [kubectl log](../artifacts/step-08/kubectl.log), [matrix](../artifacts/step-08/kubectl-matrix.json), [kubeconfig metadata](../artifacts/step-08/kubeconfigs.json). No token values appear in these records.

## Isolated browser

[Browser container](../compose.browser.yaml) runs Chromium with Playwright. [Image](../config/browser/Dockerfile) installs only browser/test dependencies. [Startup](../config/browser/start.sh) trusts the public lab CA inside the container's Linux and NSS stores. No host trust changes, CA private key mount, public browser port, or insecure certificate override.

[Browser checks](../scripts/08-browser-check.cjs) and [runner](../scripts/08-run-browser.sh) are saved as code. Only test-user password files are mounted; admin credentials are not provided to this browser.

Run the complete browser test:

```bash
./scripts/08-run-browser.sh
# Remove the temporary browser container after testing (retain image and evidence):
docker compose -f compose.browser.yaml down
```

The final browser uses a digest-pinned Debian Node base, Debian Chromium, and Playwright 1.58.2. Installed versions are recorded in [browser-versions.txt](../artifacts/step-08/browser-versions.txt). Debian package versions are resolved at build time; retain the built image for an identical rerun. The larger all-browser image was replaced with this smaller Chromium-only build.

Rendered checks passed:

- Alice completes Keycloak login and sees exactly A and B; `mngmt` is absent.
- A's Deployments page has no Create action; B's has Create. Both lists are empty.
- Requests made inside the authenticated browser return 200 for demo pods, 403 outside demo, 403 for A/demo Secrets, and 200 for B/demo Secrets. Management-cluster API access returns 403.
- The no-role user receives an authorization code from Keycloak, then Rancher rejects entry. The UI says “Invalid username or password”; the test verifies the preceding Keycloak callback, so this is Rancher admission denial, not a bad Keycloak password.

Evidence: [browser assertions](../artifacts/step-08/browser-verify.log), [results](../artifacts/step-08/browser-results.json), [Alice home](../artifacts/step-08/alice-home.png), [A](../artifacts/step-08/cluster-a-deployments.png), [B](../artifacts/step-08/cluster-b-deployments.png), [no-role denial](../artifacts/step-08/no-role-denied.png).

Direct admin access to all three clusters and empty demo namespaces passed regression checks. No application workloads were created. The temporary browser container was removed after verification; its image, scripts, and screenshots were retained. Browser sessions and kubeconfig token lifecycle are distinct; closing the browser is not itself a server-side token revocation test.

Stop here. Next step: expiry/revocation, binding/admission changes, Keycloak account disablement, restart/outage behavior, and cleanup documentation.

Source: [Rancher-generated kubeconfigs and TTL](https://ranchermanager.docs.rancher.com/v2.12/api/workflows/kubeconfigs).

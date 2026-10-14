# Step 5 — Rancher cave opens

Date: 14 October 2026. Status: complete. Rancher deployment and connectivity checks passed.

Caveman: Keycloak knows people. Rancher will give people permissions. Today: build Rancher cave. Connect people later.

## What runs

One Rancher 2.15.2 replica in `mngmt`, installed with the pinned Helm chart and ARM64 image digest. Rancher automatically installed its default Fleet controllers/local agent, webhook, CAPI, and Turtles controllers in the management cluster. All were available in the final snapshot. These are management components; no application workloads or user GitOps bundles were added. No optional monitoring, logging, or application stacks are installed.

```text
Mac / future agents → HTTPS rancher.lab.test:8443
                    → existing Docker NGINX gateway
                    → HTTP mngmt-control-plane:30080
                    → Rancher pod, port 80
```

Gateway has the local-CA-signed Rancher certificate. The HTTP backend is reachable on Docker's kind network; its NodePort is not published to the Mac. This is external TLS termination for the local lab, not end-to-end backend encryption. WebSocket headers and long timeouts support future agent/proxy connections.

Rancher gets the public CA twice: `tls-ca` publishes the chain for agents; `tls-ca-additional` trusts outbound Keycloak connections. Agent TLS mode is `strict`. No CA private key goes into Kubernetes. Mac trust stores remain unchanged.

## Code and commands

From `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
./scripts/05-install-rancher.sh
kubectl --kubeconfig kubeconfigs/mngmt-admin.yaml apply -f config/rancher/server-url.yaml
docker exec sso-lab-gateway nginx -t
docker exec sso-lab-gateway nginx -s reload
./scripts/05-verify-rancher.py
./scripts/02-verify-clusters.sh
```

- [Helm values](../config/rancher/values.yaml): one replica, image pin, CA settings, resources, private NodePort.
- [Install script](../scripts/05-install-rancher.sh): creates CA Secrets and installs chart in `mngmt` using its explicit kubeconfig.
- [Server URL](../config/rancher/server-url.yaml): includes HTTPS and port 8443; agents must use this exact address.
- [Gateway config](../config/network/nginx.conf): Rancher route and WebSocket forwarding.
- [Verification](../scripts/05-verify-rancher.py): live HTTPS, UI HTML, CA publishing, strict mode, replica count, Keycloak trust, node access, default-host trust rejection.

Bootstrap username: `admin`. Password retained in `secrets/rancher/bootstrap-password`, mode 0600, parent directory 0700. Do not print or share it. First-login password replacement and permanent recovery access will be configured with the identity step. Helm stores its bootstrap Secret in the management cluster; retain that cluster and its direct admin kubeconfig.

Open [Rancher](https://rancher.lab.test:8443/dashboard/). The normal Mac browser still warns about the untrusted local CA. Browser login is not yet tested; only dashboard delivery is verified by the script.

## Results

- HTTPS `/ping`, dashboard HTML, correct published CA, one ready Rancher replica, strict agent TLS, and canonical URL: passed.
- Rancher container → Keycloak discovery with its installed CA bundle: passed.
- All three nodes → Rancher HTTPS: passed. Default Mac CLI trust still rejects the lab certificate as expected.
- Existing direct administrator access to all three clusters and empty A/B `demo` namespaces: passed. Keycloak readiness and database TLS regression checks passed.
- Default Fleet deployments and Rancher webhook completed rollout. Fleet briefly restarted during initial CRD installation; readiness was rechecked after the CRDs appeared. Gitjob also logged a denied leader-election Event write; it remained available. GitOps functionality is outside this auth POC and was not tested. No A/B imports or user login tests performed in this step.

Records: [verification](../artifacts/step-05/verify.log), [cluster regression](../artifacts/step-05/cluster-regression.log), [Keycloak regression](../artifacts/step-05/keycloak-regression.log), [deployment snapshot](../artifacts/step-05/deployments.txt).

## Step boundary

A/B imports, Keycloak OIDC, group assignments, and user permission tests are later steps. Native admin kubeconfigs remain separate. Stop here and wait for confirmation.

Sources: [Rancher Helm chart options, external TLS, and additional CAs](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/installation-references/helm-chart-options), [private CA Secrets](https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/resources/add-tls-secrets). Actual chart 2.15.2 values were inspected for this deployment.

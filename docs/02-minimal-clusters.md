# Step 2 — Give Docker memory. Build three empty caves.

Date: 14 October 2026. Result: completed and verified.

Caveman: Management cave will hold Rancher. App caves hold no apps. Today build caves and check guards answer.

## Files

- [Memory script](../scripts/02-set-docker-memory.py): set Docker `MemoryMiB` to 16384; preserve other settings.
- [Old memory setting](../artifacts/step-02/docker-memory-before.json): records whether the memory override existed, for undo.
- [Version pins](../config/versions.env): exact kind node image/digest.
- Cluster configs: [mngmt](../config/kind/mngmt.yaml), [cluster-a](../config/kind/cluster-a.yaml), [cluster-b](../config/kind/cluster-b.yaml).
- [Creation script](../scripts/02-create-clusters.sh): refuses existing names, creates one control-plane node per cluster, creates empty demo namespaces in A/B.
- [Verification script](../scripts/02-verify-clusters.sh): readiness, node count, administrator access, empty demo namespaces, Docker memory.

## Commands

Run from `/Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac`:

```bash
# Stop first so Docker does not overwrite the memory setting.
docker desktop stop
python3 scripts/02-set-docker-memory.py
open -a Docker
# Wait until this succeeds, then create clusters.
docker info
./scripts/02-create-clusters.sh
./scripts/02-verify-clusters.sh
```

Do not rerun the creation script over existing clusters. Rerun verification freely. If creation fails partway, inspect the log and existing names; do not delete clusters blindly.

## Access each cave

```bash
kubectl --kubeconfig kubeconfigs/mngmt-admin.yaml get nodes
kubectl --kubeconfig kubeconfigs/cluster-a-admin.yaml get pods -n demo
kubectl --kubeconfig kubeconfigs/cluster-b-admin.yaml get pods -n demo
```

Kubeconfigs retain generated administrator credentials locally with mode 0600. Do not paste their contents. Default user kubeconfig is not used or modified by these scripts.

API endpoints bind only to Mac loopback: mngmt 16443, A 26443, B 36443. Each cluster runs Kubernetes v1.36.4 with built-in networking/storage components. Empty means no application workloads; Kubernetes system pods still run.

## Evidence

- [Creation log](../artifacts/step-02/create.log)
- [Verification results](../artifacts/step-02/verify.log)

Configured Docker allocation: 16 GiB (16384 MiB). Engine reports 16,745,562,112 usable bytes, about 15.6 GiB after VM overhead. CPU allocation remains 12. No CA, Keycloak, PostgreSQL, Rancher, or OIDC configuration is installed in this step.

Verification passed: all three nodes Ready, all API readiness endpoints healthy, all administrator authorization checks returned yes, system pods Running, and both demo namespaces empty.

## Stop

Wait for user confirmation before TLS/networking and service deployment. Keep these clusters running for the next step.

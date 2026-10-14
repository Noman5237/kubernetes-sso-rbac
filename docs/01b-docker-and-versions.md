# Step 1b — Wake Docker. Check tools fit.

Date: 14 October 2026. Completed: Docker startup and core compatibility preflight. No clusters created.

Caveman: Docker is cave floor. Floor awake. Tools fit on paper. Rancher paper blueprint renders. Real building comes next.

## Commands and files

```bash
open -a Docker
cd /Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac
./scripts/01-preflight.sh
```

- [Version pins](../config/versions.env): versions future scripts must use.
- [Preflight script](../scripts/01-preflight.sh): inspect tools and render chart without deploying.
- [Observed results](../artifacts/preflight/result.txt).
- [Chart metadata](../artifacts/preflight/rancher-chart.yaml).
- [Rendered manifests](../artifacts/preflight/rancher-rendered.yaml): validation artifact, not final deployment configuration. No generated credentials.

## Results

| Item | Result |
| --- | --- |
| Docker | Running; Engine 29.7.2, Linux ARM64 |
| Docker VM | 12 CPUs, 8,319,238,144 bytes RAM (about 7.75 GiB) |
| Mac | 48 GiB RAM; about 741 GiB filesystem space available |
| Compose | v5.5.1 |
| kind | v0.33.0 |
| Kubernetes selected | v1.36.4, official kind node image pinned by digest |
| Rancher selected | v2.15.2; registry manifest contains linux/arm64 |
| Helm | v4.3.0; chart rendered successfully for Kubernetes 1.36.4 |
| kubectl | v1.37.0; one minor newer than selected API server |
| Candidate loopback ports | 16443, 26443, 36443, 8443, 9443, 6080 available at check time |

Rancher chart requires Kubernetes below 1.37. Therefore do not use kind's default v1.37.0 image. Use the explicit image in versions.env.

Rancher's matrix covers Kubernetes 1.34–1.36 and ARM64. kind is a local lab environment, not a certified Rancher management distribution. Rendering proves chart compatibility at template level only; installation and authentication remain untested.

Docker has only about 8 GiB assigned. Three control planes plus Rancher, Keycloak production mode, PostgreSQL, and a browser may exceed this. Proposed budget: 16 GiB for Docker before the full stack; this is a lab estimate, not a measured minimum. Docker's resource settings were not changed.

Keycloak, PostgreSQL, browser, and Rancher dependency-image pins remain for their implementation steps. The combined prerequisite TODO remains pending until all pins and the resource decision are complete.

## Sources

- [kind v0.33.0 images and digests](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0)
- [Rancher v2.15.2 support matrix](https://www.suse.com/suse-rancher/support-matrix/all-supported-versions/rancher-v2-15-2/)
- [Helm version support](https://helm.sh/docs/topics/version_skew/)

## Stop here

Wait for user confirmation before creating clusters. Next step: write minimal kind configs, create three single-node clusters with the pinned image, and verify native administrator access. Decide Docker memory allocation before deploying the full stack.

# Demo transcript

Real browser recording with local synthetic narration. Terminal panels replay actual captured kubectl output.

## 00:00 — One identity. Different permissions.

Three tiny Kubernetes clusters. The management cluster runs Rancher. Keycloak knows who Alice is. Rancher decides what Alice can do in each application cluster. We will check the real dashboard and real cube control results.

## 00:15 — Keycloak says: this is Alice.

Here is Alice in Keycloak. Keycloak handles her login. There are no lab groups. We keep all cluster permission assignments in Rancher. These administrator screens show the configuration; they are not screens Alice can administer.

## 00:31 — Reusable role: read pods + deployments.

Here is the reusable lab developer role template. It grants get, list, and watch for pods and deployments. There is no cluster assignment inside this template. The project member binding chooses where these permissions apply.

## 00:46 — Alice → lab-developer → A / demo

In cluster A, open Cluster and Project Members, then Project Membership. Alice has the lab developer role in the demo project. The row says Local for this direct binding, but Alice authenticates through Keycloak. This binding supplies the scope. The reusable role name does not need a cluster name.

## 01:06 — Same Alice → namespace admin → B / demo

In cluster B, the same Alice has lab namespace admin in demo. This is namespace administration, not cluster administration. The role uses an explicit resource list. Keycloak has no cluster role mapping to maintain.

## 01:22 — Alice sees two app clusters.

Now we are signed in as Alice through Keycloak. Rancher shows both application clusters. The management cluster is absent. Same identity, different permissions, controlled by Rancher project assignments.

## 01:37 — Cluster A: read only. No Create action.

In cluster A, Alice can view deployments. The list is empty because we deployed no applications. There is no Create action. Empty means the read succeeded; it does not mean access was denied.

## 01:51 — Cluster B: Create is available.

In cluster B, the Create action is available. Alice has the broader demo namespace role here. We do not deploy anything. Next, the command line checks whether the API agrees with the dashboard.

## 02:04 — Actual kubectl results · Cluster A

These are real cube control commands captured for this demo, using Alice's Rancher kubeconfig. In A, listing pods succeeds. Creating deployments and reading secrets are denied. System namespace pods and cluster nodes are also denied.

## 02:21 — Actual kubectl results · Cluster B

In B, listing pods succeeds. Creating deployments and reading secrets are allowed in demo. System namespace pods and cluster nodes remain denied. Permission checks do not create workloads. The dashboard and command line agree.

## 02:37 — Keycloak = identity. Rancher = permissions.

Keycloak says, this is Alice. Rancher assigns her project roles. Kubernetes enforces the resulting permissions. The current kubeconfig tokens last one hour and can be revoked. This demo leaves the roles unchanged. Lifecycle and outage tests are still a separate next step.

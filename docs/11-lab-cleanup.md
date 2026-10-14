# Lab cleanup — instructions only

Nothing in this document was executed. The lab stays running after reliability testing.

Caveman rule: **stop = pause; delete = lose that lab state.** Git contains configuration and evidence, not a backup of running Kubernetes etcd or PostgreSQL volumes.

## Keep the clusters; detach them from Rancher

While Rancher and its agents are healthy, use **Cluster Management → cluster-a / cluster-b → ⋮ → Delete** for these registered kind clusters. Follow the [Rancher detachment procedure](https://rancher.github.io/product-docs-playbook/rancher-manager/v2.14/en/faq/rancher-is-no-longer-needed.html) and verify component cleanup through each direct administrator kubeconfig before removing the management server.

Use the direct admin kubeconfigs afterward. Rancher-issued Alice kubeconfigs need the Rancher proxy and will not become standalone cluster credentials.

## Delete this entire local lab

Run only when you explicitly want to remove it. From the project directory, first remove the separate Docker services while the gateway still exists:

```sh
./scripts/04-compose.sh down
```

That preserves the PostgreSQL volume. To erase the database too, use `./scripts/04-compose.sh down --volumes` **instead of** the command above. Choose one; the wrapper needs the existing gateway to read its network address. [Docker Compose down](https://docs.docker.com/reference/cli/docker/compose/down/).

Then remove only the three named kind clusters:

```sh
kind delete cluster --name cluster-a --kubeconfig kubeconfigs/cluster-a-admin.yaml
kind delete cluster --name cluster-b --kubeconfig kubeconfigs/cluster-b-admin.yaml
kind delete cluster --name mngmt --kubeconfig kubeconfigs/mngmt-admin.yaml
```

This deletes those clusters' live state, including Rancher and their Kubernetes RBAC. Explicit kubeconfig paths avoid changing your default kubeconfig. [kind deletion documentation](https://kind.sigs.k8s.io/docs/user/quick-start/#deleting-a-cluster).

Remove only this lab's `sso.lab.test` and `rancher.lab.test` entries from `/etc/hosts` if they are no longer needed. No lab CA was installed in macOS Keychain. Keep the project files, secrets, and evidence unless you separately choose to delete them.

Do not use global Docker prune commands for this cleanup. Other Docker projects and clusters are outside this lab.

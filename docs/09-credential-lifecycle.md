# Step 9 — Credentials die. Permissions can change.

14 October 2026. Tested against this lab's Rancher 2.15.2 and Keycloak 26.8.0.

## What we tested

| Action | Actual result |
| --- | --- |
| Delete a generated kubeconfig in Rancher | Its token disappeared. The copied file stopped working on the first check. Another kubeconfig still worked. |
| Issue a token for 20 seconds | It worked before expiry and failed at the first check after expiry, about 21 seconds after issuance. |
| Log out of Rancher | That login token failed immediately. A separately issued kubeconfig still worked. |
| Remove Alice's A/demo project binding | A access failed on the first check. B access continued with the same credential. |
| Restore the A/demo binding | A access returned on the first check. |
| Disable Alice in Keycloak | Fresh login failed with “Account is disabled.” Existing Rancher session and kubeconfig requests still worked throughout a 20-second observation window. |
| Remove Alice from Rancher's explicit allow-list | Three fresh logins still succeeded. Existing credentials still worked during a further 20-second observation window. Alice remained a project member. |

“First check” means the first request after the mutation API returned. It is not a precise controller latency measurement. Expiry was polled every two seconds.

Revoked/expired kubeconfigs returned **403**, with Rancher identifying the requester as `system:unauthenticated`. That is different from a valid Alice identity losing a role. The script checks the anonymous identity for these cases. A logged-out Rancher login token returned **401**.

## Why the allow-list test behaved this way

Our configuration uses `accessMode: restricted`. That mode allows project/cluster members **or** explicitly allowed users. Alice kept her project membership, so removing her allow-list entry did not block login.

`accessMode: required` is the strict allow-list-only mode. We did not switch modes. Earlier descriptions of the lab as simply “allow-list restricted” were incomplete. See [Rancher's login scope documentation](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/authentication-permissions-and-global-configuration/authentication-config/) and the [2.15.2 CheckAccess implementation](https://github.com/rancher/rancher/blob/v2.15.2/pkg/auth/providers/common/usermanager.go#L190-L238).

Caveman version:

- Delete Rancher credential: that credential stops.
- Remove role binding: permission stops in that project.
- Disable Keycloak user: new login stops. Existing Rancher tokens are separate.
- Logout: that session stops. Separate kubeconfig stays alive.
- Remove allow-list entry: membership can still let user in with our current mode.

## Run it

From the project directory:

```sh
python3 scripts/09-credential-lifecycle.py
```

The [script](../scripts/09-credential-lifecycle.py) performs fresh authorization-code/PKCE logins, creates disposable kubeconfigs, makes actual kubectl API requests, and restores Alice's enabled flag, admission configuration, and A/demo binding in `finally`. It renews its Keycloak administrator access token if the short administrator token expires during the test.

It uses [Rancher API helpers](../scripts/rancher_api.py), [Keycloak helpers](../scripts/keycloak_api.py), and [Step 7 assignment IDs](../artifacts/step-07/assignments.json). No application workload is created. Normal `kubeconfigs/alice-*.yaml` files and global token lifetime settings are not changed. Temporary kubeconfigs live in `secrets/lifecycle/`; their tokens are revoked at the end.

If the process is forcibly interrupted, restore the saved identity/admission/binding state with:

```sh
python3 scripts/09-credential-lifecycle.py --restore
```

The restore-only command restores configuration. After a hard interruption, use the resource/session IDs recorded in `results.json` to review and revoke remaining test credentials; it does not automatically clean those up.

## Evidence and limits

- [Final results](../artifacts/step-09/results.json) and [run log](../artifacts/step-09/lifecycle.log).
- [Restoration snapshot](../artifacts/step-09/restore-state.json).
- Initial attempt logs are retained: the first assumed 401 instead of Rancher's anonymous 403; the second exposed the administrator-token renewal requirement. Configuration was restored and abandoned test credentials were removed before the final run.
- Existing-token behavior after Keycloak disablement and admission changes was observed for 20 seconds, not until every possible refresh/resync boundary. This does not prove tokens remain usable indefinitely.
- Long-duration OIDC session refresh, browser single logout, service outages, and restart behavior are not covered here.
- [Rancher kubeconfig resource documentation](https://ranchermanager.docs.rancher.com/api/workflows/kubeconfigs) describes per-kubeconfig TTL and deletion of associated tokens.

## Restored and checked

Alice is enabled again, her original explicit login list and both direct project assignments are intact, and the original permission matrix passed again. The no-role user remains denied. Native administrator access works in all three clusters, and both demo namespaces remain empty. All disposable kubeconfigs, associated tokens, and final-run login sessions were confirmed deleted. See [final verification](../artifacts/step-09/final-verification.json).

Stop after this step. Wait for confirmation before outage/restart testing.

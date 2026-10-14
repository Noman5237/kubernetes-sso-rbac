# Step 10 — Break one service. Check recovery.

14 October 2026. Controlled local outages; no HA.

## Results

| Test | Observed result |
| --- | --- |
| Stop Keycloak; leave PostgreSQL/Rancher running | Fresh OIDC login failed. Rancher dashboard and local administrator login worked. Alice's existing Rancher session and both kubeconfigs worked throughout the 20-second observation window. |
| Start Keycloak | Fresh OIDC login worked again. Realm, Alice, client configuration, roles and bindings matched the baseline. Existing kubeconfigs still worked. Recovery checks completed in **7.9 seconds**. |
| Scale Rancher from one replica to zero | Dashboard returned HTTP 502. Both Rancher-proxy kubeconfigs failed. Keycloak stayed available. |
| While Rancher is down | Direct administrator kubeconfigs worked on all three clusters. Actual native ServiceAccount authentication worked in A/B. |
| Restore Rancher to one replica | Both clusters returned Active with available agents. The same pre-outage kubeconfig worked again. Fresh login and stored configuration passed. Recovery checks completed in **22.7 seconds**. |
| Final regression | Alice's original A/B permissions passed again; no-role login remained denied; demo namespaces stayed empty. |
| TLS trust | Explicit lab CA succeeded; an unrelated CA failed verification. The lab CA was absent from checked user and system Mac keychains. |

Times include readiness polling and verification work after the start/scale command. They are single-run lab observations, not recovery-time guarantees.

Caveman version:

- Keycloak down: new login stuck. Existing Rancher tokens worked in our short test.
- Rancher down: dashboard and proxy stuck. Direct Kubernetes admins still work.
- Service comes back: same users, roles and bindings still there.
- One replica means downtime. This test does not provide HA.

## Code and commands

From the project directory:

```sh
python3 scripts/10-reliability.py
python3 scripts/10-verify-recovery.py
```

[Outage script](../scripts/10-reliability.py) records a baseline and issues a separate 30-minute test kubeconfig. It stops/starts only the existing Keycloak container, then temporarily scales Rancher to zero and back to its original one replica. It waits for actual proxy access and agent availability as well as the server endpoint.

[Verification script](../scripts/10-verify-recovery.py) checks service recovery, native administrator access, empty demo namespaces, test-credential cleanup, TLS rejection with the wrong CA, and targeted Mac keychain CA searches.

Inputs: [Rancher deployment values](../config/rancher/values.yaml), [Keycloak Compose configuration](../compose.keycloak.yaml), [assignment IDs](../artifacts/step-07/assignments.json), and the existing direct administrator kubeconfigs. Deployment values and normal Alice kubeconfig files are unchanged.

ServiceAccount test tokens use Kubernetes TokenRequest with a ten-minute lifetime and stay in process memory. No ServiceAccount, Role or RoleBinding is created for this check. Disposable Rancher credentials are explicitly revoked after testing.

## If the test is interrupted

The script restores services and cleans up its Rancher credentials in `finally`. After a hard interruption, run:

```sh
python3 scripts/10-reliability.py --restore
```

This reads [the recorded baseline](../artifacts/step-10/restore-state.json), starts Keycloak if needed, restores Rancher's replica count, waits for readiness, and removes recorded test credentials. Recovery uses the direct management-cluster administrator kubeconfig; Rancher does not have to be available first.

## Evidence and boundaries

- [Final outage results](../artifacts/step-10/results.json) and [run log](../artifacts/step-10/reliability.log).
- [Recovery/TLS verification](../artifacts/step-10/final-verification.json) and [permission regression](../artifacts/step-10/permission-regression.log).
- Two earlier test logs are retained: one exposed a timeout-handler naming bug, the other an unrecognized kubectl response during startup. Both restored services and removed their test credentials. The final run completed all checks.
- Keycloak outage observation of existing credentials was 20 seconds. Long-duration token refresh/resync behavior is not established.
- PostgreSQL remained running. Database failure, host restart, Docker Desktop restart, power loss, backup restoration, managed EKS/GKE, and HA were not tested here.
- No CA was installed in macOS, no TLS verification was bypassed, and no cluster or data volume was deleted.

[Cleanup/unregistration instructions](11-lab-cleanup.md) are documented separately and were not executed.

Stop here. The lab is restored and running. Wait for the next instruction.

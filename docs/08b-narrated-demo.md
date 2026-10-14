# Step 8b — Watch the auth lab

14 October 2026. This is a demo of the completed setup. Lifecycle/outage tests remain pending.

## Watch

Watch the 2 minute 58 second demo. Open [the narrated video](../demo/kubernetes-sso-rbac-demo.mp4). Read [the transcript and chapter times](../artifacts/demo/transcript.md).

Caveman version:

1. Keycloak knows Alice. No lab groups.
2. Rancher stores reusable role templates.
3. Project A binds Alice to `lab-developer`.
4. Project B binds Alice to `lab-namespace-admin`.
5. Alice opens dashboard. A: read. B: more powers inside `demo`.
6. Alice runs kubectl through Rancher. Same boundaries.

The video labels administrator configuration views separately from Alice's dashboard. Rancher's project-member row displays **Local** for this direct user binding; the Users page identifies Alice's provider as Keycloak, and the demo checks an actual Keycloak authorization-code login. Alice has no local password configured by this POC.

## What was recorded

Real Keycloak and Rancher web pages, with added callout outlines and captions. Browser recording happens in an isolated Linux container. Voice is synthesized locally with the macOS Daniel voice. No desktop capture, microphone recording, host-browser control, or host CA installation.

The terminal panels are **playback of actual command output captured for this demo**, not an interactive terminal screen recording. [Results](../artifacts/demo/kubectl-results.json) include commands, exit codes, and capture time. No simulated permission results.

Both app clusters remain empty of application workloads. `kubectl auth can-i` checks write permission without creating anything. Neither secret values nor kubeconfig token contents appear in the video.

## Files used

- [Demo container](../compose.demo.yaml): isolated browser, read-only password mounts, public lab CA. Temporary profiles stay inside container.
- [Narration](../scripts/demo-narration.py): script and local speech generation.
- [Real kubectl capture](../scripts/demo-capture-kubectl.py): ten read-only checks against Alice's two contexts.
- [Browser preparation](../scripts/demo-prepare.cjs): administrator session for configuration views.
- [Browser recording](../scripts/demo-record.cjs): fresh Alice OIDC login, actual UI assertions, callouts, video scenes.
- [Video assembly](../scripts/demo-render.py): voice synchronization, H.264/AAC MP4, transcript, full decode verification.
- [Rerun script](../scripts/demo-run.sh): complete procedure below.

## Run again

From the POC directory:

```sh
sh scripts/demo-run.sh
```

Needs the existing healthy lab, local `sso-lab-browser:1.58.2` image from Step 8, Docker, Python, kubectl, and macOS `say`. FFmpeg dependencies are downloaded inside the temporary container. Browser TLS verification remains enabled.

Rerunning refreshes Alice's two one-hour POC kubeconfigs using [the existing generator](../scripts/08-generate-kubeconfigs.py), which revokes the prior matching lab kubeconfigs. It does not change Rancher token-lifetime settings, identity configuration, role templates, or project bindings. Six-month credentials were discussed but not applied.

## Verification

- Actual Alice OIDC authorization-code callback observed before dashboard access.
- Keycloak user list and empty groups shown.
- Reusable developer role and direct Alice project assignments shown.
- Alice home lists A/B, with no management-cluster link.
- A deployment list has no Create action; B has Create.
- Actual kubectl: A denies deployment creation and Secret reads; B allows both within demo.
- Both deny system-namespace pod access and node access.
- Final MP4 contains H.264 video and AAC narration; full-file decoding checked.
- [Recording metadata](../artifacts/demo/recording.json), [media verification](../artifacts/demo/media-verification.json), and scene PNGs provide review evidence.

Stop here. Wait for confirmation before lifecycle/outage tests.

# README GIF — whole lab in 56 seconds

14 October 2026.

[Watch the GIF](../demo/poc-overview.gif). The project [README](../readme.md) embeds it as a normal Markdown image, so GitHub displays it inline.

## What it shows

Three-cluster architecture → Keycloak users and no groups → reusable developer role → Alice's A/B project bindings → Alice's multi-cluster dashboard → A read-only versus B Create action → actual kubectl results → lifecycle findings and recovery boundaries.

Real browser footage comes from the existing narrated demo. Its audio is discarded. Terminal scenes replay actual command output. Caption cards summarize verified results; outage/restart testing is explicitly pending. Existing-token behavior after Keycloak disablement is limited to the measured 20-second window.

## Build again

```sh
sh scripts/demo-gif.sh
```

- [Build script](../scripts/demo-gif.sh): starts an isolated media container and removes it afterward.
- [Scene/encoding script](../scripts/demo-gif.cjs): renders caption cards, trims the existing clips, removes audio, and creates the GIF.
- [Container configuration](../compose.gif.yaml): mounts recording assets and scripts; no credentials or live cluster connection are mounted.
- Inputs: `artifacts/demo/clip-*.mp4` and the completed Step 9 results.
- Output: `demo/poc-overview.gif`.

Uses the existing `sso-lab-browser:1.58.2` image. FFmpeg and gifsicle are installed only in the temporary container. No POC configuration changes or host CA changes.

## Verified

- Duration: **56 seconds**, below one minute.
- Dimensions: **1080 × 676**.
- Size: **1,812,898 bytes** (about 1.8 MB).
- Infinite loop, no audio.
- Full GIF decode passed; caption cards and representative output frames visually checked.
- [Machine-readable verification](../artifacts/gif/verification.json).

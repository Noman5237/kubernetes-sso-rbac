# Step 1a — Install Helm

Date: 14 October 2026. Result: installed and verified.

Caveman: Helm carries app packages into cluster. Today install tool. No app deployed.

## Commands used

```bash
brew install helm
helm version --short
helm env
```

Observed version: `v4.3.0+gbec5b06` (native ARM64 Homebrew bottle).
Executable: `/opt/homebrew/bin/helm`.
Installation: `/opt/homebrew/Cellar/helm/4.3.0`.
All commands exited successfully. No cluster access was needed.

Homebrew's automatic cleanup also removed old cached downloads/logs and pruned stale entries; the installation output reported this behavior.

## Next step — wait for user

Check/start Docker and validate the Rancher/Kubernetes/Helm version combination before creating clusters. Helm is installed; compatibility with the chosen Rancher release is not yet verified. Homebrew installs its current formula, so this command alone does not pin future installations to 4.3.0.

Related checklist: [TODO](../todo.md). This installation does not complete the checklist's full version-compatibility task.

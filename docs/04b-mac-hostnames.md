# Step 4b — Mac knows cave names

Status: complete. Added lab host entries through the macOS administrator prompt. No CA installed.

Caveman: Browser knows name after hosts entry. Browser still distrusts certificate. No CA installed.

Run in your Mac terminal:

```bash
sudo /bin/sh /Users/mdabdullahal.noman/Workshops/kubernetes-sso-rbac/scripts/04b-host-dns.sh
```

[Script](../scripts/04b-host-dns.sh) adds only:

```text
127.0.0.1 sso.lab.test rancher.lab.test
```

Then open https://sso.lab.test:8443/admin/ . A certificate warning remains because Mac trust stores are unchanged.

Verified: macOS resolves `sso.lab.test` to `127.0.0.1`; HTTPS `/admin/` responds with HTTP 302 using an explicit CA file, without a DNS override. Mac trust stores unchanged.

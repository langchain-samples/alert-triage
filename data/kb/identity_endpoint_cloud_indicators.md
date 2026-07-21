> SYNTHETIC / FICTIONAL: This SOC detection guide is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# Identity, Endpoint, and Cloud-Exfil Indicators

## Identity indicators

Treat impossible travel as higher risk when it is followed within 30 minutes by MFA fatigue, new device registration, OAuth consent with broad scopes, or privileged group activity. A single impossible-travel event with normal device posture is usually `needs_review`, but impossible travel plus token reuse on a finance, payment, or identity-admin account is at least High.

OAuth grants requesting `Mail.Read`, `Files.Read.All`, `offline_access`, or tenant-wide admin consent are High when the app is new to the tenant or matches a domain seen in prior phishing incidents. If the account has privileged or payment approval roles, escalate.

## Endpoint indicators

PowerShell using encoded commands, credential access tooling, LSASS handle access, unsigned remote management binaries, or suspicious scheduled tasks are High when seen on production or executive endpoints. On build/test hosts, blocked execution with no persistence is Medium unless incident history shows the same toolchain succeeded before.

Ransomware canary or rapid file-renaming behavior on file servers is Critical, especially when backup shares or regulated data stores are involved. Isolate only the affected host or storage path first; do not mass-disable unrelated systems.

## Cloud and data-exfil indicators

Large downloads from storage buckets, abnormal `GetObject` bursts, new access keys, access from unusual ASN/geography, or bulk exports from SaaS systems are High. Make it Critical when the asset holds regulated data or customer payment records, or when the evidence includes public ACL changes or outbound transfer to an unapproved external account.

Use this file as `identity_endpoint_cloud_indicators.md` when citing indicator-specific guidance.

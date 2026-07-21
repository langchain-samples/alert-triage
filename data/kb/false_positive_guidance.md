> SYNTHETIC / FICTIONAL: This false-positive guide is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# False-Positive and Benign-Activity Guidance

The following fictional patterns reduce severity when they are explicitly present in the alert evidence or asset notes:

- **Approved vulnerability scans** — Scanner service accounts, the `redcanary-scan` user-agent, source segment `scanner-segment`, or asset owner `Security Assurance` indicate sanctioned testing. If the control blocked the probe and there is no exploitation, disposition should be `benign_false_positive` or `blocked_attempt`, severity Low or Informational.
- **Patch and configuration windows** — Change windows tagged in asset notes can explain admin logins, reboot bursts, or package downloads. Still verify no suspicious command or external destination is present.
- **Backup and ETL jobs** — Scheduled exports by service accounts are benign only when the destination, volume, and time match the asset's expected job notes. New destinations, unusual ASN, or public ACL changes override this guidance.
- **Developer sandbox activity** — Test malware strings, encoded commands, or failed exploit payloads in sandbox assets are usually Medium or Low when blocked and isolated to the sandbox. Escalate only if there is lateral movement, credential access, or a production asset target.

When citing this guidance, use `false_positive_guidance.md` and state the exact benign indicator that was present. Do not call an alert benign merely because one field is missing.

> SYNTHETIC / FICTIONAL: This SOC policy excerpt is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# Meridian Union SOC Severity Rubric

Use this rubric for the fictional Meridian Union environment. Severity is the analyst's cited decision after combining alert evidence, asset criticality, historical incidents, and containment risk.

## Severity levels

- **Critical** — confirmed or strongly indicated compromise of a crown-jewel, identity-control, payment, or domain-administration asset; active data exfiltration; credential dumping on tier-0 infrastructure; ransomware behavior with encryption/canary hits; or any event requiring immediate incident commander escalation.
- **High** — likely compromise or policy violation on a high/critical business asset; phishing-to-token or OAuth abuse with privileged scope; suspicious data movement involving regulated datasets; or endpoint activity matching a prior confirmed incident even if impact is not yet proven.
- **Medium** — suspicious activity with plausible malicious intent but limited asset criticality, blocked exploitation, incomplete kill-chain evidence, or containment that can wait for analyst confirmation.
- **Low** — benign, sanctioned, or low-impact activity with clear false-positive indicators, no sensitive asset, and no persistence/exfiltration evidence.
- **Informational** — expected control noise or hygiene finding that should be logged but does not require containment.

## Disposition taxonomy

Use exactly one disposition:

- `confirmed_incident` — evidence meets the critical/high incident threshold and containment should start.
- `likely_incident` — evidence is strong but one confirmatory signal is missing.
- `needs_review` — suspicious but ambiguous; gather more evidence before disruptive action.
- `benign_false_positive` — documented sanctioned behavior or known scanner/test pattern explains the alert.
- `blocked_attempt` — control blocked the attempt and no compromise evidence is present.

## Escalation rule

Set `escalate: true` for Critical severity, for High severity involving regulated data, privileged identity, or repeat incident-history match, and for any case requiring account disablement, host isolation, key rotation, or legal/privacy notification approval. Cite this file as `severity_rubric.md` when applying the severity or escalation rule.

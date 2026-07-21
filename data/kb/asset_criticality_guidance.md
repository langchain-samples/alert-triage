> SYNTHETIC / FICTIONAL: This asset-criticality guide is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# Asset Criticality Guidance

Use this guide to translate fictional Meridian Union asset context into alert-triage impact. Always combine asset criticality with observed alert evidence; a critical asset does not automatically make a blocked or hygiene-only event Critical.

## Critical assets

Critical assets include identity-control-plane services, payment systems, regulated cloud storage, and regulated claims file shares. Confirmed compromise, public exposure, active exfiltration, credential dumping, ransomware canary hits, or destructive changes on these assets should be High or Critical depending on whether the evidence shows active impact. Cite `asset_criticality_guidance.md` when explaining why `AST-IDP-01`, `AST-PAY-API-01`, `AST-FS-02`, or `AST-CLOUD-STG-09` raises impact.

## High-criticality assets

High assets include privileged finance endpoints, executive endpoints, HR SaaS applications, and internet-facing remote-access services. Suspicious identity abuse, credential access, or unapproved bulk export on these assets is usually High when paired with a prior incident match or sensitive-data movement. Blocked activity without successful compromise may remain Medium when containment can safely wait for owner confirmation.

## Medium and low assets

Medium build, inventory, and internal service assets can generate important security signals, but severity should stay Medium or lower when egress is blocked, no credential access is present, and asset notes show an expected job or ephemeral environment. Low sandbox and scanner assets should generally reduce severity when their tags explicitly show sanctioned testing and there is no production reach.

## Criticality caveats

- Do not escalate solely because an asset is critical; cite the compromising behavior that changes impact.
- Do not mark a sanctioned scanner or sandbox test High unless it moves beyond the approved testing context.
- Do not recommend broad containment across an owner team just because one asset is high impact. Scope containment to the implicated account, host, token, key, app grant, bucket, or path.

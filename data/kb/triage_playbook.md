> SYNTHETIC / FICTIONAL: This SOC playbook excerpt is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# Alert Triage Playbook

Follow this sequence for every fictional Meridian Union alert:

1. **Identify the alert** — retrieve the alert by ID and summarize the detector, entities, timestamp, and raw evidence.
2. **Enrich entities** — retrieve asset context for each host, account, application, cloud resource, or identity provider entity named by the alert. Prioritize business criticality, data classification, owner team, exposure, and environment.
3. **Match history** — search prior incidents for shared indicators, tactics, affected asset types, detector names, user-agent strings, commands, domains, buckets, or named entity patterns.
4. **Apply KB guidance** — use the severity rubric and the relevant indicator/false-positive/containment guide to decide severity and disposition.
5. **Recommend containment** — choose specific next actions. Prefer reversible containment first unless the rubric says escalation is required.

## Required triage report format

Return:

- `severity`: Critical, High, Medium, Low, or Informational
- `disposition`: one taxonomy value from the severity rubric
- `escalate`: true or false
- `rationale`: 2-4 concise bullets grounded in alert evidence, asset context, incident history, and KB guidance
- `recommended_containment`: specific, severity-appropriate actions
- `citations`: filenames for KB guidance plus structured sources such as alert ID, asset ID, and incident ID
- `uncertainty`: what remains unknown and the next non-destructive check

Never invent IP reputation, user identity, malware family, ticket numbers, or containment status. If the fixture data does not provide a fact, state that it is unknown.

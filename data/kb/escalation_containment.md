> SYNTHETIC / FICTIONAL: This escalation and containment guide is invented for the alert-triage lab. It contains no real organization data, PII, secrets, or operational instructions for a real environment.

# Escalation and Containment Guide

Containment must be proportional and reversible unless the severity rubric requires immediate escalation.

## Critical or escalated High

- Page the SOC lead and incident commander.
- Preserve evidence: snapshot affected host or cloud audit logs before cleanup where practical.
- Isolate only affected endpoint, storage bucket, service account, or application role.
- Disable or revoke only the implicated account, OAuth grant, session, access key, or token. Avoid broad tenant-wide disablement unless an incident commander approves it.
- For regulated or payment data exposure, notify privacy/legal according to the fictional Meridian Union breach workflow.

## Medium or needs-review

- Do not take destructive action by default.
- Add temporary monitoring, require step-up MFA, collect endpoint triage package, verify owner-approved change or job schedule, and open an analyst review task.
- If new evidence shows persistence, credential access, exfiltration, or crown-jewel asset impact, reclassify and escalate.

## Low, Informational, blocked, or benign

- Document why the alert is benign or blocked.
- Suppress only the exact known-safe signature or test pattern and set an expiry.
- Leave production containment unchanged unless follow-up evidence appears.

Use this file as `escalation_containment.md` for containment recommendations.

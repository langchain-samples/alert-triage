---
name: campaign-correlation
description: >
  Correlate several SOC alerts into a coordinated-campaign verdict. Use when triaging more than one
  alert together: how to pivot on shared entities, build the timeline, exclude decoys, and set an
  aggregate severity that can exceed any single alert.
---

# Campaign correlation

A coordinated campaign is several alerts driven by one actor against one objective. Individual alerts
often look Medium/High in isolation; correlated, they are a Critical incident.

## Procedure

1. **Build the pivot table.** For every investigated alert, list its accounts, source IPs, hosts,
   destination domains, and matched prior incidents. Two or more alerts sharing an **account** or a
   **source IP** are strong evidence of one campaign.
2. **Order by timestamp.** A campaign usually stages over hours: identity compromise → endpoint
   access → data movement. A coherent kill-chain across shared pivots confirms coordination.
3. **Exclude decoys explicitly.** Same detector is not the same campaign. Drop any alert whose
   account **and** IP differ from the cluster, whose destination is sanctioned, or that occurred in an
   approved change window. State why it was excluded.
4. **Set the aggregate.** Severity = the impact of the *combined* activity, not the max of the parts.
   Account takeover of a privileged/finance identity plus data export is **Critical**, `escalate:
   true`, even when each alert alone was ≤ High.
5. **Report** the linked alert IDs, the pivot entities, the excluded decoys, the aggregate
   severity/disposition/escalation, one consolidated containment plan, and cited fixture IDs.

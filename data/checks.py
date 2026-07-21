#!/usr/bin/env python3
"""Per-use-case consistency plugin for the SOC Alert-Triage Assistant.

lab-check is domain-agnostic; THIS file holds alert-triage-specific consistency the generic checker
can't know: (1) the alert_triage_graph.py tool contract still works, (2) every structured fixture is
synthetic/provenanced and internally referential, and (3) eval reference triage fields are grounded in
data/alerts.json, data/assets.json, data/incidents.json, and data/kb/*.md.

Contract: exit 0 = consistent, non-zero = violation. Offline: imports the deployable graph module but
makes no network call (KB search is local text search; model clients are constructed only).

Run standalone too:  uv run python data/checks.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# repo root: data/checks.py -> data -> <repo root>
CONTENT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent
KB = DATA / "kb"
ALERTS_PATH = DATA / "alerts.json"
ASSETS_PATH = DATA / "assets.json"
INCIDENTS_PATH = DATA / "incidents.json"
DATASET = CONTENT / "evals" / "dataset_alert_triage.json"

errors: list[str] = []
oks: list[str] = []


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _records(obj: dict) -> dict:
    return {k: v for k, v in obj.items() if not k.startswith("_")}


def check_synthetic_markers() -> None:
    """Every corpus doc carries a synthetic banner and every structured JSON has a _note."""
    for md in sorted(KB.glob("*.md")):
        text = md.read_text().upper()
        if "SYNTHETIC" not in text or "FICTIONAL" not in text:
            errors.append(f"{md.name} missing SYNTHETIC / FICTIONAL banner")
        else:
            oks.append(f"synthetic banner: {md.name}")
    for path in (ALERTS_PATH, ASSETS_PATH, INCIDENTS_PATH):
        obj = _load(path)
        if "_note" not in obj or "SYNTHETIC" not in obj["_note"].upper() or "FICTIONAL" not in obj["_note"].upper():
            errors.append(f"{path.name} missing synthetic _note provenance")
        else:
            oks.append(f"structured provenance: {path.name}")


def check_graph_contract() -> None:
    """alert_triage_graph.py imports and each public structured tool returns the expected fixture facts."""
    sys.path.insert(0, str(CONTENT))
    os.environ.setdefault("OPENAI_API_KEY", "sk-dummy-offline-construct-only")  # construct, never call
    if "gateway.smith.langchain.com" in os.environ.get("OPENAI_BASE_URL", ""):
        os.environ.pop("OPENAI_BASE_URL", None)
    try:
        import alert_triage_graph as g  # noqa: E402 — deployable module
    except Exception as e:  # pragma: no cover
        errors.append(f"alert_triage_graph.py failed to import: {e}")
        return

    alerts = _records(_load(ALERTS_PATH))
    assets = _records(_load(ASSETS_PATH))
    incidents = _records(_load(INCIDENTS_PATH))

    for alert_id, rec in alerts.items():
        out = g.get_alert.invoke({"alert_id": alert_id})
        if "No alert found" in out or rec["detector"] not in out or rec["title"] not in out:
            errors.append(f"get_alert({alert_id!r}) did not return the alert record")
        else:
            oks.append(f"graph contract: get_alert({alert_id}) OK")

    for asset_id, rec in assets.items():
        out = g.get_asset_context.invoke({"query": asset_id})
        if "No asset context" in out or rec["business_criticality"] not in out or rec["data_classification"] not in out:
            errors.append(f"get_asset_context({asset_id!r}) did not return the asset context")
        else:
            oks.append(f"graph contract: get_asset_context({asset_id}) OK")

    for incident_id, rec in incidents.items():
        out = g.search_incident_history.invoke({"query": incident_id})
        if "No matching" in out or rec["title"] not in out:
            errors.append(f"search_incident_history({incident_id!r}) did not return the incident")
        else:
            oks.append(f"graph contract: search_incident_history({incident_id}) OK")

    out = g.search_soc_kb.invoke({"query": "severity escalation containment"})
    if "severity_rubric.md" not in out or "escalation_containment.md" not in out:
        errors.append("search_soc_kb did not return expected severity/containment KB citations")
    else:
        oks.append("graph contract: search_soc_kb returns cited KB snippets")


def check_referential_integrity() -> None:
    """Alert asset/incident links resolve; incident affected-assets resolve; recommended reference shape is valid."""
    alerts = _records(_load(ALERTS_PATH))
    assets = _records(_load(ASSETS_PATH))
    incidents = _records(_load(INCIDENTS_PATH))
    severities = {"Critical", "High", "Medium", "Low", "Informational"}
    dispositions = {"confirmed_incident", "likely_incident", "needs_review", "benign_false_positive", "blocked_attempt"}

    for incident_id, rec in incidents.items():
        for asset_id in rec.get("affected_assets", []):
            if asset_id not in assets:
                errors.append(f"{incident_id} affected asset {asset_id} not found in assets.json")

    for alert_id, rec in alerts.items():
        for asset_id in rec.get("asset_ids", []):
            if asset_id not in assets:
                errors.append(f"{alert_id} asset_id {asset_id} not found in assets.json")
        for incident_id in rec.get("related_incident_ids", []):
            if incident_id not in incidents:
                errors.append(f"{alert_id} related incident {incident_id} not found in incidents.json")
        ref = rec.get("recommended_reference", {})
        if ref.get("severity") not in severities:
            errors.append(f"{alert_id} invalid recommended severity {ref.get('severity')!r}")
        if ref.get("disposition") not in dispositions:
            errors.append(f"{alert_id} invalid recommended disposition {ref.get('disposition')!r}")
        if not isinstance(ref.get("escalate"), bool):
            errors.append(f"{alert_id} recommended_reference.escalate must be boolean")
        if not ref.get("required_evidence") or not ref.get("recommended_containment"):
            errors.append(f"{alert_id} recommended reference missing evidence or containment")
    if not any("not found" in e or "invalid recommended" in e or "recommended_reference" in e for e in errors):
        oks.append(f"referential integrity: {len(alerts)} alerts, {len(assets)} assets, {len(incidents)} incidents resolve")


def _text_blob(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_text_blob(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_text_blob(v) for v in value.values())
    return str(value)


def _assert_contains(i: int, where: str, needle: str, haystack: str) -> None:
    if needle not in haystack:
        errors.append(f"eval example {i}: {where} missing grounded token {needle!r}")


def check_eval_grounding() -> None:
    """The 10 eval examples agree with alerts.json and cite only existing KB docs/fixture IDs."""
    alerts = _records(_load(ALERTS_PATH))
    assets = _records(_load(ASSETS_PATH))
    incidents = _records(_load(INCIDENTS_PATH))
    kb_files = {p.name for p in KB.glob("*.md")}
    examples = json.loads(DATASET.read_text())

    if len(examples) != 10:
        errors.append(f"eval dataset should contain 10 examples, found {len(examples)}")

    allowed_tools = {"get_alert", "get_asset_context", "search_incident_history", "search_soc_kb"}
    md_ref = re.compile(r"[\w./-]+\.md")
    checked = 0
    for i, ex in enumerate(examples):
        meta = ex.get("metadata", {})
        outputs = ex.get("outputs", {})
        alert_id = meta.get("alert_id")
        if alert_id not in alerts:
            errors.append(f"eval example {i}: metadata.alert_id {alert_id!r} not in alerts.json")
            continue
        alert = alerts[alert_id]
        ref = alert["recommended_reference"]
        reference_answer = outputs.get("reference_answer", "")

        for field in ("severity", "disposition", "escalate"):
            if outputs.get(field) != ref.get(field):
                errors.append(f"eval example {i} ({alert_id}): outputs.{field}={outputs.get(field)!r} but alert fixture has {ref.get(field)!r}")
        if outputs.get("required_evidence") != ref.get("required_evidence"):
            errors.append(f"eval example {i} ({alert_id}): required_evidence drifted from alerts.json")
        if outputs.get("recommended_containment") != ref.get("recommended_containment"):
            errors.append(f"eval example {i} ({alert_id}): recommended_containment drifted from alerts.json")
        if not set(outputs.get("expected_tools", [])).issubset(allowed_tools):
            errors.append(f"eval example {i} ({alert_id}): unexpected tool in expected_tools")

        # Required report must cite the alert, its assets, related incidents, and any referenced KB files must exist.
        _assert_contains(i, "reference_answer", alert_id, reference_answer)
        for asset_id in alert.get("asset_ids", []):
            _assert_contains(i, "reference_answer", asset_id, reference_answer)
        for incident_id in alert.get("related_incident_ids", []):
            _assert_contains(i, "reference_answer", incident_id, reference_answer)
        for cited in md_ref.findall(reference_answer):
            fname = Path(cited).name
            if fname not in kb_files:
                errors.append(f"eval example {i}: cites {fname!r}, not present in data/kb")

        # Every required evidence item should be derivable from the alert, its assets, or related incidents.
        fixture_blob = " ".join(
            [
                _text_blob(alert),
                _text_blob([assets[a] for a in alert.get("asset_ids", []) if a in assets]),
                _text_blob([incidents[j] for j in alert.get("related_incident_ids", []) if j in incidents]),
            ]
        ).lower()
        for evidence in outputs.get("required_evidence", []):
            tokens = [tok.lower().strip(".,;:()") for tok in evidence.replace("/", " ").replace("-", " ").split()]
            content_tokens = [tok for tok in tokens if len(tok) >= 4 and tok not in {"with", "from", "role", "match", "pattern", "asset", "critical", "prior"}]
            if content_tokens and not any(tok in fixture_blob for tok in content_tokens):
                errors.append(f"eval example {i} ({alert_id}): evidence {evidence!r} is not grounded in fixtures")
        checked += 1

    if checked == len(examples) and not any(e.startswith("eval example") for e in errors):
        oks.append(f"eval grounding: {len(examples)} examples match alert references and fixture IDs")


def main() -> int:
    check_synthetic_markers()
    check_graph_contract()
    check_referential_integrity()
    check_eval_grounding()
    for m in oks:
        print(f"  ✅ {m}")
    for m in errors:
        print(f"  ⛔ {m}")
    print(f"checks.py: {len(oks)} ok · {len(errors)} error")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

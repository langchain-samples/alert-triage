"""Deployable alert-triage agent — single source of truth for the SOC Alert-Triage Assistant.

This graph is built over synthetic fixtures in `data/` so the labs can
teach grounded SOC triage without real incidents, PII, secrets, or live security telemetry.

In `langchain>=1.0`, `create_agent` returns a compiled LangGraph graph. The module-level graphs below are
registered in `langgraph.json` for LangGraph Studio and reused by notebooks/evals.

Security: all tools are pure-Python lookups/searches over committed JSON/Markdown fixtures (no SQL, eval,
network, shelling out, or real containment action). The system prompt is pulled with an offline-safe
fallback via `utils.prompts`; API keys are read only by the model provider at runtime.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from utils.models import get_model
from utils.prompts import get_prompt

_DATA_DIR = Path(__file__).resolve().parent / "data"
KB_DIR = _DATA_DIR / "kb"
AGENT_DIR = _DATA_DIR / "agent"  # AGENTS.md + skills/ for the campaign deep agent (v2)
ALERTS_PATH = _DATA_DIR / "alerts.json"
ASSETS_PATH = _DATA_DIR / "assets.json"
INCIDENTS_PATH = _DATA_DIR / "incidents.json"
PROMPT_PATH = _DATA_DIR / "prompt.md"

PROMPT_NAME = "alert-triage-01-build"

ALERTS: dict = json.loads(ALERTS_PATH.read_text())
ASSETS: dict = json.loads(ASSETS_PATH.read_text())
INCIDENTS: dict = json.loads(INCIDENTS_PATH.read_text())


def _talk_to_openai_directly() -> None:
    """LangGraph Platform may inject an OpenAI gateway URL. This workspace's gateway is not assumed to
    serve the configured lab model, so remove that injected value and use the normal provider path."""
    if "gateway.smith.langchain.com" in os.environ.get("OPENAI_BASE_URL", ""):
        os.environ.pop("OPENAI_BASE_URL", None)


_talk_to_openai_directly()


def _records(obj: dict) -> list[dict]:
    return [rec for key, rec in obj.items() if not key.startswith("_")]


def _fmt_list(values: list[str] | None) -> str:
    return ", ".join(values or []) if values else "none"


@tool
def get_alert(alert_id: str) -> str:
    """Get one synthetic alert's detector, entities, evidence, related assets/incidents, and reference
    triage hints by alert ID, e.g. `ALT-1001`."""
    q = alert_id.strip().upper()
    rec = ALERTS.get(q)
    if rec is None:
        known = ", ".join(k for k in ALERTS if not k.startswith("_"))
        return f"No alert found for {alert_id!r}. Known alert IDs: {known}."

    lines = [
        f"{rec['alert_id']} — {rec['title']}",
        f"  timestamp: {rec['timestamp']} · detector: {rec['detector']}",
        f"  asset_ids: {_fmt_list(rec.get('asset_ids'))}",
        f"  related_incident_ids: {_fmt_list(rec.get('related_incident_ids'))}",
        "  evidence:",
    ]
    lines.extend(f"    - {item}" for item in rec.get("evidence", []))
    lines.append("  [source: alerts.json]")
    return "\n".join(lines)


@tool
def get_asset_context(query: str) -> str:
    """Get asset context by asset ID or asset name. For multiple assets, pass a comma-separated list of
    IDs, e.g. `AST-IDP-01, AST-FIN-LAP-07`."""
    terms = [t.strip().lower() for t in query.replace(";", ",").split(",") if t.strip()]
    if not terms:
        return "No asset query provided."

    matches: list[dict] = []
    for term in terms:
        for asset_id, rec in ASSETS.items():
            if asset_id.startswith("_"):
                continue
            haystack = " ".join(
                [asset_id, rec["name"], rec["type"], rec["owner"], rec["environment"], rec["data_classification"]]
                + rec.get("tags", [])
            ).lower()
            if term == asset_id.lower() or term in haystack:
                if rec not in matches:
                    matches.append(rec)
    if not matches:
        known = ", ".join(k for k in ASSETS if not k.startswith("_"))
        return f"No asset context found for {query!r}. Known asset IDs: {known}."

    blocks = []
    for rec in matches:
        blocks.append(
            f"{rec['asset_id']} — {rec['name']} ({rec['type']})\n"
            f"  criticality: {rec['business_criticality']} · classification: {rec['data_classification']}\n"
            f"  owner: {rec['owner']} · environment: {rec['environment']} · exposure: {rec['exposure']}\n"
            f"  tags: {_fmt_list(rec.get('tags'))}\n"
            f"  notes: {rec['notes']}\n"
            f"  [source: assets.json]"
        )
    return "\n\n---\n\n".join(blocks)


@tool
def search_incident_history(query: str) -> str:
    """Search synthetic prior incidents by incident ID, asset ID, indicator, detector, tactic, title, or
    free-text query. Returns the best cited incident summaries."""
    q = query.strip().lower()
    if not q:
        return "No incident-history query provided."

    scored: list[tuple[int, dict]] = []
    tokens = [tok for tok in q.replace(",", " ").replace(";", " ").split() if len(tok) > 2]
    for rec in _records(INCIDENTS):
        haystack = " ".join(
            [
                rec["incident_id"],
                rec["title"],
                rec["severity"],
                rec["disposition"],
                rec["summary"],
                rec["lessons"],
            ]
            + rec.get("affected_assets", [])
            + rec.get("indicators", [])
        ).lower()
        score = 0
        if q in haystack:
            score += 5
        score += sum(1 for tok in tokens if tok in haystack)
        if score:
            scored.append((score, rec))
    scored.sort(key=lambda item: (-item[0], item[1]["incident_id"]))
    hits = [rec for _, rec in scored[:4]]
    if not hits:
        return "No matching prior incidents found."

    blocks = []
    for rec in hits:
        blocks.append(
            f"{rec['incident_id']} — {rec['title']} ({rec['date']})\n"
            f"  severity/disposition: {rec['severity']} / {rec['disposition']}\n"
            f"  affected_assets: {_fmt_list(rec.get('affected_assets'))}\n"
            f"  indicators: {_fmt_list(rec.get('indicators'))}\n"
            f"  summary: {rec['summary']}\n"
            f"  lessons: {rec['lessons']}\n"
            f"  [source: incidents.json]"
        )
    return "\n\n---\n\n".join(blocks)


@tool
def search_soc_kb(query: str) -> str:
    """Search the synthetic SOC knowledge base (severity rubric, triage playbook, indicators,
    false-positive guidance, containment guidance). Returns cited snippets by Markdown filename."""
    q = query.strip().lower()
    tokens = [tok for tok in q.replace(",", " ").replace(";", " ").split() if len(tok) > 2]
    hits: list[tuple[int, Path, str]] = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text()
        lower = text.lower()
        score = (5 if q and q in lower else 0) + sum(1 for tok in tokens if tok in lower)
        if score:
            # Return the most relevant short excerpt: first paragraph containing any query token, else prefix.
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            excerpt = next((p for p in paragraphs if any(tok in p.lower() for tok in tokens)), paragraphs[0] if paragraphs else "")
            hits.append((score, path, excerpt[:1400]))
    hits.sort(key=lambda item: (-item[0], item[1].name))
    if not hits:
        return "No relevant SOC KB passages found."
    return "\n\n---\n\n".join(f"[source: {path.name}]\n{excerpt}" for _, path, excerpt in hits[:4])


def alert_triage_tools() -> list:
    """The agent's four grounding tools: alert lookup, asset context, incident-history search, and SOC KB search."""
    return [get_alert, get_asset_context, search_incident_history, search_soc_kb]


class AlertTriageReport(BaseModel):
    """The triage report shape. Passed as `response_format=` so LangChain enforces it and returns a parsed
    object at `result["structured_response"]` — the schema lives here as code, NOT as a template in the
    prompt. (Mirrored visibly in the 01_build lab, where structured output is taught.)"""

    severity: Literal["Critical", "High", "Medium", "Low", "Informational"] = Field(
        description="Severity from the SOC rubric (severity_rubric.md)."
    )
    disposition: Literal[
        "confirmed_incident", "likely_incident", "needs_review", "benign_false_positive", "blocked_attempt"
    ] = Field(description="Exactly one triage disposition.")
    escalate: bool = Field(description="True when the rubric/containment requires human escalation or approval.")
    rationale: list[str] = Field(
        description="Grounded reasoning bullets, each citing alert evidence, asset context, or incident/KB guidance."
    )
    recommended_containment: list[str] = Field(
        description="Specific, scoped, reversible containment actions; empty if none is warranted."
    )
    uncertainty: str = Field(description="What remains unknown and the next non-destructive check.")
    citations: list[str] = Field(description="The fixture IDs / KB filenames used: alert ID, asset/incident IDs, kb *.md.")


class CampaignTriageReport(BaseModel):
    """Campaign-level verdict over SEVERAL related alerts (04_deep_agent capstone).

    The single-alert schema (AlertTriageReport) can't express correlation; these fields are what a
    single agent — holding every alert in one context — tends to get wrong, and what the coordinator
    deep agent gets right by delegating per alert and correlating clean summaries.
    """

    is_coordinated_campaign: bool = Field(
        description="True if the alerts are one coordinated campaign rather than independent events."
    )
    linked_alert_ids: list[str] = Field(description="Alert IDs judged part of the same campaign.")
    excluded_alert_ids: list[str] = Field(
        description="Alert IDs deliberately excluded as decoys/unrelated, with the reason in rationale."
    )
    pivot_entities: list[str] = Field(
        description="Shared accounts / source IPs / hosts / domains / incidents that link the alerts."
    )
    aggregate_severity: Literal["Critical", "High", "Medium", "Low", "Informational"] = Field(
        description="Severity of the campaign as a whole — may exceed any single alert."
    )
    aggregate_escalate: bool = Field(description="True when the campaign warrants escalation.")
    rationale: list[str] = Field(description="Grounded bullets citing per-alert evidence and the shared pivots.")
    recommended_containment: list[str] = Field(description="One consolidated, scoped, reversible action plan.")
    citations: list[str] = Field(description="Fixture IDs / KB filenames used: alert/asset/incident IDs, kb *.md.")


def build_agent(*, use_checkpointer: bool = False, interrupt_on: dict | None = None, name: str = "alert_triage_agent"):
    """Build the alert-triage agent.

    Args:
        use_checkpointer: attach an in-memory checkpointer for local memory/threads + HITL.
        interrupt_on: optional HumanInTheLoopMiddleware config mapping tool name -> approval policy.
        name: the graph's internal name.
    """
    system_prompt = get_prompt(PROMPT_NAME, fallback=PROMPT_PATH.read_text().strip())

    kwargs = {}
    if interrupt_on:
        from langchain.agents.middleware import HumanInTheLoopMiddleware

        kwargs["middleware"] = [HumanInTheLoopMiddleware(interrupt_on=interrupt_on)]
    if use_checkpointer:
        from langgraph.checkpoint.memory import MemorySaver

        kwargs["checkpointer"] = MemorySaver()

    return create_agent(
        get_model(),
        tools=alert_triage_tools(),
        system_prompt=system_prompt,
        response_format=AlertTriageReport,  # enforce the typed report shape (schema is code, not prompt text)
        name=name,
        **kwargs,
    )


def _subagents() -> list[dict]:
    """Deep-agent sub-agents for multi-source alert investigations."""
    return [
        {
            "name": "alert-enricher",
            "description": "Retrieve one alert and enrich its listed entities with asset context.",
            "system_prompt": (
                "You enrich a single alert. Use get_alert first, then get_asset_context for every listed "
                "asset. Return only cited evidence and asset context; do not decide final severity."
            ),
            "tools": [get_alert, get_asset_context],
        },
        {
            "name": "history-analyst",
            "description": "Find prior incidents and SOC KB guidance matching the alert's indicators and asset types.",
            "system_prompt": (
                "You compare alert indicators to prior incidents and SOC guidance. Use search_incident_history "
                "and search_soc_kb, cite incident IDs and KB filenames, and state whether the match raises or "
                "lowers severity."
            ),
            "tools": [search_incident_history, search_soc_kb],
        },
        {
            "name": "containment-planner",
            "description": "Plan scoped, reversible containment using the severity rubric and containment guide.",
            "system_prompt": (
                "You plan containment only. Use search_soc_kb for escalation and containment guidance. Recommend "
                "specific reversible actions and call out when human approval/escalation is required."
            ),
            "tools": [search_soc_kb, get_asset_context],
        },
    ]


def build_deep_agent(*, name: str = "alert_triage_deep_agent"):
    """Build the capstone coordinator that delegates enrichment, history matching, and containment planning."""
    from deepagents import create_deep_agent

    system_prompt = get_prompt(PROMPT_NAME, fallback=PROMPT_PATH.read_text().strip())
    coordinator_prompt = (
        system_prompt
        + "\n\nYou are the coordinator for multi-source SOC investigations. You have no direct data tools; "
        "delegate to alert-enricher, history-analyst, and containment-planner, then synthesize the final "
        "structured triage report. Do not invent facts absent from sub-agent results."
    )
    return create_deep_agent(
        model=get_model(),
        system_prompt=coordinator_prompt,
        subagents=_subagents(),
        response_format=AlertTriageReport,  # same typed report shape as the single agent
        name=name,
    )


def _campaign_investigator() -> dict:
    """The ONE sub-agent for the campaign capstone: fully investigates a single alert, end to end."""
    return {
        "name": "alert-investigator",
        "description": (
            "Fully investigate ONE alert: retrieve it, enrich every asset, and match prior incidents + "
            "SOC guidance. Report cited evidence and the accounts/IPs/hosts/domains it touches. Do not "
            "decide the campaign."
        ),
        "system_prompt": (
            "You investigate exactly one alert end to end. Use get_alert, then get_asset_context for "
            "every asset, then search_incident_history and search_soc_kb. Report cited evidence, the "
            "entities (accounts, source IPs, hosts, domains) it involves, and any prior-incident match. "
            "Do not decide whether alerts form a campaign — that is the coordinator's job."
        ),
        "tools": [get_alert, get_asset_context, search_incident_history, search_soc_kb],
    }


def build_deep_agent_v2(*, name: str = "alert_triage_campaign_agent"):
    """Capstone v2: a campaign coordinator over ONE reusable investigator sub-agent.

    Differs from build_deep_agent (v1): a single sub-agent fanned out per alert, file-based identity
    (AGENTS.md) + an on-demand skill loaded from a FilesystemBackend, and a correlation-aware
    CampaignTriageReport. The coordinator holds NO leaf tools — it plans, delegates, and correlates.
    """
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend

    base_prompt = get_prompt(PROMPT_NAME, fallback=PROMPT_PATH.read_text().strip())
    coordinator_prompt = (
        base_prompt
        + "\n\nYou coordinate multi-alert campaign investigations. Follow your AGENTS.md: delegate each "
        "alert to the alert-investigator sub-agent, correlate the findings on shared entities, exclude "
        "decoys, and synthesize one CampaignTriageReport. Do not invent facts absent from sub-agent results."
    )
    return create_deep_agent(
        model=get_model(),
        system_prompt=coordinator_prompt,
        subagents=[_campaign_investigator()],
        backend=FilesystemBackend(root_dir=str(AGENT_DIR), virtual_mode=True),  # /AGENTS.md, /skills/ resolve inside AGENT_DIR
        memory=["/AGENTS.md"],  # file-based coordinator identity
        skills=["/skills/"],  # on-demand campaign-correlation skill
        response_format=CampaignTriageReport,
        name=name,
    )


# Module-level compiled graphs for langgraph.json / LangGraph Studio.
# 1) alert_triage_agent          — plain ReAct-style triage agent and eval target.
# 2) alert_triage_agent_hitl     — same agent, with approval pause before asset-context lookup for HITL demos.
# 3) alert_triage_deep_agent     — v1 coordinator delegating to enrichment/history/containment sub-agents.
# 4) alert_triage_campaign_agent — v2 capstone: campaign coordinator over one investigator sub-agent.
graph = build_agent()
graph_hitl = build_agent(interrupt_on={"get_asset_context": True}, name="alert_triage_agent_hitl")
graph_deep = build_deep_agent()
graph_deep_v2 = build_deep_agent_v2()

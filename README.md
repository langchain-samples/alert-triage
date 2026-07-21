# SOC Alert-Triage Agent — a LangChain / LangGraph / LangSmith lab

A hands-on lab that builds a **Security Operations Center (SOC) alert-triage assistant** and walks it
through the full agent-engineering loop: **build → evaluate → orchestrate → deep agent → observe.**

The agent triages synthetic security alerts by grounding every decision in committed fixtures — alerts,
asset context, prior incidents, and a SOC knowledge base — and returns a typed triage report (severity,
disposition, escalation, cited rationale, containment). Everything runs on **synthetic, fictional data**
(no real incidents, PII, secrets, or live telemetry).

## What you'll build (5 notebooks)

| Notebook | You learn |
|---|---|
| `01_build.ipynb` | Create tools, wire an agent with `create_agent`, and enforce a typed report with `response_format`. |
| `02_evaluate.ipynb` | Seed an eval dataset and score the agent with LangSmith `evaluate()` (custom evaluators). |
| `03_orchestrate.ipynb` | Add middleware — human-in-the-loop approval, PII redaction, tool-call limits — and memory/threads. |
| `04_deep_agent.ipynb` | Scale to a **deep agent**: a coordinator delegating to sub-agents for multi-alert campaign correlation. |
| `05_observe.ipynb` | Production observability: tracing, online-eval run rules, and routing low scores to annotation queues. |

## Prerequisites

- **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/)
- An **OpenAI API key** (required)
- A **LangSmith API key** (optional — needed for evaluation, tracing, and the observability notebook)

## Quickstart

```bash
git clone https://github.com/langchain-samples/alert-triage.git
cd alert-triage
uv sync

cp .env.example .env      # then add your OPENAI_API_KEY (LangSmith key optional)

uv run jupyter lab notebooks/
```

Open `notebooks/01_build.ipynb` and run top to bottom, then continue through `05_observe.ipynb`.

### What needs a LangSmith key?

- **Runs without LangSmith:** `01_build`, `03_orchestrate` — the system prompt falls back to the
  committed `data/prompt.md`, and trace links are simply skipped.
- **Needs `LANGSMITH_API_KEY`:** `02_evaluate`, `04_deep_agent` (eval sections), `05_observe` — these
  seed datasets, run experiments, and create observability rules in **your own** workspace.

The eval datasets are committed as JSON (`evals/dataset_alert_triage*.json`) and seeded idempotently, so
re-running never duplicates. Notebook 05's live online-eval rules are opt-in behind `ENABLE_ONLINE_EVALS=1`.

## Run the graphs in LangGraph Studio

The agents are registered in `langgraph.json`, so you can open them in LangGraph Studio:

```bash
uv run langgraph dev
```

This serves four graphs: `alert_triage_agent`, `alert_triage_agent_hitl`, `alert_triage_deep_agent`,
and `alert_triage_campaign_agent`.

## Choosing the model

The model is set in one place — `utils/models.py` (default `openai:gpt-5.4-mini`). Override it without
touching code via `LABS_MODEL` in your `.env` (e.g. `LABS_MODEL="openai:gpt-4o-mini"`).

## Repository layout

```
alert-triage/
├── alert_triage_graph.py   # the deployable agent: tools, typed reports, and the 4 graphs
├── utils/                  # model selection, prompt loading, tracing, online-eval rules
├── evals/                  # dataset seeders + committed eval datasets (JSON)
├── data/                   # synthetic fixtures: alerts, assets, incidents, SOC KB, agent skills
├── notebooks/              # the 5 lab notebooks (+ images)
└── langgraph.json          # graph registry for LangGraph Studio
```

---

*Synthetic data notice: all alerts, assets, incidents, and knowledge-base content are fictional and
generated for teaching. Any resemblance to real systems, people, or events is coincidental.*

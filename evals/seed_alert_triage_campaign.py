"""Seed the alert-triage CAMPAIGN eval dataset into LangSmith (idempotent, offline-safe).

Companion to seed_alert_triage.py, for the 04_deep_agent capstone: multi-alert campaign examples
that exercise cross-alert correlation (where the deep agent beats the single agent). The committed
``dataset_alert_triage_campaign.json`` is the source of truth.

Run from the content root:
    uv run python evals/seed_alert_triage_campaign.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DATASET_NAME = "alert-triage-campaign-eval"
DATASET_PATH = Path(__file__).resolve().parent / "dataset_alert_triage_campaign.json"


def load_examples() -> list[dict]:
    raw = json.loads(DATASET_PATH.read_text())
    return [{"inputs": e["inputs"], "outputs": e["outputs"], "metadata": e.get("metadata", {})} for e in raw]


def seed_dataset(name: str = DATASET_NAME, *, refresh: bool = False) -> str | None:
    """Create/refresh the LangSmith campaign dataset from the committed JSON. Returns the name (or None offline)."""
    if not os.getenv("LANGSMITH_API_KEY"):
        print("LANGSMITH_API_KEY not set — skipping seed (the dataset JSON is committed locally).")
        return None

    from langsmith import Client

    client = Client()

    if refresh and client.has_dataset(dataset_name=name):
        client.delete_dataset(dataset_name=name)

    if client.has_dataset(dataset_name=name):
        ds = client.read_dataset(dataset_name=name)
        existing = sum(1 for _ in client.list_examples(dataset_id=ds.id))
        if existing:
            print(f"Dataset {name!r} already has {existing} examples — leaving as is (pass refresh=True to rebuild).")
            return name
    else:
        ds = client.create_dataset(
            dataset_name=name,
            description="Multi-alert campaign correlation over synthetic SOC fixtures (alert-triage deep-agent capstone).",
        )

    examples = load_examples()
    client.create_examples(dataset_id=ds.id, examples=examples)
    print(f"Seeded {len(examples)} examples into LangSmith dataset {name!r}.")
    return name


if __name__ == "__main__":
    seed_dataset()

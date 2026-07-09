"""REST API gateway for the multi-agent banking pipeline.

Wraps the file-based pipeline (`integrator.py`) behind HTTP endpoints so
transactions can be submitted and results retrieved via ordinary HTTP calls
instead of invoking `integrator.py` by hand. Every request operates on the
same `shared/{input,processing,output,results}/` directory tree the CLI and
the `pipeline-status` MCP server already use — this is a thin adapter over
the existing pipeline, not a second implementation of it.

Run with: uvicorn api.server:app
Configure the shared/ root via the PIPELINE_SHARED_ROOT env var (default
"shared"), so tests and demos can point it at an isolated directory.

The policy rule engine's configuration (normally hand-edited at
agents/rules_config.json) can also be read and replaced over HTTP via
GET/PUT /rules — see RuleIn below for the shape agents/rule_engine.py
expects.
"""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

import integrator
from agents import rule_engine
from agents.common import ensure_shared_dirs, read_json, write_json

app = FastAPI(title="Banking Pipeline API", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"


def get_shared_root() -> Path:
    return Path(os.environ.get("PIPELINE_SHARED_ROOT", "shared"))


def get_rules_path() -> Path:
    """The exact file agents/rule_engine.py reads by default — kept as a
    live attribute lookup (not a local alias) so tests can monkeypatch
    rule_engine.DEFAULT_RULES_PATH and have both this endpoint and actual
    pipeline runs observe the same override."""
    return rule_engine.DEFAULT_RULES_PATH


class TransactionIn(BaseModel):
    transaction_id: str
    timestamp: str
    source_account: str
    destination_account: str
    amount: str
    currency: str
    transaction_type: str
    description: Optional[str] = None
    metadata: Optional[dict] = None


class RuleIn(BaseModel):
    id: str
    field: str
    operator: Literal["eq", "neq", "in", "not_in"]
    value: Any = None
    min_amount: Optional[str] = None
    action: Literal["reject", "flag"]
    reason: str
    description: Optional[str] = None

    @field_validator("min_amount")
    @classmethod
    def _min_amount_must_be_decimal(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"min_amount '{value}' is not a valid decimal string") from exc
        return value


class RulesConfigIn(BaseModel):
    rules: list[RuleIn]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/transactions", status_code=201)
def submit_transaction(transaction: TransactionIn) -> dict:
    """Run one transaction through the full pipeline and return its terminal result."""
    shared_root = get_shared_root()
    paths = ensure_shared_dirs(shared_root)
    log_path = paths["results"] / "pipeline_run.log"

    raw = transaction.model_dump(exclude_none=True)
    final_message = integrator.process_transaction(raw, paths, log_path)
    integrator.rebuild_summary(shared_root)
    return final_message


@app.get("/transactions")
def list_transactions() -> dict:
    outcomes = integrator.list_results(get_shared_root())
    return {"total": len(outcomes), "transactions": outcomes}


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str) -> dict:
    result = integrator.load_result(get_shared_root(), transaction_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No result on file for '{transaction_id}'.")
    return result


@app.get("/summary")
def get_summary() -> dict:
    summary_path = get_shared_root() / "results" / "pipeline_summary.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="No pipeline run found yet.")
    return read_json(summary_path)


@app.get("/rules")
def get_rules() -> dict:
    """Return the policy rule engine's current configuration."""
    path = get_rules_path()
    if not path.exists():
        return {"rules": []}
    return read_json(path)


@app.put("/rules")
def update_rules(config: RulesConfigIn) -> dict:
    """Replace the policy rule engine's configuration; takes effect on the
    next transaction submitted (rule_engine.py reloads the file every time,
    it never caches rules in memory)."""
    payload = config.model_dump(exclude_none=True)
    write_json(get_rules_path(), payload)
    return payload


# Mounted last so it never shadows the API routes above — Starlette matches
# routes in registration order, and this only catches paths none of them
# claimed (chiefly "/", serving static/index.html, the demo console).
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

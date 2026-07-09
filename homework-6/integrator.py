#!/usr/bin/env python3
"""Orchestrator for the multi-agent banking pipeline.

Loads sample-transactions.json, wraps each record as a standard pipeline
message, and runs it through:

    transaction_validator -> fraud_detector -> compliance_checker

Every intermediate message is persisted under shared/processing/ and
shared/output/ for auditability; each transaction's terminal outcome lands
in shared/results/{transaction_id}.json. A run-level pipeline_summary.json
and a pipeline_run.log audit trail are also written to shared/results/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

from agents import compliance_checker, fraud_detector, rule_engine, transaction_validator
from agents.common import ensure_shared_dirs, new_message, read_json, write_json

PIPELINE = (
    ("transaction_validator", transaction_validator),
    ("fraud_detector", fraud_detector),
    ("rule_engine", rule_engine),
    ("compliance_checker", compliance_checker),
)


def clear_shared(shared_root: Path) -> None:
    for name in ("input", "processing", "output", "results"):
        d = shared_root / name
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)


def _outcome_status(data: dict) -> str:
    """Return the terminal status field regardless of which agent stopped the flow."""
    return data.get("final_status") or data.get("status") or "unknown"


def process_transaction(raw: dict, paths: dict, log_path: Path) -> dict:
    transaction_id = raw.get("transaction_id", "UNKNOWN")

    write_json(paths["input"] / f"{transaction_id}.json", raw)

    message = new_message("integrator", "transaction_validator", "transaction", dict(raw))

    for agent_name, agent_module in PIPELINE:
        write_json(paths["processing"] / f"{transaction_id}_{agent_name}.json", message)
        message = agent_module.process_message(message, log_path=log_path)
        write_json(paths["output"] / f"{transaction_id}_{agent_name}.json", message)
        if message.get("target_agent") is None:
            break

    write_json(paths["results"] / f"{transaction_id}.json", message)
    return message


def _outcome_from_result(data: dict) -> dict:
    return {
        "transaction_id": data.get("transaction_id"),
        "status": _outcome_status(data),
        "reason": data.get("reason") or data.get("rejection_reason") or data.get("policy_reason"),
        "risk_score": data.get("risk_score"),
    }


def list_results(shared_root: Path) -> list[dict]:
    """Return one outcome dict per terminal result file in shared/results/."""
    results_dir = shared_root / "results"
    if not results_dir.exists():
        return []
    outcomes = []
    for path in sorted(results_dir.glob("TXN*.json")):
        message = read_json(path)
        outcomes.append(_outcome_from_result(message.get("data", {})))
    return outcomes


def load_result(shared_root: Path, transaction_id: str) -> Optional[dict]:
    """Return the raw terminal message for one transaction, or None if absent."""
    path = shared_root / "results" / f"{transaction_id}.json"
    if not path.exists():
        return None
    return read_json(path)


def rebuild_summary(shared_root: Path) -> dict:
    """Recompute pipeline_summary.json from every result file on disk.

    Used after both a full batch run and a single ad-hoc API submission, so
    the summary always reflects the current contents of shared/results/.
    """
    outcomes = list_results(shared_root)
    status_counts = Counter(o["status"] for o in outcomes)
    summary = {
        "total_transactions": len(outcomes),
        "status_counts": dict(status_counts),
        "outcomes": outcomes,
    }
    write_json(shared_root / "results" / "pipeline_summary.json", summary)
    return summary


def run_pipeline(input_path: Path, shared_root: Path, clear: bool = False) -> dict:
    if clear:
        clear_shared(shared_root)
    paths = ensure_shared_dirs(shared_root)
    log_path = paths["results"] / "pipeline_run.log"

    transactions = json.loads(input_path.read_text(encoding="utf-8"))

    for raw in transactions:
        process_transaction(raw, paths, log_path)

    return rebuild_summary(shared_root)


def print_summary(summary: dict) -> None:
    print("\n=== Pipeline Summary ===")
    print(f"Total transactions: {summary['total_transactions']}")
    for status, count in summary["status_counts"].items():
        print(f"  {status}: {count}")
    print("\n=== Per-transaction outcomes ===")
    for o in summary["outcomes"]:
        reason = f" ({o['reason']})" if o.get("reason") else ""
        risk = f" risk={o['risk_score']}" if o.get("risk_score") is not None else ""
        print(f"  {o['transaction_id']}: {o['status']}{risk}{reason}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the multi-agent banking pipeline end-to-end.")
    parser.add_argument("--input", default="sample-transactions.json", help="Path to raw transactions JSON.")
    parser.add_argument("--shared-root", default="shared", help="Root of the shared/ directory tree.")
    parser.add_argument("--clear", action="store_true", help="Wipe shared/ subdirectories before running.")
    args = parser.parse_args(argv)

    summary = run_pipeline(Path(args.input), Path(args.shared_root), clear=args.clear)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())

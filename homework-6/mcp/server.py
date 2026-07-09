"""Custom FastMCP server making the banking pipeline queryable.

Exposes:
  - tool `get_transaction_status(transaction_id)`
  - tool `list_pipeline_results()`
  - resource `pipeline://summary`

All three are read-only and resolve paths relative to this project's
`shared/results/` directory, so the pipeline must have been run at least
once (e.g. via `python integrator.py` or the `/run-pipeline` skill) before
these return anything.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("pipeline-status-server")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "shared" / "results"


def _load_result(transaction_id: str) -> dict | None:
    path = RESULTS_DIR / f"{transaction_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@mcp.tool()
def get_transaction_status(transaction_id: str) -> dict:
    """Return the current status of a single transaction from shared/results/.

    Returns a not-found payload (rather than raising) for unknown IDs so the
    caller can branch on `found` without handling an exception.
    """
    result = _load_result(transaction_id)
    if result is None:
        return {"found": False, "transaction_id": transaction_id, "message": "No result on file for this transaction."}

    data = result.get("data", {})
    return {
        "found": True,
        "transaction_id": transaction_id,
        "status": data.get("final_status") or data.get("status"),
        "reason": data.get("reason") or data.get("rejection_reason"),
        "risk_score": data.get("risk_score"),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
    }


@mcp.tool()
def list_pipeline_results() -> dict:
    """Return a summary of every processed transaction in shared/results/."""
    if not RESULTS_DIR.exists():
        return {"total": 0, "transactions": []}

    transactions = []
    for path in sorted(RESULTS_DIR.glob("TXN*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        data = result.get("data", {})
        transactions.append(
            {
                "transaction_id": data.get("transaction_id"),
                "status": data.get("final_status") or data.get("status"),
                "reason": data.get("reason") or data.get("rejection_reason"),
            }
        )
    return {"total": len(transactions), "transactions": transactions}


@mcp.resource("pipeline://summary")
def pipeline_summary() -> str:
    """Return the latest pipeline run summary as human-readable text."""
    summary_path = RESULTS_DIR / "pipeline_summary.json"
    if not summary_path.exists():
        return "No pipeline run found yet. Run `python integrator.py` first."

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    lines = [
        f"Total transactions: {summary.get('total_transactions', 0)}",
        "Status counts:",
    ]
    for status, count in summary.get("status_counts", {}).items():
        lines.append(f"  - {status}: {count}")
    lines.append("Per-transaction outcomes:")
    for outcome in summary.get("outcomes", []):
        reason = f" ({outcome['reason']})" if outcome.get("reason") else ""
        lines.append(f"  - {outcome['transaction_id']}: {outcome['status']}{reason}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()

"""Agent 4 of the pipeline: compliance disposition (terminal agent).

Makes the final call on a transaction: rejects unknown transaction types,
flags cross-border transactions and anything the fraud detector or rule
engine already flagged for manual review, and approves everything else.
Its output is written directly to shared/results/ — it does not forward
to another agent.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from agents.common import (
    HOME_COUNTRY,
    KNOWN_TRANSACTION_TYPES,
    is_known_transaction_type,
    log_event,
    new_message,
)

AGENT_NAME = "compliance_checker"


def process_message(message: dict, log_path: Optional[Path] = None) -> dict:
    """Assign a final disposition and return the terminal message."""
    data = dict(message.get("data", {}))
    transaction_id = data.get("transaction_id", "UNKNOWN")

    if not is_known_transaction_type(data.get("transaction_type")):
        data["final_status"] = "rejected"
        data["reason"] = (
            f"unknown_transaction_type: '{data.get('transaction_type')}' not in "
            f"{sorted(KNOWN_TRANSACTION_TYPES)}"
        )
        log_event(AGENT_NAME, transaction_id, "rejected", detail=data["reason"], log_path=log_path)
        return new_message(AGENT_NAME, None, "transaction", data)

    country = (data.get("metadata") or {}).get("country")
    is_cross_border = bool(country) and country != HOME_COUNTRY
    fraud_flagged = data.get("status") == "flagged_for_review"
    policy_flags = data.get("policy_flags") or []

    if fraud_flagged or is_cross_border or policy_flags:
        reasons = []
        if fraud_flagged:
            reasons.append("fraud_risk_flagged")
        if is_cross_border:
            reasons.append("cross_border")
        if policy_flags:
            reasons.append("policy_rule_flagged")
        data["final_status"] = "flagged_for_review"
        data["reason"] = ",".join(reasons)
    else:
        data["final_status"] = "approved"
        data["reason"] = "no_issues_found"

    log_event(AGENT_NAME, transaction_id, data["final_status"], detail=data["reason"], log_path=log_path)
    return new_message(AGENT_NAME, None, "transaction", data)

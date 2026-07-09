"""Agent 2 of the pipeline: fraud risk scoring.

Scores a validated transaction on high value, unusual timing, cross-border,
and wire-transfer signals. Always forwards to the compliance checker — the
fraud score is advisory input to the final disposition, not a rejection by
itself.
"""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Optional

from agents.common import (
    FRAUD_FLAG_THRESHOLD,
    HIGH_VALUE_THRESHOLD,
    HOME_COUNTRY,
    OFF_HOURS_END,
    OFF_HOURS_START,
    log_event,
    new_message,
    parse_amount,
    parse_hour_utc,
)

AGENT_NAME = "fraud_detector"

SIGNAL_WEIGHTS = {
    "high_value": 0.8,
    "off_hours": 0.3,
    "cross_border": 0.3,
    "wire_transfer": 0.1,
}


def _compute_risk(data: dict) -> tuple[float, list[str]]:
    factors: list[str] = []

    amount = parse_amount(data.get("amount")) or Decimal("0")
    if amount > HIGH_VALUE_THRESHOLD:
        factors.append("high_value")

    hour = parse_hour_utc(data.get("timestamp", ""))
    if hour is not None and OFF_HOURS_START <= hour < OFF_HOURS_END:
        factors.append("off_hours")

    country = (data.get("metadata") or {}).get("country")
    if country and country != HOME_COUNTRY:
        factors.append("cross_border")

    if data.get("transaction_type") == "wire_transfer":
        factors.append("wire_transfer")

    score = min(1.0, sum(SIGNAL_WEIGHTS[f] for f in factors))
    return score, factors


def process_message(message: dict, log_path: Optional[Path] = None) -> dict:
    """Score a validated transaction and forward it to compliance_checker."""
    data = dict(message.get("data", {}))
    transaction_id = data.get("transaction_id", "UNKNOWN")

    risk_score, risk_factors = _compute_risk(data)
    data["risk_score"] = round(risk_score, 2)
    data["risk_factors"] = risk_factors
    data["status"] = "flagged_for_review" if risk_score > FRAUD_FLAG_THRESHOLD else "fraud_cleared"

    log_event(
        AGENT_NAME,
        transaction_id,
        data["status"],
        detail=f"risk_score={data['risk_score']} factors={','.join(risk_factors) or 'none'}",
        log_path=log_path,
    )
    return new_message(AGENT_NAME, "compliance_checker", "transaction", data)

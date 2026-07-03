"""Agent 1 of the pipeline: structural transaction validation.

Checks required fields, a positive parseable amount, and an ISO 4217
currency code. Rejects everything else with a specific reason before any
downstream agent (fraud detector, compliance checker) sees the message.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.common import (  # noqa: E402
    REQUIRED_TRANSACTION_FIELDS,
    is_valid_currency,
    log_event,
    mask_account,
    new_message,
    parse_amount,
)

AGENT_NAME = "transaction_validator"


def process_message(message: dict, log_path: Optional[Path] = None) -> dict:
    """Validate an inbound transaction message; return the outbound message.

    Inbound `message["data"]` is expected to be a raw transaction record.
    On success, the outbound message is targeted at "fraud_detector" with
    `data.status = "validated"`. On failure, `target_agent` is None (the
    message is terminal) and `data.status = "rejected"` with a
    `rejection_reason`.
    """
    data = dict(message.get("data", {}))
    transaction_id = data.get("transaction_id", "UNKNOWN")

    missing = [f for f in REQUIRED_TRANSACTION_FIELDS if not data.get(f)]
    if missing:
        return _reject(
            data,
            transaction_id,
            f"missing_required_fields: {', '.join(missing)}",
            log_path,
        )

    amount = parse_amount(data.get("amount"))
    if amount is None:
        return _reject(
            data,
            transaction_id,
            f"invalid_amount: '{data.get('amount')}' is not a positive decimal",
            log_path,
        )

    if not is_valid_currency(data.get("currency")):
        return _reject(
            data,
            transaction_id,
            f"invalid_currency: '{data.get('currency')}' is not an ISO 4217 code we accept",
            log_path,
        )

    data["amount"] = str(amount)
    data["status"] = "validated"
    log_event(
        AGENT_NAME,
        transaction_id,
        "validated",
        detail=(
            f"amount={amount} {data.get('currency')} "
            f"src={mask_account(data.get('source_account'))} "
            f"dst={mask_account(data.get('destination_account'))}"
        ),
        log_path=log_path,
    )
    return new_message(AGENT_NAME, "fraud_detector", "transaction", data)


def _reject(data: dict, transaction_id: str, reason: str, log_path: Optional[Path]) -> dict:
    data["status"] = "rejected"
    data["rejection_reason"] = reason
    log_event(AGENT_NAME, transaction_id, "rejected", detail=reason, log_path=log_path)
    return new_message(AGENT_NAME, None, "transaction", data)


def validate_dry_run(transactions: list[dict]) -> dict:
    """Run structural validation only, without touching fraud/compliance agents."""
    results = []
    for raw in transactions:
        outbound = process_message({"data": raw})
        results.append(outbound["data"])
    valid = [r for r in results if r.get("status") == "validated"]
    invalid = [r for r in results if r.get("status") == "rejected"]
    return {
        "total": len(results),
        "valid_count": len(valid),
        "invalid_count": len(invalid),
        "invalid": [
            {"transaction_id": r.get("transaction_id"), "reason": r.get("rejection_reason")}
            for r in invalid
        ],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate transactions without running the full pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Only run structural validation and print a report.")
    parser.add_argument(
        "--input",
        default="sample-transactions.json",
        help="Path to a JSON array of raw transactions (default: sample-transactions.json).",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    transactions = json.loads(input_path.read_text(encoding="utf-8"))

    if args.dry_run:
        report = validate_dry_run(transactions)
        print(json.dumps(report, indent=2))
        return 0

    print("Run with --dry-run to validate without executing the full pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

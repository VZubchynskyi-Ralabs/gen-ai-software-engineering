"""Agent 3 of the pipeline: configurable policy rule engine.

Evaluates a validated, risk-scored transaction against a declarative rule
set loaded from `agents/rules_config.json` (or an override path) — no
business rule lives in this file's code, only the generic evaluator. A
matching `reject` rule makes this a terminal agent (mirrors
`transaction_validator`'s rejection pattern); matching `flag` rules are
collected as advisory input for the compliance checker, same spirit as the
fraud detector's risk score.
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.common import log_event, new_message, parse_amount  # noqa: E402

AGENT_NAME = "rule_engine"

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules_config.json"


def load_rules(rules_path: Optional[Path] = None, log_path: Optional[Path] = None) -> list[dict]:
    """Load the declarative rule set. Returns [] (never raises) if the
    config is missing or malformed, so a bad config degrades to "no rules"
    rather than crashing the pipeline."""
    path = rules_path or DEFAULT_RULES_PATH
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        log_event(
            AGENT_NAME,
            "N/A",
            "config_load_failed",
            detail=f"{path.name}: {exc.__class__.__name__}",
            log_path=log_path,
        )
        return []
    return config.get("rules", [])


def _get_field(data: dict, dotted_field: str) -> Any:
    value: Any = data
    for part in dotted_field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches(rule: dict, data: dict) -> bool:
    field_value = _get_field(data, rule["field"])
    operator = rule["operator"]
    target = rule.get("value")

    if operator == "eq":
        condition_met = field_value == target
    elif operator == "neq":
        condition_met = field_value != target
    elif operator == "in":
        condition_met = field_value in (target or [])
    elif operator == "not_in":
        condition_met = field_value not in (target or [])
    else:
        condition_met = False

    if not condition_met:
        return False

    min_amount = rule.get("min_amount")
    if min_amount is not None:
        amount = parse_amount(data.get("amount"))
        if amount is None or amount < Decimal(min_amount):
            return False

    return True


def evaluate_rules(data: dict, rules: list[dict]) -> tuple[Optional[dict], list[dict]]:
    """Return (reject_rule, matched_flag_rules). The first matching `reject`
    rule short-circuits evaluation; every matching `flag` rule is collected."""
    flag_rules: list[dict] = []
    for rule in rules:
        if not _matches(rule, data):
            continue
        if rule.get("action") == "reject":
            return rule, flag_rules
        if rule.get("action") == "flag":
            flag_rules.append(rule)
    return None, flag_rules


def process_message(
    message: dict,
    log_path: Optional[Path] = None,
    rules_path: Optional[Path] = None,
) -> dict:
    """Apply the configured policy rules; return the outbound message."""
    data = dict(message.get("data", {}))
    transaction_id = data.get("transaction_id", "UNKNOWN")

    rules = load_rules(rules_path, log_path=log_path)
    reject_rule, flag_rules = evaluate_rules(data, rules)

    if reject_rule is not None:
        data["status"] = "policy_rejected"
        data["policy_reason"] = reject_rule["reason"]
        log_event(AGENT_NAME, transaction_id, "policy_rejected", detail=reject_rule["reason"], log_path=log_path)
        return new_message(AGENT_NAME, None, "transaction", data)

    if flag_rules:
        data["policy_flags"] = [rule["reason"] for rule in flag_rules]
        log_event(
            AGENT_NAME,
            transaction_id,
            "policy_flagged",
            detail=",".join(data["policy_flags"]),
            log_path=log_path,
        )
    else:
        log_event(AGENT_NAME, transaction_id, "policy_cleared", detail="no_rules_matched", log_path=log_path)

    return new_message(AGENT_NAME, "compliance_checker", "transaction", data)


def validate_dry_run(transactions: list[dict], rules_path: Optional[Path] = None) -> dict:
    """Run the rule engine only, without touching fraud/compliance agents."""
    results = []
    for raw in transactions:
        outbound = process_message({"data": raw}, rules_path=rules_path)
        results.append(outbound["data"])
    rejected = [r for r in results if r.get("status") == "policy_rejected"]
    flagged = [r for r in results if r.get("policy_flags")]
    return {
        "total": len(results),
        "rejected_count": len(rejected),
        "flagged_count": len(flagged),
        "rejected": [
            {"transaction_id": r.get("transaction_id"), "reason": r.get("policy_reason")} for r in rejected
        ],
        "flagged": [
            {"transaction_id": r.get("transaction_id"), "flags": r.get("policy_flags")} for r in flagged
        ],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate transactions against the policy rule engine.")
    parser.add_argument("--dry-run", action="store_true", help="Only run the rule engine and print a report.")
    parser.add_argument(
        "--input",
        default="sample-transactions.json",
        help="Path to a JSON array of raw transactions (default: sample-transactions.json).",
    )
    parser.add_argument(
        "--rules",
        default=None,
        help="Path to an alternate rules_config.json (default: agents/rules_config.json).",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    transactions = json.loads(input_path.read_text(encoding="utf-8"))
    rules_path = Path(args.rules) if args.rules else None

    if args.dry_run:
        report = validate_dry_run(transactions, rules_path=rules_path)
        print(json.dumps(report, indent=2))
        return 0

    print("Run with --dry-run to evaluate rules without executing the full pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

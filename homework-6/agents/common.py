"""Shared utilities for all banking-pipeline agents.

Every agent communicates through JSON message files with the envelope
shape defined in `specification.md`. This module holds the conventions
every agent must follow: monetary parsing, currency/type allow-lists,
structured audit logging, and the shared/ directory layout.
"""
from __future__ import annotations

import json
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

# --- Domain constants -------------------------------------------------

VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}

KNOWN_TRANSACTION_TYPES = {
    "transfer",
    "wire_transfer",
    "refund",
    "payment",
    "deposit",
    "withdrawal",
}

REQUIRED_TRANSACTION_FIELDS = (
    "transaction_id",
    "timestamp",
    "source_account",
    "destination_account",
    "amount",
    "currency",
    "transaction_type",
)

HIGH_VALUE_THRESHOLD = Decimal("10000.00")
OFF_HOURS_START = 0   # 00:00 UTC
OFF_HOURS_END = 5     # 05:00 UTC
HOME_COUNTRY = "US"
FRAUD_FLAG_THRESHOLD = 0.7

SHARED_SUBDIRS = ("input", "processing", "output", "results")


# --- Time & IDs ---------------------------------------------------------

def now_iso(clock: Optional[Any] = None) -> str:
    """Return current UTC time as an ISO 8601 string with a 'Z' suffix."""
    from datetime import datetime, timezone

    dt = clock() if clock is not None else datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def new_message_id() -> str:
    return str(uuid.uuid4())


# --- Money & validation ---------------------------------------------------

def parse_amount(raw: Any) -> Optional[Decimal]:
    """Parse a monetary amount from its original string form.

    Returns None (never raises) if the value isn't a valid, positive
    decimal number. Never accepts a float directly to avoid binary
    rounding error leaking into the Decimal.
    """
    if isinstance(raw, float):
        return None
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if value <= 0:
        return None
    return value


def is_valid_currency(code: Any) -> bool:
    return isinstance(code, str) and code.upper() in VALID_CURRENCIES


def is_known_transaction_type(value: Any) -> bool:
    return isinstance(value, str) and value in KNOWN_TRANSACTION_TYPES


def mask_account(account: Optional[str]) -> str:
    """Mask an account identifier for safe logging (never log PII raw)."""
    if not account:
        return "****"
    tail = account[-4:] if len(account) >= 4 else account
    return f"***{tail}"


def parse_hour_utc(timestamp: str) -> Optional[int]:
    from datetime import datetime

    try:
        cleaned = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned).hour
    except (ValueError, AttributeError):
        return None


# --- Message envelope -----------------------------------------------------

def new_message(
    source_agent: str,
    target_agent: Optional[str],
    message_type: str,
    data: dict,
    clock: Optional[Any] = None,
) -> dict:
    return {
        "message_id": new_message_id(),
        "timestamp": now_iso(clock),
        "source_agent": source_agent,
        "target_agent": target_agent,
        "message_type": message_type,
        "data": data,
    }


# --- Structured audit logging ----------------------------------------------

def log_event(
    agent: str,
    transaction_id: str,
    outcome: str,
    detail: str = "",
    log_path: Optional[Path] = None,
    clock: Optional[Any] = None,
) -> dict:
    """Emit one structured audit-log line (stdout + optional file).

    `detail` must never contain raw account numbers or names — callers
    should pre-mask any PII before passing it in.
    """
    entry = {
        "timestamp": now_iso(clock),
        "agent": agent,
        "transaction_id": transaction_id,
        "outcome": outcome,
        "detail": detail,
    }
    line = json.dumps(entry, sort_keys=True)
    print(line)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return entry


# --- shared/ directory layout -----------------------------------------------

def ensure_shared_dirs(root: Path) -> dict:
    """Create shared/{input,processing,output,results} under root; return paths."""
    paths = {}
    for name in SHARED_SUBDIRS:
        p = root / name
        p.mkdir(parents=True, exist_ok=True)
        paths[name] = p
    return paths


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

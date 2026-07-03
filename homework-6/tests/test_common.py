from decimal import Decimal
from pathlib import Path

from agents.common import (
    ensure_shared_dirs,
    is_known_transaction_type,
    is_valid_currency,
    log_event,
    mask_account,
    new_message,
    now_iso,
    parse_amount,
    parse_hour_utc,
    read_json,
    write_json,
)


def test_parse_amount_valid_string():
    assert parse_amount("1500.00") == Decimal("1500.00")


def test_parse_amount_rejects_float():
    assert parse_amount(1500.00) is None


def test_parse_amount_rejects_negative():
    assert parse_amount("-100.00") is None


def test_parse_amount_rejects_zero():
    assert parse_amount("0") is None


def test_parse_amount_rejects_garbage():
    assert parse_amount("not-a-number") is None


def test_is_valid_currency_accepts_known():
    assert is_valid_currency("USD")
    assert is_valid_currency("eur")


def test_is_valid_currency_rejects_unknown():
    assert not is_valid_currency("XYZ")
    assert not is_valid_currency(None)


def test_is_known_transaction_type():
    assert is_known_transaction_type("wire_transfer")
    assert not is_known_transaction_type("teleport")


def test_mask_account_masks_all_but_last_four():
    assert mask_account("ACC-1001") == "***1001"


def test_mask_account_handles_missing():
    assert mask_account(None) == "****"
    assert mask_account("") == "****"


def test_parse_hour_utc():
    assert parse_hour_utc("2026-03-16T02:47:00Z") == 2


def test_parse_hour_utc_invalid():
    assert parse_hour_utc("not-a-timestamp") is None


def test_now_iso_format():
    ts = now_iso()
    assert ts.endswith("Z")
    assert "T" in ts


def test_new_message_shape():
    msg = new_message("agent_a", "agent_b", "transaction", {"k": "v"})
    assert msg["source_agent"] == "agent_a"
    assert msg["target_agent"] == "agent_b"
    assert msg["message_type"] == "transaction"
    assert msg["data"] == {"k": "v"}
    assert msg["message_id"]
    assert msg["timestamp"].endswith("Z")


def test_log_event_writes_to_file(tmp_path: Path):
    log_path = tmp_path / "run.log"
    entry = log_event("test_agent", "TXN001", "validated", detail="ok", log_path=log_path)
    assert entry["agent"] == "test_agent"
    content = log_path.read_text(encoding="utf-8")
    assert "TXN001" in content
    assert "validated" in content


def test_ensure_shared_dirs_creates_all(tmp_path: Path):
    paths = ensure_shared_dirs(tmp_path)
    for name in ("input", "processing", "output", "results"):
        assert paths[name].is_dir()


def test_write_json_and_read_json_roundtrip(tmp_path: Path):
    path = tmp_path / "sub" / "file.json"
    write_json(path, {"a": 1})
    assert read_json(path) == {"a": 1}

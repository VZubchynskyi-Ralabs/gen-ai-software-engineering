from agents.transaction_validator import main, process_message, validate_dry_run

BASE_TXN = {
    "transaction_id": "TXN100",
    "timestamp": "2026-03-16T09:00:00Z",
    "source_account": "ACC-1001",
    "destination_account": "ACC-2001",
    "amount": "1500.00",
    "currency": "USD",
    "transaction_type": "transfer",
}


def _message(overrides=None):
    data = dict(BASE_TXN)
    if overrides:
        data.update(overrides)
    return {"data": data}


def test_validate_accepts_valid_transaction():
    outbound = process_message(_message())
    assert outbound["data"]["status"] == "validated"
    assert outbound["target_agent"] == "fraud_detector"


def test_validate_rejects_missing_required_field():
    data = dict(BASE_TXN)
    del data["currency"]
    outbound = process_message({"data": data})
    assert outbound["data"]["status"] == "rejected"
    assert "missing_required_fields" in outbound["data"]["rejection_reason"]
    assert outbound["target_agent"] is None


def test_validate_rejects_invalid_currency():
    outbound = process_message(_message({"currency": "XYZ"}))
    assert outbound["data"]["status"] == "rejected"
    assert "invalid_currency" in outbound["data"]["rejection_reason"]


def test_validate_rejects_negative_amount():
    outbound = process_message(_message({"amount": "-100.00"}))
    assert outbound["data"]["status"] == "rejected"
    assert "invalid_amount" in outbound["data"]["rejection_reason"]


def test_validate_rejects_non_numeric_amount():
    outbound = process_message(_message({"amount": "abc"}))
    assert outbound["data"]["status"] == "rejected"
    assert "invalid_amount" in outbound["data"]["rejection_reason"]


def test_validate_normalizes_amount_to_string_decimal():
    outbound = process_message(_message({"amount": "1500"}))
    assert outbound["data"]["amount"] == "1500"


def test_validate_dry_run_report_shape(sample_transactions):
    report = validate_dry_run(sample_transactions)
    assert report["total"] == 8
    assert report["valid_count"] == 6
    assert report["invalid_count"] == 2
    rejected_ids = {r["transaction_id"] for r in report["invalid"]}
    assert rejected_ids == {"TXN006", "TXN007"}


def test_main_dry_run_prints_report(sample_transactions_file, capsys):
    exit_code = main(["--dry-run", "--input", str(sample_transactions_file)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"total": 8' in captured.out


def test_main_without_dry_run_prints_hint(sample_transactions_file, capsys):
    exit_code = main(["--input", str(sample_transactions_file)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "--dry-run" in captured.out

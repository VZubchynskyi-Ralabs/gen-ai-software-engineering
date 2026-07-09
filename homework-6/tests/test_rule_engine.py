import json
from pathlib import Path

from agents.rule_engine import _get_field, load_rules, main, process_message, validate_dry_run

BASE_TXN = {
    "transaction_id": "TXN100",
    "timestamp": "2026-03-16T09:00:00Z",
    "source_account": "ACC-1001",
    "destination_account": "ACC-2001",
    "amount": "1500.00",
    "currency": "USD",
    "transaction_type": "transfer",
    "status": "fraud_cleared",
    "risk_score": 0.0,
    "risk_factors": [],
    "metadata": {"channel": "online", "country": "US"},
}


def _message(overrides=None):
    data = dict(BASE_TXN)
    if overrides:
        data.update(overrides)
    return {"data": data}


def test_sanctioned_country_is_rejected():
    outbound = process_message(_message({"metadata": {"channel": "online", "country": "IR"}}))
    assert outbound["target_agent"] is None
    assert outbound["data"]["status"] == "policy_rejected"
    assert outbound["data"]["policy_reason"] == "sanctioned_country"


def test_large_withdrawal_is_flagged():
    outbound = process_message(
        _message({"transaction_type": "withdrawal", "amount": "6000.00"})
    )
    assert outbound["target_agent"] == "compliance_checker"
    assert outbound["data"]["policy_flags"] == ["large_cash_withdrawal"]


def test_small_withdrawal_is_not_flagged():
    outbound = process_message(
        _message({"transaction_type": "withdrawal", "amount": "100.00"})
    )
    assert "policy_flags" not in outbound["data"]


def test_large_branch_wire_is_flagged():
    outbound = process_message(
        _message({"transaction_type": "wire_transfer", "amount": "75000.00"})
    )
    assert outbound["data"]["policy_flags"] == ["large_wire_requires_review"]


def test_clean_transaction_forwards_with_no_policy_flags():
    outbound = process_message(_message())
    assert outbound["target_agent"] == "compliance_checker"
    assert "policy_flags" not in outbound["data"]
    assert outbound["data"]["status"] == "fraud_cleared"


def test_missing_nested_field_does_not_crash():
    outbound = process_message(_message({"metadata": {}}))
    assert outbound["target_agent"] == "compliance_checker"


def test_load_rules_missing_file_returns_empty_list(tmp_path: Path):
    assert load_rules(tmp_path / "does-not-exist.json") == []


def test_load_rules_malformed_json_returns_empty_list(tmp_path: Path):
    bad_config = tmp_path / "bad_rules.json"
    bad_config.write_text("{not valid json", encoding="utf-8")
    assert load_rules(bad_config) == []


def test_process_message_with_missing_rules_file_passes_through(tmp_path: Path):
    outbound = process_message(
        _message({"metadata": {"channel": "online", "country": "IR"}}),
        rules_path=tmp_path / "does-not-exist.json",
    )
    assert outbound["target_agent"] == "compliance_checker"
    assert "policy_flags" not in outbound["data"]


def test_validate_dry_run_report_shape(sample_transactions):
    report = validate_dry_run(sample_transactions)
    assert report["total"] == 8
    assert report["rejected_count"] == 0
    assert report["flagged_count"] == 1
    assert report["flagged"][0]["transaction_id"] == "TXN005"


def test_get_field_returns_none_when_intermediate_value_is_not_a_dict():
    assert _get_field({"metadata": {"country": "US"}}, "metadata.country.sub") is None


def _write_rules(path: Path, rules: list[dict]) -> None:
    path.write_text(json.dumps({"rules": rules}), encoding="utf-8")


def test_neq_operator_flags_non_matching_value(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    _write_rules(
        rules_path,
        [
            {
                "id": "flag_non_us",
                "field": "metadata.country",
                "operator": "neq",
                "value": "US",
                "action": "flag",
                "reason": "non_us_country",
            }
        ],
    )
    outbound = process_message(
        _message({"metadata": {"channel": "online", "country": "DE"}}), rules_path=rules_path
    )
    assert outbound["data"]["policy_flags"] == ["non_us_country"]


def test_not_in_operator_flags_value_outside_allow_list(tmp_path: Path):
    rules_path = tmp_path / "rules.json"
    _write_rules(
        rules_path,
        [
            {
                "id": "flag_unusual_type",
                "field": "transaction_type",
                "operator": "not_in",
                "value": ["transfer", "deposit"],
                "action": "flag",
                "reason": "unusual_transaction_type",
            }
        ],
    )
    outbound = process_message(_message({"transaction_type": "refund"}), rules_path=rules_path)
    assert outbound["data"]["policy_flags"] == ["unusual_transaction_type"]


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


def test_main_accepts_custom_rules_path(tmp_path: Path, sample_transactions_file, capsys):
    rules_path = tmp_path / "rules.json"
    _write_rules(rules_path, [])
    exit_code = main(["--dry-run", "--input", str(sample_transactions_file), "--rules", str(rules_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"rejected_count": 0' in captured.out
    assert '"flagged_count": 0' in captured.out


def test_custom_rules_path_overrides_default(tmp_path: Path):
    custom_rules = tmp_path / "custom_rules.json"
    custom_rules.write_text(
        json.dumps(
            {
                "rules": [
                    {
                        "id": "custom_reject_transfer",
                        "field": "transaction_type",
                        "operator": "eq",
                        "value": "transfer",
                        "action": "reject",
                        "reason": "custom_rule_hit",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    outbound = process_message(_message(), rules_path=custom_rules)
    assert outbound["data"]["status"] == "policy_rejected"
    assert outbound["data"]["policy_reason"] == "custom_rule_hit"

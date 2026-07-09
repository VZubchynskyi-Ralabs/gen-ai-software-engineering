from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agents import rule_engine
from api.server import app

client = TestClient(app)

TXN_APPROVED = {
    "transaction_id": "TXN001",
    "timestamp": "2026-03-16T09:00:00Z",
    "source_account": "ACC-1001",
    "destination_account": "ACC-2001",
    "amount": "1500.00",
    "currency": "USD",
    "transaction_type": "transfer",
    "metadata": {"channel": "online", "country": "US"},
}

TXN_INVALID_CURRENCY = {
    "transaction_id": "TXN006",
    "timestamp": "2026-03-16T10:05:00Z",
    "source_account": "ACC-1006",
    "destination_account": "ACC-7700",
    "amount": "200.00",
    "currency": "XYZ",
    "transaction_type": "transfer",
    "metadata": {"channel": "online", "country": "US"},
}


@pytest.fixture(autouse=True)
def isolated_shared_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PIPELINE_SHARED_ROOT", str(tmp_path / "shared"))


@pytest.fixture(autouse=True)
def isolated_rules_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Never let API-gateway tests read or overwrite the real bundled
    agents/rules_config.json; start from "no rules file yet" like a fresh
    checkout would."""
    monkeypatch.setattr(rule_engine, "DEFAULT_RULES_PATH", tmp_path / "rules_config.json")


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_submit_transaction_returns_approved_result():
    response = client.post("/transactions", json=TXN_APPROVED)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["transaction_id"] == "TXN001"
    assert data["final_status"] == "approved"


def test_submit_transaction_rejected_by_validator():
    response = client.post("/transactions", json=TXN_INVALID_CURRENCY)
    assert response.status_code == 201
    body = response.json()
    assert body["target_agent"] is None
    assert body["data"]["status"] == "rejected"
    assert "invalid_currency" in body["data"]["rejection_reason"]


def test_submit_transaction_missing_field_returns_422():
    incomplete = dict(TXN_APPROVED)
    del incomplete["currency"]
    response = client.post("/transactions", json=incomplete)
    assert response.status_code == 422


def test_get_transaction_not_found_returns_404():
    response = client.get("/transactions/TXN999")
    assert response.status_code == 404


def test_get_transaction_after_submission():
    client.post("/transactions", json=TXN_APPROVED)
    response = client.get("/transactions/TXN001")
    assert response.status_code == 200
    assert response.json()["data"]["final_status"] == "approved"


def test_list_transactions_reflects_all_submissions():
    client.post("/transactions", json=TXN_APPROVED)
    client.post("/transactions", json=TXN_INVALID_CURRENCY)
    response = client.get("/transactions")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    ids = {t["transaction_id"] for t in body["transactions"]}
    assert ids == {"TXN001", "TXN006"}


def test_summary_missing_before_any_run():
    response = client.get("/summary")
    assert response.status_code == 404


def test_summary_reflects_submissions():
    client.post("/transactions", json=TXN_APPROVED)
    client.post("/transactions", json=TXN_INVALID_CURRENCY)
    response = client.get("/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["total_transactions"] == 2
    assert body["status_counts"] == {"approved": 1, "rejected": 1}


REJECT_TRANSFER_RULE_CONFIG = {
    "rules": [
        {
            "id": "reject_all_transfers",
            "field": "transaction_type",
            "operator": "eq",
            "value": "transfer",
            "action": "reject",
            "reason": "transfers_disabled_for_testing",
        }
    ]
}


def test_get_rules_returns_empty_before_any_configuration():
    response = client.get("/rules")
    assert response.status_code == 200
    assert response.json() == {"rules": []}


def test_put_rules_replaces_config_and_get_reflects_it():
    response = client.put("/rules", json=REJECT_TRANSFER_RULE_CONFIG)
    assert response.status_code == 200
    assert response.json()["rules"][0]["id"] == "reject_all_transfers"

    response = client.get("/rules")
    assert response.status_code == 200
    assert response.json() == REJECT_TRANSFER_RULE_CONFIG


def test_put_rules_takes_effect_on_next_submission():
    client.put("/rules", json=REJECT_TRANSFER_RULE_CONFIG)
    response = client.post("/transactions", json=TXN_APPROVED)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "policy_rejected"
    assert data["policy_reason"] == "transfers_disabled_for_testing"


def test_put_rules_rejects_unknown_operator():
    bad_config = {
        "rules": [
            {
                "id": "bad_rule",
                "field": "transaction_type",
                "operator": "startswith",
                "value": "wire",
                "action": "flag",
                "reason": "bad_operator",
            }
        ]
    }
    response = client.put("/rules", json=bad_config)
    assert response.status_code == 422


def test_put_rules_rejects_invalid_min_amount():
    bad_config = {
        "rules": [
            {
                "id": "bad_rule",
                "field": "transaction_type",
                "operator": "eq",
                "value": "withdrawal",
                "min_amount": "not-a-number",
                "action": "flag",
                "reason": "bad_min_amount",
            }
        ]
    }
    response = client.put("/rules", json=bad_config)
    assert response.status_code == 422


def test_put_rules_accepts_a_valid_min_amount():
    config = {
        "rules": [
            {
                "id": "large_withdrawal",
                "field": "transaction_type",
                "operator": "eq",
                "value": "withdrawal",
                "min_amount": "5000.00",
                "action": "flag",
                "reason": "large_cash_withdrawal",
            }
        ]
    }
    response = client.put("/rules", json=config)
    assert response.status_code == 200
    assert response.json()["rules"][0]["min_amount"] == "5000.00"


def test_put_rules_accepts_an_explicit_null_min_amount():
    config = {
        "rules": [
            {
                "id": "no_min_amount",
                "field": "transaction_type",
                "operator": "eq",
                "value": "withdrawal",
                "min_amount": None,
                "action": "flag",
                "reason": "any_withdrawal",
            }
        ]
    }
    response = client.put("/rules", json=config)
    assert response.status_code == 200
    assert "min_amount" not in response.json()["rules"][0]


def test_put_rules_rejects_unknown_action():
    bad_config = {
        "rules": [
            {
                "id": "bad_rule",
                "field": "transaction_type",
                "operator": "eq",
                "value": "withdrawal",
                "action": "quarantine",
                "reason": "bad_action",
            }
        ]
    }
    response = client.put("/rules", json=bad_config)
    assert response.status_code == 422

from agents.compliance_checker import process_message

BASE_CLEARED = {
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
    data = dict(BASE_CLEARED)
    if overrides:
        data.update(overrides)
    return {"data": data}


def test_clean_transaction_is_approved():
    outbound = process_message(_message())
    assert outbound["data"]["final_status"] == "approved"
    assert outbound["target_agent"] is None


def test_unknown_transaction_type_is_rejected():
    outbound = process_message(_message({"transaction_type": "teleport"}))
    assert outbound["data"]["final_status"] == "rejected"
    assert "unknown_transaction_type" in outbound["data"]["reason"]


def test_fraud_flagged_transaction_is_flagged_for_review():
    outbound = process_message(_message({"status": "flagged_for_review"}))
    assert outbound["data"]["final_status"] == "flagged_for_review"
    assert "fraud_risk_flagged" in outbound["data"]["reason"]


def test_cross_border_transaction_is_flagged_for_review():
    outbound = process_message(_message({"metadata": {"channel": "api", "country": "DE"}}))
    assert outbound["data"]["final_status"] == "flagged_for_review"
    assert "cross_border" in outbound["data"]["reason"]


def test_fraud_and_cross_border_both_recorded_in_reason():
    outbound = process_message(
        _message({"status": "flagged_for_review", "metadata": {"channel": "api", "country": "DE"}})
    )
    assert outbound["data"]["final_status"] == "flagged_for_review"
    assert "fraud_risk_flagged" in outbound["data"]["reason"]
    assert "cross_border" in outbound["data"]["reason"]


def test_is_terminal_agent():
    outbound = process_message(_message())
    assert outbound["target_agent"] is None
    assert outbound["source_agent"] == "compliance_checker"

from agents.fraud_detector import process_message

BASE_VALIDATED = {
    "transaction_id": "TXN100",
    "timestamp": "2026-03-16T09:00:00Z",
    "source_account": "ACC-1001",
    "destination_account": "ACC-2001",
    "amount": "1500.00",
    "currency": "USD",
    "transaction_type": "transfer",
    "status": "validated",
    "metadata": {"channel": "online", "country": "US"},
}


def _message(overrides=None):
    data = dict(BASE_VALIDATED)
    if overrides:
        data.update(overrides)
    return {"data": data}


def test_low_risk_transaction_is_cleared():
    outbound = process_message(_message())
    assert outbound["data"]["status"] == "fraud_cleared"
    assert outbound["data"]["risk_score"] == 0
    assert outbound["data"]["risk_factors"] == []
    assert outbound["target_agent"] == "compliance_checker"


def test_high_value_alone_flags_for_review():
    outbound = process_message(_message({"amount": "25000.00", "transaction_type": "wire_transfer"}))
    assert outbound["data"]["status"] == "flagged_for_review"
    assert "high_value" in outbound["data"]["risk_factors"]
    assert outbound["data"]["risk_score"] > 0.7


def test_off_hours_and_cross_border_combine_but_do_not_cross_threshold():
    outbound = process_message(
        _message(
            {
                "timestamp": "2026-03-16T02:47:00Z",
                "metadata": {"channel": "api", "country": "DE"},
            }
        )
    )
    assert set(outbound["data"]["risk_factors"]) == {"off_hours", "cross_border"}
    assert outbound["data"]["status"] == "fraud_cleared"
    assert outbound["data"]["risk_score"] == 0.6


def test_risk_score_capped_at_one():
    outbound = process_message(
        _message(
            {
                "amount": "75000.00",
                "transaction_type": "wire_transfer",
                "timestamp": "2026-03-16T02:00:00Z",
                "metadata": {"channel": "branch", "country": "DE"},
            }
        )
    )
    assert outbound["data"]["risk_score"] <= 1.0


def test_always_forwards_to_compliance_checker():
    outbound = process_message(_message({"amount": "99999.00"}))
    assert outbound["target_agent"] == "compliance_checker"

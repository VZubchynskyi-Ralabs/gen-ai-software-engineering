"""
test_categorization.py — 10 tests for keyword-rule classifier
"""
import pytest
from src.services.classifier import classify_ticket


def _ticket(subject, description=""):
    return {"id": "test-id", "subject": subject, "description": description}


def test_urgent_priority_critical():
    result = classify_ticket(_ticket("critical issue", "production down"))
    assert result["priority"] == "urgent"


def test_urgent_priority_security():
    result = classify_ticket(_ticket("security breach", "we have been hacked"))
    assert result["priority"] == "urgent"


def test_high_priority_blocking():
    result = classify_ticket(_ticket("blocking issue", "this is blocking the team asap"))
    assert result["priority"] == "high"


def test_low_priority_cosmetic():
    result = classify_ticket(_ticket("minor cosmetic issue", "suggestion for UI"))
    assert result["priority"] == "low"


def test_medium_priority_default():
    result = classify_ticket(_ticket("general question", "just asking about something"))
    assert result["priority"] == "medium"


def test_category_account_access():
    result = classify_ticket(_ticket("cannot login", "password reset not working"))
    assert result["category"] == "account_access"


def test_category_billing():
    result = classify_ticket(_ticket("billing question", "invoice is wrong refund needed"))
    assert result["category"] == "billing_question"


def test_category_feature_request():
    result = classify_ticket(_ticket("feature request suggestion", "please add new feature enhancement"))
    assert result["category"] == "feature_request"


def test_category_other_fallback():
    result = classify_ticket(_ticket("xyz abc", "no relevant keywords at all here"))
    assert result["category"] == "other"


def test_confidence_and_keywords_returned():
    result = classify_ticket(_ticket("login error", "password reset fails with exception error 500"))
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["keywords_found"], list)
    assert isinstance(result["reasoning"], str)
    assert len(result["reasoning"]) > 0


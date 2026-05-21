"""
test_ticket_model.py — 9 tests covering validation helpers
"""
import pytest
from src.models import validate_ticket_data, CATEGORIES, PRIORITIES, STATUSES

BASE = {
    "customer_id": "CUST-001",
    "customer_email": "user@example.com",
    "customer_name": "Alice",
    "subject": "Valid subject",
    "description": "A description that is definitely long enough to pass validation checks.",
}


def test_valid_ticket_passes():
    cleaned, errors = validate_ticket_data(BASE)
    assert errors == []
    assert cleaned["customer_email"] == "user@example.com"


def test_missing_required_fields():
    _, errors = validate_ticket_data({})
    assert len(errors) >= 5


def test_invalid_email_rejected():
    _, errors = validate_ticket_data({**BASE, "customer_email": "bad"})
    assert any("email" in e for e in errors)


def test_subject_too_short():
    _, errors = validate_ticket_data({**BASE, "subject": ""})
    assert any("subject" in e for e in errors)


def test_subject_too_long():
    _, errors = validate_ticket_data({**BASE, "subject": "x" * 201})
    assert any("subject" in e for e in errors)


def test_description_too_short():
    _, errors = validate_ticket_data({**BASE, "description": "Short"})
    assert any("description" in e for e in errors)


def test_invalid_category_rejected():
    _, errors = validate_ticket_data({**BASE, "category": "nonsense"})
    assert any("category" in e for e in errors)


def test_invalid_priority_rejected():
    _, errors = validate_ticket_data({**BASE, "priority": "super_urgent"})
    assert any("priority" in e for e in errors)


def test_partial_update_skips_required():
    cleaned, errors = validate_ticket_data({"status": "resolved"}, partial=True)
    assert errors == []
    assert cleaned["status"] == "resolved"


def test_invalid_source_rejected():
    _, errors = validate_ticket_data({**BASE, "metadata": {"source": "fax"}})
    assert any("source" in e for e in errors)


def test_invalid_device_type_rejected():
    _, errors = validate_ticket_data({**BASE, "metadata": {"device_type": "smartwatch"}})
    assert any("device_type" in e for e in errors)


def test_metadata_as_json_string():
    import json
    data = {**BASE, "metadata": json.dumps({"source": "email", "browser": "Safari"})}
    cleaned, errors = validate_ticket_data(data)
    assert errors == []
    assert cleaned.get("source") == "email"


def test_tags_as_comma_string():
    cleaned, errors = validate_ticket_data({**BASE, "tags": "alpha,beta,gamma"})
    assert errors == []
    import json
    assert json.loads(cleaned["tags"]) == ["alpha", "beta", "gamma"]


def test_tags_as_list():
    cleaned, errors = validate_ticket_data({**BASE, "tags": ["x", "y"]})
    assert errors == []
    import json
    assert json.loads(cleaned["tags"]) == ["x", "y"]



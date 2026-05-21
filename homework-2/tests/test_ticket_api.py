"""
test_ticket_api.py — 11 tests covering all REST endpoints
"""
import json
import pytest
from tests.conftest import VALID_TICKET


def test_create_ticket_201(fresh_app):
    res = fresh_app.post("/tickets", json=VALID_TICKET)
    assert res.status_code == 201
    data = res.get_json()
    assert data["customer_email"] == "test@example.com"
    assert "id" in data


def test_create_ticket_missing_required_400(fresh_app):
    res = fresh_app.post("/tickets", json={"customer_id": "X"})
    assert res.status_code == 400
    assert "errors" in res.get_json()


def test_create_ticket_invalid_email_400(fresh_app):
    bad = {**VALID_TICKET, "customer_email": "not-an-email"}
    res = fresh_app.post("/tickets", json=bad)
    assert res.status_code == 400


def test_create_ticket_invalid_category_400(fresh_app):
    bad = {**VALID_TICKET, "category": "unknown_cat"}
    res = fresh_app.post("/tickets", json=bad)
    assert res.status_code == 400


def test_get_all_tickets_200(fresh_app):
    fresh_app.post("/tickets", json=VALID_TICKET)
    res = fresh_app.get("/tickets")
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_get_ticket_by_id_200(fresh_app):
    created = fresh_app.post("/tickets", json=VALID_TICKET).get_json()
    res = fresh_app.get(f"/tickets/{created['id']}")
    assert res.status_code == 200
    assert res.get_json()["id"] == created["id"]


def test_get_ticket_not_found_404(fresh_app):
    res = fresh_app.get("/tickets/nonexistent-id")
    assert res.status_code == 404


def test_update_ticket_200(fresh_app):
    created = fresh_app.post("/tickets", json=VALID_TICKET).get_json()
    res = fresh_app.put(f"/tickets/{created['id']}", json={"status": "in_progress"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "in_progress"


def test_update_ticket_not_found_404(fresh_app):
    res = fresh_app.put("/tickets/nonexistent-id", json={"status": "resolved"})
    assert res.status_code == 404


def test_delete_ticket_204(fresh_app):
    created = fresh_app.post("/tickets", json=VALID_TICKET).get_json()
    res = fresh_app.delete(f"/tickets/{created['id']}")
    assert res.status_code == 204


def test_delete_ticket_not_found_404(fresh_app):
    res = fresh_app.delete("/tickets/nonexistent-id")
    assert res.status_code == 404


def test_create_ticket_auto_classify(fresh_app):
    """?auto_classify=true should return category/priority from classifier"""
    res = fresh_app.post("/tickets?auto_classify=true", json=VALID_TICKET)
    assert res.status_code == 201
    data = res.get_json()
    assert data["category"] in ["account_access", "technical_issue", "billing_question",
                                 "feature_request", "bug_report", "other"]


def test_bulk_import_no_file_400(fresh_app):
    res = fresh_app.post("/tickets/import")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_bulk_import_unsupported_format_400(fresh_app):
    import io
    res = fresh_app.post(
        "/tickets/import",
        data={"file": (io.BytesIO(b"data"), "tickets.txt")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 400


def test_auto_classify_endpoint_unknown_ticket(fresh_app):
    res = fresh_app.post("/tickets/nonexistent-id/auto-classify")
    assert res.status_code == 404


def test_update_ticket_invalid_status_400(fresh_app):
    created = fresh_app.post("/tickets", json=VALID_TICKET).get_json()
    res = fresh_app.put(f"/tickets/{created['id']}", json={"status": "invalid_status"})
    assert res.status_code == 400


def test_list_tickets_with_filters(fresh_app):
    fresh_app.post("/tickets", json={**VALID_TICKET, "priority": "urgent"})
    res = fresh_app.get("/tickets?priority=urgent")
    assert res.status_code == 200
    data = res.get_json()
    assert all(t["priority"] == "urgent" for t in data)



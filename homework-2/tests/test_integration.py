"""
test_integration.py — 5 end-to-end workflow tests
"""
import io
import os
import json
import threading
import pytest
from tests.conftest import VALID_TICKET

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_full_ticket_lifecycle(fresh_app):
    """Create -> Read -> Update -> Auto-classify -> Delete"""
    # Create
    res = fresh_app.post("/tickets", json=VALID_TICKET)
    assert res.status_code == 201
    ticket_id = res.get_json()["id"]

    # Read
    res = fresh_app.get(f"/tickets/{ticket_id}")
    assert res.status_code == 200

    # Update
    res = fresh_app.put(f"/tickets/{ticket_id}", json={"status": "in_progress", "assigned_to": "agent1@support.com"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "in_progress"

    # Auto-classify
    res = fresh_app.post(f"/tickets/{ticket_id}/auto-classify")
    assert res.status_code == 200
    data = res.get_json()
    assert "category" in data
    assert "priority" in data
    assert "confidence" in data

    # Delete
    res = fresh_app.delete(f"/tickets/{ticket_id}")
    assert res.status_code == 204

    # Verify gone
    res = fresh_app.get(f"/tickets/{ticket_id}")
    assert res.status_code == 404


def test_bulk_import_csv_then_list(fresh_app):
    """Import CSV, verify tickets appear in list"""
    csv_text = open(os.path.join(FIXTURES, "sample_tickets.csv")).read()
    res = fresh_app.post(
        "/tickets/import",
        data={"file": (io.BytesIO(csv_text.encode()), "sample_tickets.csv")},
        content_type="multipart/form-data",
    )
    assert res.status_code in (200, 207)
    summary = res.get_json()
    assert summary["successful"] > 0

    list_res = fresh_app.get("/tickets")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) >= summary["successful"]


def test_bulk_import_with_auto_classify(fresh_app):
    """Import JSON file, then auto-classify each ticket"""
    json_text = open(os.path.join(FIXTURES, "sample_tickets.json")).read()
    res = fresh_app.post(
        "/tickets/import",
        data={"file": (io.BytesIO(json_text.encode()), "sample_tickets.json")},
        content_type="multipart/form-data",
    )
    assert res.status_code in (200, 207)
    summary = res.get_json()
    created_ids = summary["created_ids"]
    assert len(created_ids) > 0

    # Auto-classify first 3
    for ticket_id in created_ids[:3]:
        res = fresh_app.post(f"/tickets/{ticket_id}/auto-classify")
        assert res.status_code == 200
        data = res.get_json()
        assert data["category"] in ["account_access","technical_issue","billing_question",
                                     "feature_request","bug_report","other"]


def test_filtering_by_status_and_category(fresh_app):
    """Create tickets with specific fields, verify filtering works"""
    t1 = {**VALID_TICKET, "status": "resolved", "category": "billing_question"}
    t2 = {**VALID_TICKET, "status": "new", "category": "technical_issue"}
    fresh_app.post("/tickets", json=t1)
    fresh_app.post("/tickets", json=t2)

    res = fresh_app.get("/tickets?status=resolved")
    records = res.get_json()
    assert all(t["status"] == "resolved" for t in records)

    res = fresh_app.get("/tickets?category=technical_issue")
    records = res.get_json()
    assert all(t["category"] == "technical_issue" for t in records)


def test_concurrent_ticket_creation(app):
    """20 simultaneous ticket creations — each thread uses its own client"""
    results = []
    errors = []

    def create_ticket(i):
        try:
            with app.test_client() as c:
                res = c.post("/tickets", json={
                    **VALID_TICKET,
                    "customer_id": f"CUST-CONC-{i}",
                    "customer_email": f"concurrent{i}@example.com",
                    "subject": f"Concurrent ticket {i}",
                })
                results.append(res.status_code)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=create_ticket, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Errors during concurrent creation: {errors}"
    assert all(s == 201 for s in results), f"Non-201 responses: {results}"


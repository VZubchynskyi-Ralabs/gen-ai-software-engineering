"""
test_performance.py — 5 benchmark tests
Asserts response times stay within reasonable thresholds.
"""
import io
import os
import time
import threading
import pytest
from tests.conftest import VALID_TICKET

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

# Thresholds (seconds)
SINGLE_CREATE_MAX = 0.5
BULK_IMPORT_50_MAX = 3.0
LIST_MAX = 0.5
P95_20REQ_MAX = 2.0


def test_single_ticket_creation_speed(fresh_app):
    start = time.perf_counter()
    res = fresh_app.post("/tickets", json=VALID_TICKET)
    elapsed = time.perf_counter() - start
    assert res.status_code == 201
    assert elapsed < SINGLE_CREATE_MAX, f"Create took {elapsed:.3f}s (limit {SINGLE_CREATE_MAX}s)"


def test_bulk_import_50_csv_speed(fresh_app):
    csv_text = open(os.path.join(FIXTURES, "sample_tickets.csv")).read()
    start = time.perf_counter()
    res = fresh_app.post(
        "/tickets/import",
        data={"file": (io.BytesIO(csv_text.encode()), "sample_tickets.csv")},
        content_type="multipart/form-data",
    )
    elapsed = time.perf_counter() - start
    assert res.status_code in (200, 207)
    assert elapsed < BULK_IMPORT_50_MAX, f"Bulk import took {elapsed:.3f}s (limit {BULK_IMPORT_50_MAX}s)"


def test_list_tickets_speed(fresh_app):
    # Pre-populate
    for i in range(20):
        fresh_app.post("/tickets", json={
            **VALID_TICKET,
            "customer_id": f"PERF-{i}",
            "customer_email": f"perf{i}@example.com",
        })
    start = time.perf_counter()
    res = fresh_app.get("/tickets")
    elapsed = time.perf_counter() - start
    assert res.status_code == 200
    assert elapsed < LIST_MAX, f"List took {elapsed:.3f}s (limit {LIST_MAX}s)"


def test_p95_response_time_20_requests(app):
    times = []

    def measure(i):
        with app.test_client() as c:
            start = time.perf_counter()
            c.post("/tickets", json={
                **VALID_TICKET,
                "customer_id": f"P95-{i}",
                "customer_email": f"p95user{i}@example.com",
            })
            times.append(time.perf_counter() - start)

    threads = [threading.Thread(target=measure, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    times.sort()
    p95 = times[int(0.95 * len(times))]
    print(f"\nP95 response time (20 concurrent): {p95:.3f}s")
    assert p95 < P95_20REQ_MAX, f"P95 = {p95:.3f}s exceeds limit {P95_20REQ_MAX}s"


def test_auto_classify_speed(fresh_app):
    created = fresh_app.post("/tickets", json=VALID_TICKET).get_json()
    ticket_id = created["id"]
    start = time.perf_counter()
    res = fresh_app.post(f"/tickets/{ticket_id}/auto-classify")
    elapsed = time.perf_counter() - start
    assert res.status_code == 200
    assert elapsed < SINGLE_CREATE_MAX, f"Classify took {elapsed:.3f}s (limit {SINGLE_CREATE_MAX}s)"


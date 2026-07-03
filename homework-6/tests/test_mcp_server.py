"""Tests for mcp/server.py.

Loaded via importlib under a distinct module name (not `mcp.server`)
because this project's `mcp/` directory intentionally shares its top-level
name with the `mcp` PyPI package that `fastmcp` itself depends on;
`import mcp.server` in a test process would collide with that real
package. Loading by file path sidesteps the collision entirely.
"""
import importlib.util
import json
from pathlib import Path

import pytest

SERVER_PATH = Path(__file__).resolve().parent.parent / "mcp" / "server.py"


@pytest.fixture
def server_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    spec = importlib.util.spec_from_file_location("pipeline_mcp_server_under_test", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "RESULTS_DIR", tmp_path)
    return module


def _write_result(results_dir: Path, transaction_id: str, data: dict) -> None:
    payload = {
        "message_id": "test",
        "timestamp": "2026-03-16T10:00:00Z",
        "source_agent": "compliance_checker",
        "target_agent": None,
        "message_type": "transaction",
        "data": data,
    }
    (results_dir / f"{transaction_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_get_transaction_status_found(server_module, tmp_path: Path):
    _write_result(
        tmp_path,
        "TXN001",
        {"transaction_id": "TXN001", "final_status": "approved", "reason": "no_issues_found", "amount": "1500.00", "currency": "USD"},
    )
    result = server_module.get_transaction_status("TXN001")
    assert result["found"] is True
    assert result["status"] == "approved"


def test_get_transaction_status_not_found(server_module):
    result = server_module.get_transaction_status("TXN999")
    assert result["found"] is False


def test_list_pipeline_results_empty_when_no_results_dir(server_module, tmp_path: Path):
    empty_dir = tmp_path / "does-not-exist"
    server_module.RESULTS_DIR = empty_dir
    result = server_module.list_pipeline_results()
    assert result == {"total": 0, "transactions": []}


def test_list_pipeline_results_summarizes_all(server_module, tmp_path: Path):
    _write_result(tmp_path, "TXN001", {"transaction_id": "TXN001", "final_status": "approved"})
    _write_result(tmp_path, "TXN002", {"transaction_id": "TXN002", "final_status": "rejected", "reason": "bad_currency"})
    result = server_module.list_pipeline_results()
    assert result["total"] == 2
    ids = {t["transaction_id"] for t in result["transactions"]}
    assert ids == {"TXN001", "TXN002"}


def test_pipeline_summary_resource_missing_summary(server_module):
    text = server_module.pipeline_summary()
    assert "No pipeline run found" in text


def test_pipeline_summary_resource_with_summary(server_module, tmp_path: Path):
    summary = {
        "total_transactions": 2,
        "status_counts": {"approved": 1, "rejected": 1},
        "outcomes": [
            {"transaction_id": "TXN001", "status": "approved", "reason": "no_issues_found"},
            {"transaction_id": "TXN002", "status": "rejected", "reason": "bad_currency"},
        ],
    }
    (tmp_path / "pipeline_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    text = server_module.pipeline_summary()
    assert "Total transactions: 2" in text
    assert "TXN001: approved" in text

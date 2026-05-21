"""
test_import_json.py — 5 tests for JSON parsing
"""
import os
import json
import pytest
from src.services.importer import parse_json

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_valid_json():
    text = open(os.path.join(FIXTURES, "sample_tickets.json")).read()
    result = parse_json(text)
    assert result["total"] == 20
    assert len(result["records"]) == 20
    assert result["failed"] == []


def test_parse_json_array_format():
    data = [{"customer_id": "C1", "subject": "Test"}]
    result = parse_json(json.dumps(data))
    assert result["total"] == 1
    assert result["records"][0]["customer_id"] == "C1"


def test_parse_invalid_json_syntax():
    result = parse_json("{not valid json")
    assert result["total"] == 0
    assert len(result["failed"]) > 0
    assert "Invalid JSON" in result["failed"][0]["errors"][0]


def test_parse_json_non_list_item():
    result = parse_json(json.dumps(["string_item"]))
    assert result["failed"][0]["errors"][0] == "Each item must be a JSON object"


def test_parse_json_lifts_metadata():
    data = [{"customer_id": "C1", "metadata": {"source": "api", "browser": "Firefox"}}]
    result = parse_json(json.dumps(data))
    assert result["records"][0].get("source") == "api" or \
           result["records"][0].get("metadata", {}).get("source") == "api"


def test_import_tickets_unknown_format():
    from src.services.importer import import_tickets
    result = import_tickets("data", "yaml")
    assert result["total"] == 0
    assert len(result["failed"]) > 0
    assert "Unknown format" in result["failed"][0]["errors"][0]


def test_parse_json_object_with_tickets_key():
    from src.services.importer import parse_json as pj
    import json as j
    data = {"tickets": [{"customer_id": "C2", "subject": "S"}]}
    result = pj(j.dumps(data))
    assert result["total"] == 1
    assert result["records"][0]["customer_id"] == "C2"



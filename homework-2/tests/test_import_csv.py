"""
test_import_csv.py — 6 tests for CSV parsing
"""
import os
import pytest
from src.services.importer import parse_csv

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_valid_csv():
    text = open(os.path.join(FIXTURES, "sample_tickets.csv")).read()
    result = parse_csv(text)
    assert result["total"] == 50
    assert len(result["records"]) == 50
    assert result["failed"] == []


def test_parse_csv_returns_dict_records():
    text = open(os.path.join(FIXTURES, "sample_tickets.csv")).read()
    result = parse_csv(text)
    first = result["records"][0]
    assert "customer_id" in first
    assert "subject" in first


def test_parse_csv_strips_whitespace():
    text = "customer_id,customer_email,subject\n CUST-1 , user@example.com , My subject \n"
    result = parse_csv(text)
    assert result["records"][0]["customer_id"] == "CUST-1"
    assert result["records"][0]["subject"] == "My subject"


def test_parse_empty_csv():
    result = parse_csv("customer_id,customer_email\n")
    assert result["total"] == 0
    assert result["records"] == []


def test_parse_csv_with_no_header():
    result = parse_csv("")
    assert result["total"] == 0


def test_parse_invalid_csv_partial():
    text = open(os.path.join(FIXTURES, "invalid_tickets.csv")).read()
    result = parse_csv(text)
    # Records are parsed (validation happens in route), so we just get raw rows
    assert result["total"] >= 1


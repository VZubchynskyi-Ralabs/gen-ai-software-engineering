"""
test_import_xml.py — 5 tests for XML parsing
"""
import os
import pytest
from src.services.importer import parse_xml

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_valid_xml():
    text = open(os.path.join(FIXTURES, "sample_tickets.xml")).read()
    result = parse_xml(text)
    assert result["total"] == 30
    assert len(result["records"]) == 30
    assert result["failed"] == []


def test_parse_xml_ticket_fields():
    text = open(os.path.join(FIXTURES, "sample_tickets.xml")).read()
    result = parse_xml(text)
    first = result["records"][0]
    assert "customer_id" in first
    assert "subject" in first


def test_parse_xml_tags_as_list():
    text = open(os.path.join(FIXTURES, "sample_tickets.xml")).read()
    result = parse_xml(text)
    # Tags should be parsed as a list from <tags><tag>...</tag></tags>
    first = result["records"][0]
    assert isinstance(first.get("tags", []), list)


def test_parse_invalid_xml():
    text = open(os.path.join(FIXTURES, "invalid_tickets.xml")).read()
    result = parse_xml(text)
    assert result["total"] == 0
    assert len(result["failed"]) > 0
    assert "Invalid XML" in result["failed"][0]["errors"][0]


def test_parse_single_ticket_xml():
    text = "<ticket><customer_id>C1</customer_id><subject>Test</subject></ticket>"
    result = parse_xml(text)
    assert result["total"] == 1
    assert result["records"][0]["customer_id"] == "C1"


"""
Parse CSV, JSON, and XML ticket payloads.
Returns: { total, records: [dict], failed: [{row, errors}] }
"""
import csv
import io
import json
import xml.etree.ElementTree as ET


def parse_csv(text):
    records = []
    failed = []
    try:
        reader = csv.DictReader(io.StringIO(text))
    except Exception as e:
        return {"total": 0, "records": [], "failed": [{"row": "header", "errors": [str(e)]}]}
    for i, row in enumerate(reader, start=1):
        try:
            record = {k.strip(): (v.strip() if v else v) for k, v in row.items()}
            _lift_metadata(record)
            records.append(record)
        except Exception as e:
            failed.append({"row": i, "errors": [str(e)]})
    total = len(records) + len(failed)
    return {"total": total, "records": records, "failed": failed}


def parse_json(text):
    records = []
    failed = []
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {"total": 0, "records": [], "failed": [{"row": "root", "errors": [f"Invalid JSON: {e}"]}]}
    if isinstance(data, dict):
        data = data.get("tickets", [data])
    if not isinstance(data, list):
        return {"total": 0, "records": [], "failed": [{"row": "root", "errors": ["JSON must be an array or {tickets:[...]}"]}]}
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            failed.append({"row": i, "errors": ["Each item must be a JSON object"]})
            continue
        _lift_metadata(item)
        records.append(item)
    total = len(records) + len(failed)
    return {"total": total, "records": records, "failed": failed}


def parse_xml(text):
    records = []
    failed = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return {"total": 0, "records": [], "failed": [{"row": "root", "errors": [f"Invalid XML: {e}"]}]}
    items = root.findall("ticket") if root.tag != "ticket" else [root]
    for i, elem in enumerate(items, start=1):
        try:
            record = {}
            for child in elem:
                if len(child):
                    for sub in child:
                        record[sub.tag] = (sub.text or "").strip()
                else:
                    record[child.tag] = (child.text or "").strip()
            tags_elem = elem.find("tags")
            if tags_elem is not None:
                record["tags"] = [t.text.strip() for t in tags_elem.findall("tag") if t.text]
            records.append(record)
        except Exception as e:
            failed.append({"row": i, "errors": [str(e)]})
    total = len(records) + len(failed)
    return {"total": total, "records": records, "failed": failed}


def import_tickets(text, fmt):
    if fmt == "csv":
        return parse_csv(text)
    elif fmt == "json":
        return parse_json(text)
    elif fmt == "xml":
        return parse_xml(text)
    else:
        return {"total": 0, "records": [], "failed": [{"row": "N/A", "errors": [f"Unknown format: {fmt}"]}]}


def _lift_metadata(record):
    meta = record.get("metadata")
    if isinstance(meta, dict):
        for k, v in meta.items():
            if k not in record:
                record[k] = v


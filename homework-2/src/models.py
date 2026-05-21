"""
Validation helpers and raw SQL CRUD for tickets.
"""
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone

CATEGORIES = {"account_access", "technical_issue", "billing_question",
              "feature_request", "bug_report", "other"}
PRIORITIES = {"urgent", "high", "medium", "low"}
STATUSES = {"new", "in_progress", "waiting_customer", "resolved", "closed"}
SOURCES = {"web_form", "email", "api", "chat", "phone"}
DEVICE_TYPES = {"desktop", "mobile", "tablet"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_ticket_data(data, partial=False):
    """Validate ticket dict. Returns (cleaned_dict, list_of_errors).
    If partial=True, missing required fields are not errors (used for PUT).
    """
    errors = []
    cleaned = {}

    required = ["customer_id", "customer_email", "customer_name", "subject", "description"]
    for field in required:
        val = data.get(field)
        if val is None:
            if not partial:
                errors.append(f"'{field}' is required")
        else:
            cleaned[field] = str(val).strip()

    # email
    if "customer_email" in cleaned:
        if not EMAIL_RE.match(cleaned["customer_email"]):
            errors.append("'customer_email' must be a valid email address")

    # subject length
    if "subject" in cleaned:
        if not (1 <= len(cleaned["subject"]) <= 200):
            errors.append("'subject' must be between 1 and 200 characters")

    # description length
    if "description" in cleaned:
        if not (10 <= len(cleaned["description"]) <= 2000):
            errors.append("'description' must be between 10 and 2000 characters")

    # enums
    for field, allowed in [("category", CATEGORIES), ("priority", PRIORITIES),
                            ("status", STATUSES)]:
        val = data.get(field)
        if val is not None:
            val = str(val).strip().lower()
            if val not in allowed:
                errors.append(f"'{field}' must be one of: {', '.join(sorted(allowed))}")
            else:
                cleaned[field] = val

    # metadata
    metadata = data.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {}

    source = metadata.get("source") or data.get("source")
    if source is not None:
        source = str(source).strip().lower()
        if source not in SOURCES:
            errors.append(f"'metadata.source' must be one of: {', '.join(sorted(SOURCES))}")
        else:
            cleaned["source"] = source

    browser = metadata.get("browser") or data.get("browser")
    if browser is not None:
        cleaned["browser"] = str(browser).strip()

    device_type = metadata.get("device_type") or data.get("device_type")
    if device_type is not None:
        device_type = str(device_type).strip().lower()
        if device_type not in DEVICE_TYPES:
            errors.append(f"'metadata.device_type' must be one of: {', '.join(sorted(DEVICE_TYPES))}")
        else:
            cleaned["device_type"] = device_type

    # optional simple fields
    for field in ("assigned_to", "resolved_at"):
        val = data.get(field)
        if val is not None:
            cleaned[field] = str(val).strip()

    # tags
    tags = data.get("tags")
    if tags is not None:
        if isinstance(tags, list):
            cleaned["tags"] = json.dumps(tags)
        elif isinstance(tags, str):
            # try JSON, else comma-separated
            try:
                parsed = json.loads(tags)
                cleaned["tags"] = json.dumps(parsed if isinstance(parsed, list) else [tags])
            except Exception:
                cleaned["tags"] = json.dumps([t.strip() for t in tags.split(",") if t.strip()])

    return cleaned, errors


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # parse tags back to list
    try:
        d["tags"] = json.loads(d.get("tags") or "[]")
    except Exception:
        d["tags"] = []
    # rebuild metadata sub-object
    d["metadata"] = {
        "source": d.pop("source", "api"),
        "browser": d.pop("browser", None),
        "device_type": d.pop("device_type", None),
    }
    return d


def create_ticket(conn, data):
    ticket_id = str(uuid.uuid4())
    now = _now()
    conn.execute(
        """
        INSERT INTO tickets (id, customer_id, customer_email, customer_name,
            subject, description, category, priority, status,
            created_at, updated_at, resolved_at, assigned_to, tags,
            source, browser, device_type)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            ticket_id,
            data["customer_id"],
            data["customer_email"],
            data["customer_name"],
            data["subject"],
            data["description"],
            data.get("category", "other"),
            data.get("priority", "medium"),
            data.get("status", "new"),
            now,
            now,
            data.get("resolved_at"),
            data.get("assigned_to"),
            data.get("tags", "[]"),
            data.get("source", "api"),
            data.get("browser"),
            data.get("device_type"),
        ),
    )
    conn.commit()
    return get_ticket(conn, ticket_id)


def get_ticket(conn, ticket_id):
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return _row_to_dict(row)


def list_tickets(conn, filters=None):
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if filters:
        for col in ("status", "category", "priority"):
            if filters.get(col):
                query += f" AND {col} = ?"
                params.append(filters[col])
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_ticket(conn, ticket_id, data):
    ticket = get_ticket(conn, ticket_id)
    if ticket is None:
        return None

    allowed_update = [
        "customer_id", "customer_email", "customer_name", "subject",
        "description", "category", "priority", "status", "resolved_at",
        "assigned_to", "tags", "source", "browser", "device_type",
    ]
    sets = []
    params = []
    for col in allowed_update:
        if col in data:
            sets.append(f"{col} = ?")
            params.append(data[col])

    # classification fields
    for col in ("classification_confidence", "classification_reasoning", "classification_keywords"):
        if col in data:
            sets.append(f"{col} = ?")
            params.append(data[col])

    if not sets:
        return ticket

    sets.append("updated_at = ?")
    params.append(_now())
    params.append(ticket_id)

    conn.execute(f"UPDATE tickets SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    return get_ticket(conn, ticket_id)


def delete_ticket(conn, ticket_id):
    result = conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    return result.rowcount > 0


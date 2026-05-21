"""
CRUD routes for /tickets and /tickets/import
"""
import io
from flask import Blueprint, request, jsonify, current_app

from src.app import get_db
from src.models import validate_ticket_data, create_ticket, get_ticket, list_tickets, update_ticket, delete_ticket
from src.services.importer import import_tickets
from src.services.classifier import classify_ticket

tickets_bp = Blueprint("tickets", __name__)


def _db():
    return get_db(current_app.config["DB_PATH"])


# ---------------------------------------------------------------------------
# POST /tickets
# ---------------------------------------------------------------------------
@tickets_bp.post("/tickets")
def create():
    data = request.get_json(silent=True) or {}
    auto_classify = str(request.args.get("auto_classify", "false")).lower() == "true"

    cleaned, errors = validate_ticket_data(data)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = _db()
    ticket = create_ticket(conn, cleaned)
    conn.close()

    if auto_classify:
        conn = _db()
        result = classify_ticket(ticket)
        update_ticket(conn, ticket["id"], {
            "category": result["category"],
            "priority": result["priority"],
            "classification_confidence": result["confidence"],
            "classification_reasoning": result["reasoning"],
            "classification_keywords": ", ".join(result["keywords_found"]),
        })
        ticket = get_ticket(conn, ticket["id"])
        conn.close()

    return jsonify(ticket), 201


# ---------------------------------------------------------------------------
# POST /tickets/import
# ---------------------------------------------------------------------------
@tickets_bp.post("/tickets/import")
def bulk_import():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided. Send a multipart/form-data request with field 'file'."}), 400

    filename = file.filename or ""
    content = file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "File must be UTF-8 encoded"}), 400

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    # also support Content-Type hint
    ct = file.content_type or ""
    if ext == "csv" or "csv" in ct:
        fmt = "csv"
    elif ext == "json" or "json" in ct:
        fmt = "json"
    elif ext == "xml" or "xml" in ct:
        fmt = "xml"
    else:
        return jsonify({"error": f"Unsupported file format '{ext}'. Use CSV, JSON, or XML."}), 400

    result = import_tickets(text, fmt)

    conn = _db()
    created = []
    failed = list(result["failed"])  # copy failures from parse stage

    for record in result["records"]:
        cleaned, errors = validate_ticket_data(record)
        if errors:
            failed.append({"row": record.get("subject", "?"), "errors": errors})
        else:
            try:
                t = create_ticket(conn, cleaned)
                created.append(t["id"])
            except Exception as e:
                failed.append({"row": record.get("subject", "?"), "errors": [str(e)]})
    conn.close()

    return jsonify({
        "total": result["total"],
        "successful": len(created),
        "failed": len(failed),
        "errors": failed,
        "created_ids": created,
    }), 200 if not failed else 207


# ---------------------------------------------------------------------------
# GET /tickets
# ---------------------------------------------------------------------------
@tickets_bp.get("/tickets")
def list_all():
    filters = {
        "status": request.args.get("status"),
        "category": request.args.get("category"),
        "priority": request.args.get("priority"),
    }
    conn = _db()
    tickets = list_tickets(conn, filters)
    conn.close()
    return jsonify(tickets), 200


# ---------------------------------------------------------------------------
# GET /tickets/:id
# ---------------------------------------------------------------------------
@tickets_bp.get("/tickets/<ticket_id>")
def get_one(ticket_id):
    conn = _db()
    ticket = get_ticket(conn, ticket_id)
    conn.close()
    if ticket is None:
        return jsonify({"error": f"Ticket '{ticket_id}' not found"}), 404
    return jsonify(ticket), 200


# ---------------------------------------------------------------------------
# PUT /tickets/:id
# ---------------------------------------------------------------------------
@tickets_bp.put("/tickets/<ticket_id>")
def update(ticket_id):
    data = request.get_json(silent=True) or {}
    cleaned, errors = validate_ticket_data(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    conn = _db()
    ticket = update_ticket(conn, ticket_id, cleaned)
    conn.close()
    if ticket is None:
        return jsonify({"error": f"Ticket '{ticket_id}' not found"}), 404
    return jsonify(ticket), 200


# ---------------------------------------------------------------------------
# DELETE /tickets/:id
# ---------------------------------------------------------------------------
@tickets_bp.delete("/tickets/<ticket_id>")
def delete(ticket_id):
    conn = _db()
    deleted = delete_ticket(conn, ticket_id)
    conn.close()
    if not deleted:
        return jsonify({"error": f"Ticket '{ticket_id}' not found"}), 404
    return "", 204


"""
POST /tickets/:id/auto-classify
"""
from flask import Blueprint, jsonify, current_app

from src.app import get_db
from src.models import get_ticket, update_ticket
from src.services.classifier import classify_ticket

classify_bp = Blueprint("classify", __name__)


@classify_bp.post("/tickets/<ticket_id>/auto-classify")
def auto_classify(ticket_id):
    conn = get_db(current_app.config["DB_PATH"])
    ticket = get_ticket(conn, ticket_id)
    if ticket is None:
        conn.close()
        return jsonify({"error": f"Ticket '{ticket_id}' not found"}), 404

    result = classify_ticket(ticket)

    update_ticket(conn, ticket_id, {
        "category": result["category"],
        "priority": result["priority"],
        "classification_confidence": result["confidence"],
        "classification_reasoning": result["reasoning"],
        "classification_keywords": ", ".join(result["keywords_found"]),
    })
    conn.close()

    return jsonify({
        "ticket_id": ticket_id,
        "category": result["category"],
        "priority": result["priority"],
        "confidence": result["confidence"],
        "reasoning": result["reasoning"],
        "keywords_found": result["keywords_found"],
    }), 200


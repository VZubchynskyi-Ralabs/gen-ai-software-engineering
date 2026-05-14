"""
Keyword-rule based ticket classifier.
Logs every decision to classifier.log in the src directory.
"""
import logging
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "classifier.log")
logging.basicConfig(
    filename=os.path.abspath(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

# ---------------------------------------------------------------------------
# Keyword dictionaries
# ---------------------------------------------------------------------------

PRIORITY_KEYWORDS = {
    "urgent": [
        "can't access", "cannot access", "critical", "production down",
        "security", "breach", "hacked", "data loss", "urgent", "emergency",
        "system down", "outage", "not working at all",
    ],
    "high": [
        "important", "blocking", "asap", "as soon as possible",
        "high priority", "major issue", "broken", "cannot login", "can't login",
    ],
    "low": [
        "minor", "cosmetic", "suggestion", "nice to have", "low priority",
        "whenever", "no rush", "small issue",
    ],
}

CATEGORY_KEYWORDS = {
    "account_access": [
        "login", "password", "2fa", "two factor", "two-factor", "sign in",
        "sign-in", "account locked", "forgot password", "reset password",
        "authentication", "access denied", "unauthorized",
    ],
    "technical_issue": [
        "error", "crash", "exception", "500", "not loading", "slow",
        "timeout", "connection refused", "server error", "bug", "broken",
        "not working", "failed", "failure",
    ],
    "billing_question": [
        "billing", "invoice", "payment", "charge", "refund", "subscription",
        "plan", "price", "pricing", "receipt", "credit card", "overcharged",
    ],
    "feature_request": [
        "feature", "enhancement", "suggestion", "request", "add support",
        "would be great", "could you add", "please add", "new feature",
        "improvement",
    ],
    "bug_report": [
        "reproduce", "steps to reproduce", "expected behavior", "actual behavior",
        "regression", "defect", "wrong result", "incorrect",
    ],
}


def _text_from_ticket(ticket):
    """Combine subject + description into a single lowercase string."""
    subject = (ticket.get("subject") or "").lower()
    desc = (ticket.get("description") or "").lower()
    return f"{subject} {desc}"


def classify_ticket(ticket):
    """
    Returns dict:
      category, priority, confidence (0-1), reasoning (str), keywords_found (list)
    """
    text = _text_from_ticket(ticket)
    found_keywords = []

    # --- Priority detection (highest precedence first) ---
    detected_priority = "medium"
    for level in ("urgent", "high", "low"):
        for kw in PRIORITY_KEYWORDS[level]:
            if kw in text:
                found_keywords.append(kw)
                detected_priority = level
                break
        if detected_priority != "medium":
            break

    # --- Category detection (score each category) ---
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text]
        scores[cat] = hits
        found_keywords.extend(hits)

    # deduplicate
    found_keywords = list(dict.fromkeys(found_keywords))

    # pick category with most hits; fall back to "other"
    best_cat = max(scores, key=lambda c: len(scores[c]))
    if len(scores[best_cat]) == 0:
        best_cat = "other"

    # --- Confidence score ---
    total_possible = (
        sum(len(v) for v in PRIORITY_KEYWORDS.values())
        + sum(len(v) for v in CATEGORY_KEYWORDS.values())
    )
    confidence = min(1.0, len(found_keywords) / max(1, total_possible) * 10)
    confidence = round(confidence, 3)

    reasoning = (
        f"Category '{best_cat}' matched {len(scores.get(best_cat, []))} keyword(s). "
        f"Priority '{detected_priority}' detected. "
        f"Total keywords matched: {len(found_keywords)}."
    )

    logging.info(
        "CLASSIFY ticket_id=%s category=%s priority=%s confidence=%.3f keywords=%s",
        ticket.get("id", "N/A"),
        best_cat,
        detected_priority,
        confidence,
        found_keywords,
    )

    return {
        "category": best_cat,
        "priority": detected_priority,
        "confidence": confidence,
        "reasoning": reasoning,
        "keywords_found": found_keywords,
    }


# API Reference

Base URL: `http://localhost:5000`

---

## Data Models

### Ticket Object

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "CUST-001",
  "customer_email": "alice@example.com",
  "customer_name": "Alice Smith",
  "subject": "Cannot login to my account",
  "description": "I cannot login since yesterday. Error says invalid credentials.",
  "category": "account_access",
  "priority": "high",
  "status": "new",
  "created_at": "2026-05-14T10:00:00+00:00",
  "updated_at": "2026-05-14T10:00:00+00:00",
  "resolved_at": null,
  "assigned_to": "agent1@support.com",
  "tags": ["login", "urgent"],
  "metadata": {
    "source": "api",
    "browser": "Chrome",
    "device_type": "desktop"
  },
  "classification_confidence": 0.85,
  "classification_reasoning": "Category 'account_access' matched 3 keyword(s).",
  "classification_keywords": "login, password, authentication"
}
```

### Enumerations

| Field | Allowed Values |
|-------|---------------|
| `category` | `account_access`, `technical_issue`, `billing_question`, `feature_request`, `bug_report`, `other` |
| `priority` | `urgent`, `high`, `medium`, `low` |
| `status` | `new`, `in_progress`, `waiting_customer`, `resolved`, `closed` |
| `metadata.source` | `web_form`, `email`, `api`, `chat`, `phone` |
| `metadata.device_type` | `desktop`, `mobile`, `tablet` |

---

## Endpoints

### POST /tickets

Create a new support ticket.

**Required fields:** `customer_id`, `customer_email`, `customer_name`, `subject` (1-200 chars), `description` (10-2000 chars)

**Query params:**
- `auto_classify=true` — run auto-classification after creation

**Request:**
```bash
curl -X POST http://localhost:5000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-001",
    "customer_email": "alice@example.com",
    "customer_name": "Alice Smith",
    "subject": "Cannot login to my account",
    "description": "I cannot login since yesterday. The error says invalid credentials.",
    "category": "account_access",
    "priority": "high",
    "metadata": { "source": "web_form", "device_type": "desktop" },
    "tags": ["login", "auth"]
  }'
```

**Response `201 Created`:**
```json
{ "id": "550e8400...", "status": "new", "category": "account_access", ... }
```

**Response `400 Bad Request`:**
```json
{ "errors": ["'customer_email' must be a valid email address"] }
```

---

### GET /tickets

List all tickets with optional filtering.

**Query params:** `status`, `category`, `priority`

```bash
# All tickets
curl http://localhost:5000/tickets

# Filter by status
curl "http://localhost:5000/tickets?status=new"

# Filter by category and priority
curl "http://localhost:5000/tickets?category=billing_question&priority=high"
```

**Response `200 OK`:** Array of ticket objects, ordered by `created_at` descending.

---

### GET /tickets/:id

Get a specific ticket by ID.

```bash
curl http://localhost:5000/tickets/550e8400-e29b-41d4-a716-446655440000
```

**Response `200 OK`:** Single ticket object.  
**Response `404 Not Found`:** `{ "error": "Ticket '...' not found" }`

---

### PUT /tickets/:id

Update one or more fields of a ticket (partial update).

```bash
curl -X PUT http://localhost:5000/tickets/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "assigned_to": "agent2@support.com",
    "priority": "urgent"
  }'
```

**Response `200 OK`:** Updated ticket object.  
**Response `404 Not Found`:** Ticket not found.  
**Response `400 Bad Request`:** Validation errors.

---

### DELETE /tickets/:id

Delete a ticket permanently.

```bash
curl -X DELETE http://localhost:5000/tickets/550e8400-e29b-41d4-a716-446655440000
```

**Response `204 No Content`:** Ticket deleted.  
**Response `404 Not Found`:** Ticket not found.

---

### POST /tickets/import

Bulk import tickets from a file.

**Supported formats:** CSV, JSON, XML (detected by file extension)

```bash
# Import CSV
curl -X POST http://localhost:5000/tickets/import \
  -F "file=@tests/fixtures/sample_tickets.csv"

# Import JSON
curl -X POST http://localhost:5000/tickets/import \
  -F "file=@tests/fixtures/sample_tickets.json"

# Import XML
curl -X POST http://localhost:5000/tickets/import \
  -F "file=@tests/fixtures/sample_tickets.xml"
```

**Response `200 OK` (all succeeded):**
```json
{
  "total": 50,
  "successful": 50,
  "failed": 0,
  "errors": [],
  "created_ids": ["uuid1", "uuid2", "..."]
}
```

**Response `207 Multi-Status` (partial success):**
```json
{
  "total": 50,
  "successful": 48,
  "failed": 2,
  "errors": [
    { "row": "Bad subject", "errors": ["'customer_email' must be a valid email address"] }
  ],
  "created_ids": [...]
}
```

**Response `400 Bad Request`:** No file provided or unsupported format.

---

### POST /tickets/:id/auto-classify

Automatically classify a ticket's category and priority using keyword rules.

```bash
curl -X POST http://localhost:5000/tickets/550e8400-e29b-41d4-a716-446655440000/auto-classify
```

**Response `200 OK`:**
```json
{
  "ticket_id": "550e8400-...",
  "category": "account_access",
  "priority": "high",
  "confidence": 0.312,
  "reasoning": "Category 'account_access' matched 3 keyword(s). Priority 'high' detected. Total keywords matched: 4.",
  "keywords_found": ["login", "password", "cannot login", "blocking"]
}
```

---

## Error Format

All error responses follow this format:

| Status | Meaning | Body |
|--------|---------|------|
| `400` | Validation failed | `{ "errors": ["..."] }` |
| `404` | Resource not found | `{ "error": "Ticket '...' not found" }` |
| `207` | Partial success (import) | `{ "total": N, "failed": N, "errors": [...] }` |


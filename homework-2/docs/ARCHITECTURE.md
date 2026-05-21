# Architecture

This document describes the architectural decisions and structure of the ticket management system. The application is built as a lightweight Flask REST API backed by SQLite, intentionally avoiding heavy frameworks to keep the codebase transparent and easy to reason about. The layered design (routes → services → models → database) enforces a clear separation of concerns: route handlers deal only with HTTP concerns, service modules encapsulate business logic (parsing and classification), and `models.py` owns data validation and persistence. This makes it straightforward to swap any layer independently — for example, replacing SQLite with PostgreSQL or the keyword classifier with an ML model — without touching the rest of the system.

## High-Level Architecture

```mermaid
graph LR
    subgraph Client Layer
        CLI["cURL / HTTP Client"]
        APP["Frontend App"]
    end

    subgraph Flask Application
        Router["URL Router (Blueprints)"]
        TicketRoutes["tickets.py\nCRUD + Import"]
        ClassifyRoutes["classify.py\nAuto-Classify"]
    end

    subgraph Services
        Importer["importer.py\nCSV/JSON/XML Parser"]
        Classifier["classifier.py\nKeyword Engine"]
    end

    subgraph Data Layer
        Models["models.py\nValidation + SQL"]
        SQLite["SQLite database.db"]
    end

    CLI --> Router
    APP --> Router
    Router --> TicketRoutes
    Router --> ClassifyRoutes
    TicketRoutes --> Importer
    TicketRoutes --> Models
    ClassifyRoutes --> Classifier
    ClassifyRoutes --> Models
    Models --> SQLite
```

---

## Component Descriptions

| Component | File | Responsibility |
|-----------|------|---------------|
| **App Factory** | `src/app.py` | Creates Flask app, registers blueprints, initializes SQLite schema |
| **Models** | `src/models.py` | Field validation (email, enums, lengths), raw SQL CRUD helpers, UUID generation |
| **Ticket Routes** | `src/routes/tickets.py` | 6 CRUD endpoints + `POST /tickets/import` |
| **Classify Route** | `src/routes/classify.py` | `POST /tickets/:id/auto-classify` |
| **Importer** | `src/services/importer.py` | Stateless parsers for CSV (`csv`), JSON (`json`), XML (`xml.etree.ElementTree`) |
| **Classifier** | `src/services/classifier.py` | Keyword dictionaries for priority/category scoring, confidence calculation, decision logging |

---

## Data Flow: Create Ticket with Auto-Classify

```mermaid
sequenceDiagram
    participant C as HTTP Client
    participant R as tickets.py
    participant V as models.py (validate)
    participant DB as SQLite
    participant CL as classifier.py

    C->>R: POST /tickets?auto_classify=true
    R->>V: validate_ticket_data(body)
    V-->>R: cleaned_data | errors
    alt validation errors
        R-->>C: 400 { errors: [...] }
    else valid
        R->>DB: create_ticket(cleaned_data)
        DB-->>R: ticket (with UUID + timestamps)
        R->>CL: classify_ticket(ticket)
        CL-->>R: { category, priority, confidence, keywords }
        R->>DB: update_ticket(classification fields)
        DB-->>R: updated ticket
        R-->>C: 201 ticket JSON
    end
```

---

## Data Flow: Bulk Import

```mermaid
sequenceDiagram
    participant C as HTTP Client
    participant R as tickets.py
    participant I as importer.py
    participant V as models.py (validate)
    participant DB as SQLite

    C->>R: POST /tickets/import (multipart file)
    R->>I: parse_csv/json/xml(text)
    I-->>R: { records[], failed[] }
    loop For each record
        R->>V: validate_ticket_data(record)
        alt invalid
            R->>R: add to failed list
        else valid
            R->>DB: create_ticket(record)
        end
    end
    R-->>C: 200/207 { total, successful, failed, errors }
```

---

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **ORM vs raw SQL** | Raw `sqlite3` | Zero dependencies, transparent queries, easy to understand |
| **Validation** | Custom helpers in `models.py` | No Pydantic/Marshmallow dependency; straightforward dict-in → dict-out |
| **Classification** | Keyword rules | Fully offline, deterministic, fast, easy to extend |
| **Confidence score** | `matched / total * 10` capped at 1.0 | Simple heuristic; weights keyword breadth over exact match count |
| **Storage** | SQLite WAL mode | Supports concurrent reads, safe writes, no server needed |
| **Blueprints** | Two separate blueprints | Separation of concerns; classify logic is a distinct domain |

---

## Security Considerations

- **No authentication** — add JWT/API-key middleware before production
- **SQL injection** — all queries use parameterized `?` placeholders
- **File upload** — content decoded as UTF-8; malformed files return 400 not 500
- **Input validation** — email regex, enum allow-lists, string length limits

## Performance Considerations

- SQLite WAL mode for concurrent read/write
- Single connection per request (no connection pool needed at this scale)
- Classifier is pure in-memory keyword scanning — sub-millisecond per ticket
- Bulk import processes records in a single transaction loop


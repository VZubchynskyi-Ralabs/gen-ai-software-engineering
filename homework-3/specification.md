# Transaction Dispute System Specification

> Ingest the information from this file, implement the Low-Level Tasks, and generate the code that will satisfy the High and Mid-Level Objectives.

---

## High-Level Objective

Build a **secure, compliant transaction dispute intake and resolution system** that enables end-users to report fraudulent or erroneous transactions, tracks dispute lifecycle from submission through resolution, maintains complete audit trails for regulatory compliance, and provides internal ops/compliance teams with efficient dispute management tools—all while protecting sensitive financial data and ensuring PCI DSS and SOC 2 compliance.

**Scope boundary:** This system covers dispute creation, evidence upload, status tracking, communication workflow, and resolution recording. It does **not** include automated fraud detection algorithms, direct integration with card networks (Visa/Mastercard dispute APIs), or external third-party dispute arbitration services.

---

## Mid-Level Objectives

### MO-1: Secure Dispute Intake
**Observable outcome:** End-users can submit disputes for specific transactions through an authenticated API, providing dispute reason, evidence, and narrative description. Each submission generates a unique, immutable dispute record logged in the audit system.

**Verification checkpoint:**
- Unit tests verify input validation (amount matching, valid transaction ID, enum reason codes)
- Integration test confirms dispute created in database with all required fields
- Manual review: Check CloudWatch logs show no PII in plain text

### MO-2: Evidence Management with Encryption
**Observable outcome:** Users can attach up to 5 evidence files (receipts, screenshots, emails) per dispute. Files are encrypted at rest (AES-256), stored in S3 with signed URLs valid for 24 hours, and access-logged for compliance audits.

**Verification checkpoint:**
- Unit tests ensure file type validation (whitelist: PDF, PNG, JPG) and size limits (10MB per file)
- Integration test uploads file and retrieves via signed URL
- Security review: Confirm S3 bucket policies block public access; encryption enabled

### MO-3: Workflow State Management
**Observable outcome:** Disputes transition through defined states (`SUBMITTED` → `UNDER_REVIEW` → `PENDING_EVIDENCE` → `RESOLVED_APPROVED` / `RESOLVED_DENIED`) with timestamps and actor attribution for each transition. State changes are idempotent and transactional.

**Verification checkpoint:**
- Unit tests validate state machine transitions (invalid transitions raise errors)
- Integration test confirms concurrent state updates handled correctly (optimistic locking)
- End-to-end test: Submit dispute → ops marks under review → resolution → verify full audit chain

### MO-4: Compliance Audit Trail
**Observable outcome:** Every create, read, update, and delete operation on disputes is logged immutably to a write-only audit log with `user_id`, `timestamp`, `action`, `old_value`, `new_value`, `IP_address`, and `request_id`. Logs are tamper-evident and retained for 7 years per regulatory requirements.

**Verification checkpoint:**
- Review sample logs for completeness (all required fields present)
- Integration test verifies read-only audit table (attempted DELETE fails)
- Compliance checklist: Confirm log rotation policy, S3 lifecycle to Glacier after 90 days

### MO-5: Internal Ops Dashboard Access
**Observable outcome:** Ops and compliance users can query disputes by status, date range, user ID, amount threshold, and dispute reason via paginated API endpoints. Results exclude sensitive PAN data unless user has elevated `VIEW_PCI` permission.

**Verification checkpoint:**
- Unit tests verify RBAC enforcement (standard ops cannot see full PAN)
- Performance test: Query with 100K disputes returns first page in <500ms
- Manual review: Confirm pagination metadata (total count, next cursor) present

### MO-6: Performance and Rate Limits
**Observable outcome:** API endpoints meet latency targets (p95 < 300ms for dispute creation, p99 < 1s for queries). Rate limiting prevents abuse: 10 disputes/hour per user, 1000 API calls/minute per API key.

**Verification checkpoint:**
- Load test: Create 100 disputes concurrently, measure p95/p99 latencies
- Rate limit test: Trigger 429 errors after threshold exceeded
- Monitoring: CloudWatch dashboards show real-time latency metrics

---

## Non-Functional Requirements & Policy

### Security
- **Authentication:** OAuth 2.0 bearer tokens (JWT) with 15-minute expiration, RSA-256 signatures
- **Authorization:** Role-based access control (RBAC) enforced at API gateway and application layer
  - `END_USER`: Submit disputes, view own disputes
  - `OPS_ANALYST`: View all disputes, update status, request evidence
  - `COMPLIANCE_ADMIN`: Full access including PCI data, export audit logs
- **Data Encryption:**
  - **At rest:** AES-256 for database columns (`evidence_description`, `narrative`), S3 server-side encryption (SSE-KMS)
  - **In transit:** TLS 1.3 only, enforce HSTS headers, certificate pinning for mobile clients
- **PCI DSS Compliance:**
  - **NEVER** log full PAN (Primary Account Number); mask to last 4 digits in all logs and non-secure storage
  - Tokenize card data; dispute system stores only token references
  - Annual PCI audit checklist integrated into compliance verification
- **Secrets Management:** AWS Secrets Manager for database credentials, API keys; rotation every 90 days

### Privacy & Data Handling
- **GDPR/CCPA:** Disputes contain personal data; implement data subject access request (DSAR) export and right-to-erasure (soft delete with audit trace)
- **Data Retention:** Active disputes retained indefinitely; resolved disputes archived after 7 years to cold storage, then purged
- **PII Minimization:** Collect only necessary fields; evidence descriptions sanitized to remove accidental PII before indexing

### Audit & Logging
- **Audit Log Schema:**
  ```
  {
    "event_id": "UUID",
    "timestamp": "ISO8601",
    "user_id": "UUID",
    "action": "DISPUTE_CREATED | STATUS_UPDATED | EVIDENCE_UPLOADED",
    "dispute_id": "UUID",
    "old_value": "JSON",
    "new_value": "JSON",
    "ip_address": "IP",
    "user_agent": "string",
    "request_id": "UUID"
  }
  ```
- **Immutability:** Audit logs stored in append-only DynamoDB table with WORM (write-once, read-many) policy
- **Reconciliation:** Daily batch job compares dispute count in main DB vs audit log entries; alert on mismatch

### Reliability
- **Uptime SLA:** 99.9% availability (excluding scheduled maintenance)
- **Disaster Recovery:** RPO = 15 minutes (continuous replication), RTO = 1 hour (automated failover to secondary region)
- **Idempotency:** Dispute creation accepts `idempotency_key` header; duplicate requests within 24 hours return cached 201 response
- **Error Handling:**
  - 4xx errors return structured JSON with `error_code`, `message`, `field_errors`
  - 5xx errors logged with correlation ID, generic message to client (no stack traces)

### Performance Expectations (Assumed Targets)

| Metric | Target | Justification |
|--------|--------|---------------|
| **Dispute Creation Latency** | p50 < 150ms, p95 < 300ms, p99 < 500ms | FinTech UX expectation: sub-second for critical flows; 95th percentile accounts for DB write + audit log |
| **Query Disputes Latency** | p50 < 100ms, p95 < 200ms, p99 < 1s | Read-heavy queries with indexed filters; p99 allows for cold cache scenarios |
| **Evidence Upload** | p95 < 2s for 5MB file | S3 multipart upload; network variance accounted for |
| **Throughput** | 500 disputes created/second | Peak load assumption: 1M users, 0.5% dispute rate daily = ~5K disputes/day, 10x buffer for spikes |
| **Database Connections** | Max 200 concurrent connections | PostgreSQL connection pooling (PgBouncer), prevents connection exhaustion |
| **Pagination Limit** | 100 disputes per page, max offset 10K | Prevents deep pagination performance degradation; use cursor-based for ops tools |
| **Rate Limits** | 10 disputes/hour/user, 1000 API calls/min/key | Anti-abuse: prevents dispute spam; ops keys higher limit |

**Justification:** Targets derived from industry benchmarks (Stripe API latency standards), expected user behavior (low dispute frequency), and compliance needs (audit log write performance non-blocking).

---

## Implementation Notes

### Data Handling Rules

1. **Monetary Values:**
   - **Use Python `decimal.Decimal`** for all amounts; precision = 2 decimal places
   - Store in database as `NUMERIC(15,2)` (supports up to $9,999,999,999,999.99)
   - API returns money as string with currency code: `{"amount": "125.50", "currency": "USD"}`
   - **NEVER** use `float` for money calculations (introduces rounding errors)

2. **Dispute ID Format:**
   - UUIDv4 for globally unique identifiers
   - External-facing ID: `DIS-{YYYYMMDD}-{SHORT_HASH}` (e.g., `DIS-20260522-A7F3`)
   - Internal primary key: UUID stored in database

3. **Transaction ID References:**
   - Accept external transaction ID from payment processor (e.g., Stripe `ch_xxx`, internal `TXN-xxx`)
   - Validate transaction exists and belongs to requesting user before allowing dispute

4. **Enum Values (Case-Sensitive):**
   - **Dispute Reasons:** `FRAUDULENT`, `DUPLICATE_CHARGE`, `PRODUCT_NOT_RECEIVED`, `PRODUCT_DEFECTIVE`, `AMOUNT_INCORRECT`, `SUBSCRIPTION_CANCELLED`, `OTHER`
   - **Dispute Status:** `SUBMITTED`, `UNDER_REVIEW`, `PENDING_EVIDENCE`, `PENDING_USER_RESPONSE`, `RESOLVED_APPROVED`, `RESOLVED_DENIED`, `WITHDRAWN`
   - Store as VARCHAR in DB; validate against enum in application layer

5. **File Handling:**
   - **Whitelist:** `.pdf`, `.png`, `.jpg`, `.jpeg` only (check magic bytes, not just extension)
   - **Size Limit:** 10MB per file, 50MB total per dispute
   - **Virus Scan:** Integrate ClamAV or AWS S3 malware scanning before acceptance
   - **Naming Convention:** `{dispute_id}/{timestamp}_{sanitized_filename}.{ext}`

6. **Timestamps:**
   - Store in UTC in database (`TIMESTAMP WITH TIME ZONE`)
   - API returns ISO8601 format with timezone: `2026-05-22T14:30:00Z`
   - Never use local time for business logic

### Error Semantics

- **400 Bad Request:** Invalid input (wrong enum, missing required field, amount > transaction amount)
- **401 Unauthorized:** Missing or invalid JWT token
- **403 Forbidden:** Valid token but insufficient permissions (e.g., user trying to access another user's dispute)
- **404 Not Found:** Dispute ID or transaction ID not found
- **409 Conflict:** Duplicate idempotency key for different request body, or invalid state transition
- **422 Unprocessable Entity:** Business logic validation failure (e.g., dispute window expired, transaction already fully refunded)
- **429 Too Many Requests:** Rate limit exceeded; include `Retry-After` header
- **500 Internal Server Error:** Unexpected errors; log internally, return generic message
- **503 Service Unavailable:** Database or S3 temporarily down; retry with exponential backoff

### Idempotency Strategy

- **Header:** `Idempotency-Key: {UUID}` for POST endpoints
- **Implementation:** Store hash of request body + idempotency key in Redis (TTL = 24 hours)
- **Behavior:**
  - First request: Process normally, cache response
  - Duplicate key + same body: Return cached 201 response
  - Duplicate key + different body: Return 409 Conflict
- **Apply to:** Dispute creation, evidence upload, status updates

### Code Conventions

- **Framework:** FastAPI 0.110+ with Pydantic v2 for validation
- **ORM:** SQLAlchemy 2.0+ (async mode) with Alembic migrations
- **Database:** PostgreSQL 15+ (JSON columns for flexible metadata)
- **Async:** Use `async`/`await` throughout; `asyncpg` driver for DB
- **Type Hints:** Mandatory for all functions; use `mypy` in strict mode
- **Naming:**
  - Files: `snake_case.py`
  - Classes: `PascalCase` (e.g., `DisputeService`)
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- **Testing:** `pytest` with `pytest-asyncio`; target 80%+ coverage for business logic
- **Linting:** `ruff` for fast linting, `bandit` for security checks

---

## Context

### Beginning Context

**Assumed existing infrastructure:**
- **API Gateway:** AWS API Gateway or similar with JWT authorizer configured
- **Database:** PostgreSQL 15 instance (RDS) with connection pooling
- **Object Storage:** AWS S3 bucket with KMS encryption configured
- **Secrets Manager:** AWS Secrets Manager or Vault with database credentials
- **Logging:** CloudWatch Logs or ELK stack for application logs
- **Monitoring:** Prometheus + Grafana or CloudWatch dashboards
- **Authentication Service:** Existing OAuth 2.0 provider issuing JWTs with user roles

**Assumed existing data models:**
- **Users Table:** `id (UUID)`, `email`, `role (enum)`, `created_at`
- **Transactions Table:** `id (UUID)`, `user_id`, `amount (NUMERIC)`, `currency`, `status`, `transaction_date`, `merchant_name`

**File structure at start:**
```
dispute-system/
├── .env.example
├── .gitignore
├── pyproject.toml (Poetry)
├── README.md
└── src/
    └── (empty)
```

### Ending Context

**Deliverables after implementation:**

**File structure:**
```
dispute-system/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
├── alembic.ini
├── alembic/
│   ├── versions/
│   │   └── 001_create_disputes_tables.py
├── src/
│   ├── __init__.py
│   ├── main.py (FastAPI app)
│   ├── config.py (Pydantic Settings)
│   ├── database.py (SQLAlchemy setup)
│   ├── dependencies.py (DI for auth, db)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dispute.py (SQLAlchemy models)
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── dispute.py (Pydantic schemas)
│   │   └── common.py (enums, shared types)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dispute_service.py
│   │   ├── evidence_service.py
│   │   └── audit_service.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── disputes.py (endpoints)
│   │   │   └── ops.py (ops endpoints)
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py (JWT validation)
│   │   └── rate_limit.py
│   └── utils/
│       ├── __init__.py
│       ├── s3_client.py
│       └── id_generator.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_dispute_service.py
│   │   └── test_evidence_service.py
│   ├── integration/
│   │   └── test_dispute_flow.py
│   └── fixtures/
│       └── sample_disputes.json
└── docs/
    ├── API.md (OpenAPI spec)
    └── RUNBOOK.md (ops guide)
```

**Database tables created:**
- **disputes:** `id`, `external_id`, `user_id`, `transaction_id`, `amount`, `currency`, `reason`, `status`, `narrative`, `created_at`, `updated_at`, `resolved_at`, `resolution_notes`, `version` (for optimistic locking)
- **evidence_files:** `id`, `dispute_id`, `file_name`, `s3_key`, `file_size`, `content_type`, `uploaded_at`
- **audit_logs:** `event_id`, `timestamp`, `user_id`, `action`, `dispute_id`, `old_value`, `new_value`, `ip_address`, `user_agent`, `request_id`

**API endpoints available:**
- `POST /api/v1/disputes` - Create dispute (user)
- `GET /api/v1/disputes/{dispute_id}` - Get dispute details (user/ops)
- `PATCH /api/v1/disputes/{dispute_id}/status` - Update status (ops only)
- `POST /api/v1/disputes/{dispute_id}/evidence` - Upload evidence (user)
- `GET /api/v1/disputes/{dispute_id}/evidence/{file_id}` - Get signed URL (user/ops)
- `GET /api/v1/ops/disputes` - Query all disputes with filters (ops only)
- `GET /api/v1/ops/audit-logs` - Query audit logs (compliance only)

**Configuration:**
- `.env` file with `DATABASE_URL`, `S3_BUCKET`, `AWS_REGION`, `JWT_SECRET_KEY`, etc.
- Rate limiting configured per role
- Monitoring dashboards showing latency, error rates, dispute volume

---

## Edge Cases and Failure Modes

| Edge Case / Failure | Expected Behavior | Compliance Impact |
|---------------------|-------------------|-------------------|
| **User submits dispute for transaction > 180 days old** | Return 422 with message "Dispute window expired (180 days)"; log attempt in audit | None; business rule enforcement |
| **Concurrent status updates to same dispute** | Use optimistic locking (`version` column); second request returns 409 Conflict | Audit log shows both attempts with timestamps; no data loss |
| **User uploads malicious file (e.g., .exe renamed to .pdf)** | Validate magic bytes; if mismatch, return 400 "Invalid file type"; reject upload | Security event logged; potential PCI incident if malware detected |
| **S3 unavailable during evidence upload** | Return 503 with `Retry-After: 60` header; log error with correlation ID | No audit impact; transactional rollback ensures no orphaned DB record |
| **Database connection pool exhausted** | Queue requests with 30s timeout; if timeout exceeded, return 503; alert ops | Service degradation; audit logs may delay but eventually consistent |
| **User tries to view another user's dispute** | Return 403 Forbidden; log unauthorized access attempt in security log | Potential data breach attempt; trigger security review after 5 attempts in 1 hour |
| **Ops analyst attempts to export >10K disputes** | Return 400 with message "Use async export job for >10K records"; provide job creation endpoint | None; prevents API timeout and memory exhaustion |
| **Duplicate idempotency key with different request body** | Return 409 with message "Idempotency key conflict"; include original request timestamp | Audit log shows both requests; prevents accidental duplicate disputes |
| **JWT token expires mid-request** | Middleware rejects with 401; client must refresh token and retry | None; standard auth flow |
| **Transaction already has 3 open disputes** | Return 422 with message "Maximum open disputes reached for transaction"; allow after one resolves | Prevents dispute spam; fraud indicator flagged for review |
| **Evidence file contains embedded PII in metadata** | Strip EXIF/metadata before storing; sanitize file names (allow only alphanumeric + dash/underscore) | Protects privacy; GDPR compliance measure |
| **Partial failure in audit log write** | Dispute creation still succeeds (audit is async); retry audit log write with exponential backoff; alert if fails after 3 retries | Critical: manual reconciliation required; daily batch job detects missing entries |

---

## Low-Level Tasks

### Task 1: Database Schema and Migrations

**Prompt to execute:**
"Create SQLAlchemy models for `disputes`, `evidence_files`, and `audit_logs` tables with all required fields, constraints, and indexes. Generate Alembic migration to create these tables in PostgreSQL. Include optimistic locking version column on disputes."

**File to CREATE:**
- `src/models/dispute.py`
- `src/models/audit_log.py`
- `alembic/versions/001_create_disputes_tables.py`

**Functions/classes to CREATE:**
- `Dispute` model (SQLAlchemy)
- `EvidenceFile` model
- `AuditLog` model

**Details to drive code changes:**
- Use `NUMERIC(15,2)` for `amount` column
- Add `CHECK` constraint: `amount > 0`
- Index on `disputes.user_id`, `disputes.status`, `disputes.created_at` for query performance
- Index on `audit_logs.dispute_id`, `audit_logs.timestamp`
- `version` column (integer, default 1) for optimistic locking
- Foreign keys with `ON DELETE RESTRICT` (prevent accidental deletion)
- `created_at`, `updated_at` auto-managed by SQLAlchemy

**Acceptance Criteria:**
- [ ] Migration applies cleanly to empty PostgreSQL database
- [ ] `alembic upgrade head` succeeds without errors
- [ ] Indexes exist (verify with `\d+ disputes` in psql)
- [ ] Insert test row with `Decimal('100.50')` stores exactly 100.50

---

### Task 2: Pydantic Schemas and Validation

**Prompt to execute:**
"Create Pydantic v2 schemas for dispute creation request, dispute response, evidence upload, and common enums. Include custom validators for amount (must be positive), dispute reason (must be valid enum), file size, and transaction ID format. Use strict types."

**File to CREATE:**
- `src/schemas/dispute.py`
- `src/schemas/common.py`

**Functions/classes to CREATE:**
- `DisputeReason` (Enum)
- `DisputeStatus` (Enum)
- `DisputeCreateRequest` (Pydantic model)
- `DisputeResponse` (Pydantic model)
- `EvidenceUploadRequest`
- `EvidenceResponse`

**Details to drive code changes:**
- Use `Decimal` type from `pydantic.types`
- Custom validator: `@field_validator('amount')` ensures `amount > 0` and max 2 decimal places
- Custom validator for `narrative`: min 10 chars, max 2000 chars, sanitize HTML
- Enum members exactly as specified in Implementation Notes (case-sensitive)
- `DisputeResponse` excludes sensitive fields when serializing for non-privileged users
- Include `model_config = ConfigDict(from_attributes=True)` for ORM compatibility

**Acceptance Criteria:**
- [ ] `DisputeCreateRequest(amount=-5.00)` raises `ValidationError`
- [ ] `DisputeCreateRequest(reason="INVALID")` raises `ValidationError`
- [ ] Valid request with all fields serializes to JSON without errors
- [ ] `mypy` passes with no type errors

---

### Task 3: Dispute Service Layer

**Prompt to execute:**
"Implement `DisputeService` class with async methods: `create_dispute()`, `get_dispute()`, `update_status()`, `query_disputes()`. Include transaction ID validation, idempotency check (mock for now), and audit log integration. Use dependency injection for database session."

**File to CREATE:**
- `src/services/dispute_service.py`

**Functions to CREATE:**
- `async def create_dispute(user_id, request, idempotency_key, db_session) -> Dispute`
- `async def get_dispute(dispute_id, user_id, role, db_session) -> Dispute | None`
- `async def update_status(dispute_id, new_status, actor_id, notes, db_session) -> Dispute`
- `async def query_disputes(filters, pagination, db_session) -> list[Dispute]`

**Details to drive code changes:**
- `create_dispute()`: Validate transaction exists and belongs to user, check for duplicate disputes (same transaction + reason within 24h), generate external ID (`DIS-{date}-{hash}`), write audit log entry
- State machine validation in `update_status()`: define allowed transitions, raise `ValueError` for invalid transitions
- Use optimistic locking: `session.execute(update(...).where(Dispute.version == current_version).values(version=version+1))`
- RBAC in `get_dispute()`: if `role != COMPLIANCE_ADMIN`, mask PAN-like fields
- Pagination: use cursor-based (last `created_at` + `id`) for `query_disputes()`
- All database writes wrapped in try/except with rollback and error logging

**Acceptance Criteria:**
- [ ] Unit test: `create_dispute` with valid input creates record in DB
- [ ] Unit test: `create_dispute` with non-existent transaction_id raises error
- [ ] Unit test: `update_status(SUBMITTED -> RESOLVED_APPROVED)` succeeds
- [ ] Unit test: `update_status(RESOLVED_APPROVED -> SUBMITTED)` raises `ValueError`
- [ ] Integration test: Concurrent updates trigger optimistic lock error

---

### Task 4: Evidence Upload Service with S3

**Prompt to execute:**
"Implement `EvidenceService` with methods to upload files to S3 with encryption, validate file types using magic bytes, generate signed URLs with 24-hour expiration, and record metadata in `evidence_files` table. Integrate virus scanning hook (placeholder)."

**File to CREATE:**
- `src/services/evidence_service.py`
- `src/utils/s3_client.py`

**Functions to CREATE:**
- `async def upload_evidence(dispute_id, file, user_id, db_session) -> EvidenceFile`
- `async def get_evidence_url(dispute_id, file_id, user_id, db_session) -> str`
- `async def validate_file_type(file_bytes) -> bool` (check magic bytes)
- `async def put_object_s3(bucket, key, body, content_type) -> None`
- `async def generate_presigned_url(bucket, key, expiration=86400) -> str`

**Details to drive code changes:**
- Use `python-magic` or `filetype` library to check magic bytes (not extension)
- Whitelist: `[b'\x89PNG', b'\xff\xd8\xff', b'%PDF']` for PNG, JPEG, PDF
- S3 key format: `disputes/{dispute_id}/evidence/{timestamp}_{sanitized_filename}`
- S3 `PutObject` with `ServerSideEncryption='aws:kms'` and `Metadata={'uploaded_by': user_id}`
- Signed URL generated with `boto3.client.generate_presigned_url('get_object', ...)`
- Placeholder for virus scan: `if await scan_for_virus(file_bytes): raise ValueError("Malware detected")`
- Store `evidence_files` record only after successful S3 upload (transactional consistency)

**Acceptance Criteria:**
- [ ] Unit test: Upload valid PDF → S3 object exists with encryption
- [ ] Unit test: Upload .exe renamed to .pdf → raises `ValueError("Invalid file type")`
- [ ] Integration test: Upload file → retrieve signed URL → verify URL accessible for 24h
- [ ] Integration test: File >10MB → raises `ValueError("File too large")`

---

### Task 5: Audit Logging Service

**Prompt to execute:**
"Create `AuditService` to log all CRUD operations on disputes. Implement async method `log_event(action, user_id, dispute_id, old_value, new_value, metadata)` that writes to immutable `audit_logs` table. Include request context (IP, user agent, request ID) extraction."

**File to CREATE:**
- `src/services/audit_service.py`

**Functions to CREATE:**
- `async def log_event(action, user_id, dispute_id, old_value, new_value, ip, user_agent, request_id, db_session) -> None`
- `async def get_audit_trail(dispute_id, db_session) -> list[AuditLog]`
- `def serialize_for_audit(obj) -> dict` (convert Pydantic/SQLAlchemy to JSON)

**Details to drive code changes:**
- `log_event()` inserts into `audit_logs` (no updates/deletes allowed on this table)
- Use `event_id = uuid4()`, `timestamp = datetime.utcnow()`
- Serialize `old_value` and `new_value` as JSON strings (handle Decimal, datetime serialization)
- Extract IP from `request.client.host`, user agent from `request.headers.get('user-agent')`
- Request ID from `request.state.request_id` (set by middleware)
- Handle serialization of sensitive fields: mask PAN to last 4 digits before logging
- Fire-and-forget pattern: if audit write fails, log error but don't block main transaction (use asyncio.create_task)

**Acceptance Criteria:**
- [ ] Unit test: `log_event(DISPUTE_CREATED, ...)` inserts row in audit_logs
- [ ] Unit test: Attempted delete on audit_logs raises DB error (via constraint or app logic)
- [ ] Integration test: Create dispute → verify audit log entry exists with correct action and values
- [ ] Unit test: Serialize Decimal(100.50) to "100.50" in JSON

---

### Task 6: FastAPI Endpoints for Dispute CRUD

**Prompt to execute:**
"Implement FastAPI endpoints for dispute creation, retrieval, and status update. Include JWT authentication dependency, RBAC checks, idempotency header handling, request validation via Pydantic, and error handling middleware. Return structured JSON errors."

**File to CREATE:**
- `src/api/v1/disputes.py`
- `src/dependencies.py`
- `src/middleware/auth.py`

**Functions to CREATE:**
- `@router.post("/disputes", status_code=201) async def create_dispute(...)`
- `@router.get("/disputes/{dispute_id}") async def get_dispute(...)`
- `@router.patch("/disputes/{dispute_id}/status") async def update_dispute_status(...)`
- `async def get_current_user(token: str = Depends(oauth2_scheme)) -> User` (dependency)
- `async def require_role(required_role: str) -> Callable` (dependency factory)

**Details to drive code changes:**
- Extract `Idempotency-Key` from headers (required for POST); validate UUID format
- Use `Depends(get_current_user)` to inject authenticated user into endpoint
- RBAC: `create_dispute` requires `END_USER` or higher; `update_dispute_status` requires `OPS_ANALYST`
- Call `DisputeService.create_dispute()` in endpoint, handle exceptions:
  - `ValueError` → 400/422
  - `PermissionError` → 403
  - `NotFoundError` → 404
- Return `DisputeResponse` Pydantic model; FastAPI auto-serializes to JSON
- Add exception handler for `HTTPException` and generic `Exception` (return 500 with correlation ID)
- Log all requests with correlation ID via middleware

**Acceptance Criteria:**
- [ ] Integration test: POST /disputes with valid JWT → 201, dispute created
- [ ] Integration test: POST /disputes without Idempotency-Key → 400
- [ ] Integration test: GET /disputes/{id} for other user's dispute → 403
- [ ] Integration test: PATCH /disputes/{id}/status as END_USER → 403
- [ ] Unit test: Invalid JWT → 401

---

### Task 7: Ops/Compliance Query Endpoints

**Prompt to execute:**
"Create ops-facing endpoints for querying disputes with filters (status, date range, user_id, amount) and pagination. Include cursor-based pagination, CSV export capability (async job), and audit log query endpoint restricted to COMPLIANCE_ADMIN role."

**File to CREATE:**
- `src/api/v1/ops.py`

**Functions to CREATE:**
- `@router.get("/ops/disputes") async def query_disputes(status, start_date, end_date, min_amount, max_amount, cursor, limit, current_user)`
- `@router.get("/ops/audit-logs") async def get_audit_logs(dispute_id, start_date, end_date, current_user)`

**Details to drive code changes:**
- `query_disputes`: Use `Depends(require_role("OPS_ANALYST"))` for auth
- Filters are optional query params; build SQLAlchemy query dynamically
- Cursor format: base64-encoded JSON `{"created_at": "2026-05-22T10:00:00Z", "id": "uuid"}`
- Pagination response: `{"data": [...], "next_cursor": "...", "total_count": 12345}`
- Limit max results per page to 100
- `get_audit_logs`: Requires `COMPLIANCE_ADMIN` role; no pagination limit (for compliance exports)
- Return audit logs as JSON array with all fields including IP addresses

**Acceptance Criteria:**
- [ ] Integration test: Query with `status=SUBMITTED` returns only submitted disputes
- [ ] Integration test: Query with `min_amount=100&max_amount=500` returns correct range
- [ ] Integration test: Pagination with `limit=10` returns 10 results + next_cursor
- [ ] Unit test: OPS_ANALYST calling `/ops/audit-logs` → 403
- [ ] Unit test: COMPLIANCE_ADMIN calling `/ops/audit-logs` → 200

---

### Task 8: Rate Limiting Middleware

**Prompt to execute:**
"Implement rate limiting middleware using Redis or in-memory store (async-compatible). Enforce limits: 10 disputes/hour per user_id, 1000 API calls/minute per API key. Return 429 with Retry-After header when exceeded. Include whitelist for internal services."

**File to CREATE:**
- `src/middleware/rate_limit.py`

**Functions to CREATE:**
- `async def rate_limit_middleware(request, call_next)`
- `async def check_rate_limit(key, limit, window) -> bool`
- `async def get_retry_after(key, window) -> int`

**Details to drive code changes:**
- Use sliding window algorithm with Redis (or `cachetools` TTLCache for local dev)
- Rate limit key: `dispute_create:{user_id}` for dispute creation, `api_call:{api_key}` for general API
- Store in Redis: `INCR key`, `EXPIRE key window_seconds`
- If count > limit, return 429 response with header `Retry-After: {seconds_until_reset}`
- Whitelist: Check `X-Internal-Service` header; if matches secret, skip rate limit
- Middleware runs before request processing; attach rate limit info to `request.state`

**Acceptance Criteria:**
- [ ] Integration test: Create 10 disputes rapidly → 11th returns 429
- [ ] Integration test: Wait 1 hour → rate limit resets
- [ ] Unit test: Request with `X-Internal-Service: {secret}` → bypasses rate limit
- [ ] Integration test: 429 response includes `Retry-After` header

---

### Task 9: Testing Suite (Unit + Integration)

**Prompt to execute:**
"Create comprehensive test suite covering DisputeService, EvidenceService, and API endpoints. Include unit tests for business logic, integration tests for database operations, and test fixtures for sample disputes. Use pytest with async support and database rollback per test."

**Files to CREATE:**
- `tests/conftest.py`
- `tests/unit/test_dispute_service.py`
- `tests/unit/test_evidence_service.py`
- `tests/integration/test_dispute_flow.py`
- `tests/fixtures/sample_disputes.json`

**Functions to CREATE:**
- `@pytest.fixture async def db_session()` - async DB session with rollback
- `@pytest.fixture async def sample_user()` - create test user
- `@pytest.fixture async def sample_transaction()` - create test transaction
- Test functions for each service method and endpoint (at least 15 tests total)

**Details to drive code changes:**
- Use `pytest-asyncio` for async test support
- Database setup: Use test database, run migrations before tests, rollback after each test
- Mock S3 client with `moto` library for evidence upload tests
- Mock JWT validation in integration tests (bypass auth)
- Test fixtures in JSON: 5 sample disputes with different statuses and reasons
- Coverage target: 80%+ for `src/services/` and `src/api/`
- Include parameterized tests for state transitions: `@pytest.mark.parametrize("from_status,to_status,should_succeed", [...])`

**Acceptance Criteria:**
- [ ] `pytest tests/` runs all tests successfully
- [ ] Coverage report shows >80% for services and API layers
- [ ] Integration test: Full dispute lifecycle (create → upload evidence → update status → resolve)
- [ ] Unit test: Edge case "dispute for transaction >180 days" raises error
- [ ] Mock S3 returns signed URL without actual AWS call

---

### Task 10: Configuration, Documentation, and Deployment Prep

**Prompt to execute:**
"Create configuration management using Pydantic Settings, environment variable loading, API documentation (OpenAPI spec), deployment runbook, and README with setup instructions. Include example .env file and docker-compose for local development."

**Files to CREATE:**
- `src/config.py`
- `.env.example`
- `docs/API.md`
- `docs/RUNBOOK.md`
- `docker-compose.yml` (PostgreSQL + Redis for local dev)
- Update `README.md`

**Functions to CREATE:**
- `class Settings(BaseSettings)` with validation for all config vars
- `@lru_cache() def get_settings() -> Settings` (singleton pattern)

**Details to drive code changes:**
- `Settings` includes: `DATABASE_URL`, `S3_BUCKET`, `AWS_REGION`, `JWT_SECRET_KEY`, `REDIS_URL`, `RATE_LIMIT_DISPUTES_PER_HOUR`, `LOG_LEVEL`
- Use `pydantic-settings` to auto-load from `.env` file
- `.env.example` has placeholder values (no secrets)
- `API.md`: Export OpenAPI spec from FastAPI (`app.openapi()`) and format as markdown table or include Swagger UI link
- `RUNBOOK.md`: Sections for deployment steps, monitoring dashboards, alert thresholds, disaster recovery procedure, log queries
- `docker-compose.yml`: PostgreSQL 15, Redis 7, init scripts to create test database
- README: Installation (Poetry install), migration (Alembic), running (uvicorn), testing (pytest), environment variables table

**Acceptance Criteria:**
- [ ] `docker-compose up` starts PostgreSQL and Redis
- [ ] `poetry install` installs all dependencies
- [ ] `alembic upgrade head` applies migrations to local DB
- [ ] `uvicorn src.main:app --reload` starts server on localhost:8000
- [ ] OpenAPI docs accessible at http://localhost:8000/docs
- [ ] README includes troubleshooting section with common errors

---

## Verification Summary

### Per Mid-Level Objective

| Objective | Primary Verification Method | Manual Review |
|-----------|----------------------------|---------------|
| **MO-1: Secure Dispute Intake** | Integration test (create dispute) + unit tests for validation | Check logs for PII leakage |
| **MO-2: Evidence Management** | Unit tests (file validation) + integration test (S3 upload) | Verify S3 bucket policies |
| **MO-3: Workflow State Management** | Unit tests (state machine) + integration test (concurrent updates) | Review state transition logic |
| **MO-4: Compliance Audit Trail** | Integration test (audit entries created) + manual log inspection | Confirm immutability (read-only table) |
| **MO-5: Internal Ops Dashboard** | Integration test (query with filters) + RBAC unit tests | Spot-check PAN masking in responses |
| **MO-6: Performance & Rate Limits** | Load test (100 concurrent creates) + rate limit integration test | CloudWatch dashboard review |

### Acceptance Checklist
- [ ] All 10 low-level tasks completed with files created
- [ ] Test suite passes with >80% coverage
- [ ] Alembic migrations apply cleanly
- [ ] OpenAPI docs generated and reviewed
- [ ] No security vulnerabilities flagged by Bandit
- [ ] No PII in logs (manual grep for email/SSN patterns)
- [ ] Rate limiting functional (429 errors triggered)
- [ ] Optimistic locking prevents concurrent update bugs
- [ ] S3 encryption enabled (verified via AWS Console)
- [ ] Audit logs immutable (DELETE fails)

---

## Appendix: Compliance & Security Checklist

### PCI DSS Requirements Addressed

✅ **6.5.1 Injection flaws:** SQLAlchemy ORM prevents SQL injection  
✅ **6.5.3 Insecure cryptographic storage:** AES-256 at rest, TLS 1.3 in transit  
✅ **6.5.7 Cross-site scripting (XSS):** Input sanitization in Pydantic validators  
✅ **6.5.10 Broken authentication:** JWT with short expiration, secure token validation  
✅ **8.2.1 Strong cryptography:** bcrypt/Argon2 for passwords (if auth is in-scope)  
✅ **10.1 Audit trails:** Immutable audit logs for all access  
✅ **10.3 Timestamp integrity:** UTC timestamps, NTP sync assumed

### SOC 2 Controls

✅ **CC6.1 Logical access controls:** RBAC enforced at API and service layers  
✅ **CC6.6 Encryption:** KMS for S3, TLS for network traffic  
✅ **CC7.2 Monitoring:** CloudWatch logs and metrics (assumed configured)  
✅ **CC8.1 Change management:** Alembic migrations tracked in version control

### GDPR Compliance

✅ **Article 17 Right to erasure:** Soft delete with audit trail (implementation note in spec)  
✅ **Article 32 Security of processing:** Encryption, pseudonymization (tokenized PAN)  
✅ **Article 33 Breach notification:** Logging of unauthorized access attempts

---

**End of Specification**


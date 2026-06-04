# Agent Configuration for Transaction Dispute System

## Overview

This document defines how AI agents (GitHub Copilot, ChatGPT, Claude, etc.) should behave when generating code, documentation, or providing assistance for the **Transaction Dispute System**—a finance-oriented application requiring strict compliance with security, audit, and regulatory standards.

**Purpose:** Ensure consistent, secure, compliant, and high-quality code generation aligned with FinTech best practices.

---

## Technology Stack

### Core Technologies
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.110+ (async web framework)
- **ORM:** SQLAlchemy 2.0+ with Alembic for migrations
- **Database:** PostgreSQL 15+ (primary data store)
- **Cache/Queue:** Redis 7+ (rate limiting, idempotency caching)
- **Object Storage:** AWS S3 with KMS encryption
- **Validation:** Pydantic v2 (strict mode with type hints)
- **Testing:** pytest with pytest-asyncio
- **Async Driver:** asyncpg (PostgreSQL), aioredis (Redis)

### Development Tools
- **Dependency Management:** Poetry 1.5+
- **Linting:** Ruff (fast Python linter)
- **Formatting:** Black (line length 100)
- **Type Checking:** mypy (strict mode)
- **Security Scanning:** Bandit, Safety
- **Pre-commit Hooks:** ruff, black, mypy, bandit

### Infrastructure (Assumed)
- **Deployment:** AWS ECS/Fargate or Kubernetes
- **API Gateway:** AWS API Gateway with JWT authorizer
- **Secrets Management:** AWS Secrets Manager
- **Logging:** CloudWatch Logs or ELK stack
- **Monitoring:** Prometheus + Grafana or CloudWatch
- **CI/CD:** GitHub Actions or GitLab CI

---

## Domain Rules: Finance & Banking

### Financial Data Handling

1. **Monetary Values - CRITICAL**
   - ✅ **ALWAYS** use `decimal.Decimal` for money amounts
   - ❌ **NEVER** use `float` or `double` for monetary calculations (introduces rounding errors)
   - ✅ Store in database as `NUMERIC(15,2)` or `NUMERIC(19,4)` for precision
   - ✅ API serialization: Return money as strings with currency codes
     ```python
     # CORRECT
     from decimal import Decimal
     amount = Decimal("100.50")
     
     # INCORRECT
     amount = 100.50  # float, FORBIDDEN for money
     ```
   
2. **Currency Handling**
   - ✅ Always store currency code (ISO 4217: USD, EUR, GBP, etc.) alongside amounts
   - ✅ Use separate columns: `amount NUMERIC(15,2)`, `currency VARCHAR(3)`
   - ✅ Validate currency codes against allowed list
   - ❌ Never assume a default currency; make it explicit

3. **Transaction Idempotency**
   - ✅ **ALWAYS** implement idempotency for state-changing operations (POST, PATCH)
   - ✅ Use `Idempotency-Key` header (UUID format)
   - ✅ Cache results for 24 hours in Redis
   - ✅ Return cached response for duplicate requests with same key + body
   - ❌ Raise 409 Conflict for duplicate key with different body

4. **Dispute-Specific Rules**
   - ✅ Verify user owns transaction before allowing dispute creation
   - ✅ Enforce dispute window (e.g., 180 days from transaction date)
   - ✅ Limit open disputes per transaction (e.g., max 3)
   - ✅ Validate dispute amount ≤ transaction amount
   - ✅ Generate human-readable external IDs: `DIS-{YYYYMMDD}-{SHORT_HASH}`

### Regulatory & Compliance

1. **PCI DSS (Payment Card Industry Data Security Standard)**
   - ❌ **NEVER** log, display, or store full Primary Account Number (PAN)
   - ✅ Mask PAN to last 4 digits in logs, UI, non-secure storage: `****1234`
   - ✅ Use tokenization: Store only token references, not raw PAN
   - ✅ Encrypt cardholder data at rest (AES-256) and in transit (TLS 1.3)
   - ✅ Maintain audit logs for all access to cardholder data

2. **SOC 2 (System and Organization Controls)**
   - ✅ Implement comprehensive audit logging for all data access and modifications
   - ✅ Enforce least privilege access (RBAC)
   - ✅ Encrypt sensitive data at rest and in transit
   - ✅ Log all authentication attempts (success and failure)
   - ✅ Immutable audit logs (append-only, no updates/deletes)

3. **GDPR (General Data Protection Regulation)**
   - ✅ Support data subject access requests (DSAR): Export all user data in structured format
   - ✅ Support right to erasure: Soft delete with audit trail (never hard delete)
   - ✅ Minimize PII collection: Only collect necessary personal data
   - ✅ Document data retention policies (7 years for financial records)
   - ✅ Obtain explicit consent for data processing where required

4. **CCPA (California Consumer Privacy Act)**
   - ✅ Provide data export capabilities in machine-readable format
   - ✅ Honor opt-out requests for data selling (not applicable if no selling occurs)
   - ✅ Disclose data collection practices in privacy policy

---

## Code Style & Conventions

### Naming Conventions

```python
# Files
dispute_service.py          # snake_case for modules
evidence_service.py

# Classes
class DisputeService:       # PascalCase
class EvidenceFile:

# Functions and variables
async def create_dispute()  # snake_case
user_id = "..."

# Constants
MAX_EVIDENCE_FILES = 5      # UPPER_SNAKE_CASE
DISPUTE_WINDOW_DAYS = 180

# Private methods/variables
def _validate_transaction() # Leading underscore
_internal_cache = {}
```

### Type Hints (Mandatory)

```python
# ✅ ALWAYS include type hints
from typing import Optional
from uuid import UUID
from decimal import Decimal

async def create_dispute(
    user_id: UUID,
    transaction_id: UUID,
    amount: Decimal,
    reason: DisputeReason,
    db_session: AsyncSession
) -> Dispute:
    ...

# ✅ Use Pydantic for request/response models
class DisputeCreateRequest(BaseModel):
    transaction_id: UUID
    amount: Decimal
    reason: DisputeReason
    narrative: str

# ❌ AVOID untyped functions
def process_data(data):  # Bad: no type hints
    ...
```

### Async/Await Patterns

```python
# ✅ Use async/await for I/O-bound operations
async def get_dispute(dispute_id: UUID, db: AsyncSession) -> Dispute:
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    return result.scalar_one_or_none()

# ✅ Database queries
async with AsyncSession(engine) as session:
    dispute = await session.get(Dispute, dispute_id)

# ✅ Parallel async operations
results = await asyncio.gather(
    fetch_dispute(id1),
    fetch_dispute(id2),
    fetch_dispute(id3)
)

# ❌ AVOID blocking calls in async functions
# Bad: requests.get() blocks event loop
response = requests.get("https://api.example.com")  

# Good: Use aiohttp or httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### Error Handling

```python
# ✅ Use custom exceptions for business logic
class DisputeWindowExpiredError(ValueError):
    """Raised when dispute is filed after allowed window."""
    pass

# ✅ Structured error responses
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": str(exc),
            "request_id": request.state.request_id
        }
    )

# ✅ Log errors with context
logger.error(
    "Failed to create dispute",
    extra={
        "user_id": str(user_id),
        "transaction_id": str(transaction_id),
        "error": str(exc),
        "request_id": request_id
    },
    exc_info=True
)

# ❌ NEVER expose stack traces to clients
# Bad:
return JSONResponse(status_code=500, content={"error": traceback.format_exc()})

# Good:
return JSONResponse(
    status_code=500,
    content={"error": "Internal server error", "correlation_id": "abc123"}
)
```

---

## Security Best Practices

### Input Validation

```python
# ✅ Validate all inputs with Pydantic
from pydantic import BaseModel, Field, field_validator

class DisputeCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    narrative: str = Field(min_length=10, max_length=2000)
    
    @field_validator('narrative')
    def sanitize_narrative(cls, v):
        # Remove HTML tags, dangerous characters
        import bleach
        return bleach.clean(v, tags=[], strip=True)

# ✅ SQL injection prevention - use ORM
# CORRECT:
result = await db.execute(
    select(Dispute).where(Dispute.user_id == user_id)
)

# INCORRECT (vulnerable to SQL injection):
query = f"SELECT * FROM disputes WHERE user_id = '{user_id}'"
```

### Authentication & Authorization

```python
# ✅ JWT validation
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    try:
        payload = jwt.decode(
            token.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=["RS256"]
        )
        user_id = UUID(payload["sub"])
        # Validate token expiration, signature, etc.
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return await get_user_by_id(user_id)

# ✅ Role-based access control
def require_role(required_role: str):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in ROLE_HIERARCHY.get(required_role, []):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

@router.patch("/disputes/{dispute_id}/status")
async def update_status(
    dispute_id: UUID,
    user: User = Depends(require_role("OPS_ANALYST"))
):
    ...
```

### Secrets Management

```python
# ✅ Load secrets from environment/Secrets Manager
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    s3_bucket: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# ❌ NEVER hardcode secrets
# Bad:
DATABASE_URL = "postgresql://user:password@localhost/db"

# Good:
settings = Settings()
DATABASE_URL = settings.database_url
```

### Data Encryption

```python
# ✅ Encrypt sensitive fields at application level
from cryptography.fernet import Fernet

def encrypt_field(plaintext: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(plaintext.encode())

def decrypt_field(ciphertext: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(ciphertext).decode()

# ✅ S3 encryption at rest
s3_client.put_object(
    Bucket=bucket,
    Key=key,
    Body=file_bytes,
    ServerSideEncryption='aws:kms',
    SSEKMSKeyId=kms_key_id
)
```

---

## Testing & Verification Expectations

### Test Structure

```python
# ✅ Organize tests by layer
# tests/
#   unit/
#     test_dispute_service.py
#     test_evidence_service.py
#   integration/
#     test_dispute_api.py
#     test_evidence_upload.py
#   fixtures/
#     sample_data.json

# ✅ Use pytest fixtures for setup
@pytest.fixture
async def db_session():
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()  # Clean up after test

@pytest.fixture
async def sample_user(db_session):
    user = User(id=uuid4(), email="test@example.com", role="END_USER")
    db_session.add(user)
    await db_session.commit()
    return user

# ✅ Test both happy path and edge cases
async def test_create_dispute_success(db_session, sample_user):
    dispute = await create_dispute(
        user_id=sample_user.id,
        transaction_id=uuid4(),
        amount=Decimal("100.00"),
        reason=DisputeReason.FRAUDULENT,
        db_session=db_session
    )
    assert dispute.status == DisputeStatus.SUBMITTED

async def test_create_dispute_expired_window(db_session, sample_user):
    old_transaction = create_transaction(
        created_at=datetime.utcnow() - timedelta(days=200)
    )
    with pytest.raises(DisputeWindowExpiredError):
        await create_dispute(
            user_id=sample_user.id,
            transaction_id=old_transaction.id,
            amount=Decimal("100.00"),
            reason=DisputeReason.FRAUDULENT,
            db_session=db_session
        )
```

### Coverage Expectations

- **Minimum Coverage:** 80% for business logic (services, models)
- **100% Coverage:** Security-critical functions (auth, encryption, validation)
- **Integration Tests:** Test full request → response cycles with real DB (test container)
- **Mocking:** Use `unittest.mock` or `pytest-mock` for external services (S3, email)

### Security Testing

```python
# ✅ Test authorization
async def test_user_cannot_access_others_dispute(client, user1_token, user2_dispute):
    response = await client.get(
        f"/api/v1/disputes/{user2_dispute.id}",
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 403

# ✅ Test input validation
async def test_negative_amount_rejected(client, user_token):
    response = await client.post(
        "/api/v1/disputes",
        json={"amount": "-100.00", "reason": "FRAUDULENT"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400
    assert "amount" in response.json()["field_errors"]
```

---

## Edge Case Treatment Guide

### How Agents Should Handle Edge Cases

1. **Empty/Null Inputs**
   - ✅ Validate with Pydantic; raise 400 for missing required fields
   - ✅ Use `Optional[T]` for truly optional fields
   - ❌ Never assume defaults for critical fields (amount, user_id)

2. **Concurrent Modifications**
   - ✅ Use optimistic locking (version column)
   - ✅ Return 409 Conflict on version mismatch
   - ✅ Include retry logic in clients with exponential backoff

3. **Partial Failures**
   - ✅ Wrap multi-step operations in database transactions
   - ✅ Rollback on any failure to maintain consistency
   - ✅ Use compensating transactions for distributed operations

4. **External Service Failures (S3, Redis)**
   - ✅ Implement circuit breaker pattern
   - ✅ Return 503 Service Unavailable with Retry-After header
   - ✅ Degrade gracefully: Skip cache on Redis failure, queue uploads on S3 failure

5. **Large Datasets**
   - ✅ Always paginate query results (max 100 per page for user-facing, 1000 for ops)
   - ✅ Use cursor-based pagination for large tables
   - ✅ Add database query timeouts (e.g., 30 seconds)

6. **Data Corruption/Inconsistency**
   - ✅ Run daily reconciliation jobs
   - ✅ Alert on mismatches between main DB and audit logs
   - ✅ Maintain manual override endpoints (COMPLIANCE_ADMIN only)

---

## Logging Rules

### What to Log

```python
# ✅ Business events
logger.info(
    "Dispute created",
    extra={
        "dispute_id": str(dispute.id),
        "user_id": str(user.id),
        "amount": str(dispute.amount),  # Decimal as string
        "reason": dispute.reason.value
    }
)

# ✅ Security events
logger.warning(
    "Unauthorized access attempt",
    extra={
        "user_id": str(user_id),
        "resource": f"/disputes/{dispute_id}",
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }
)

# ✅ Errors with correlation ID
logger.error(
    "Failed to upload evidence",
    extra={
        "dispute_id": str(dispute_id),
        "error": str(exc),
        "correlation_id": correlation_id
    },
    exc_info=True
)
```

### What NEVER to Log

❌ **Sensitive Data:**
- Full PAN (Primary Account Number) - always mask to last 4 digits
- Full SSN/Tax ID - mask to last 4
- Passwords or password hashes
- JWT tokens (full tokens)
- API keys
- Credit card CVV

❌ **PII in Plain Text:**
- Email addresses in production logs (hash or redact)
- Phone numbers
- Full names (use user IDs instead)

✅ **Safe to Log:**
- User IDs (UUIDs)
- Dispute IDs
- Timestamps
- Status changes
- Masked PAN (e.g., `****1234`)
- IP addresses (for security audits)
- Request IDs / Correlation IDs

---

## Performance Optimization

### Database Queries

```python
# ✅ Use indexes on frequently queried columns
# Alembic migration:
op.create_index('idx_disputes_user_id', 'disputes', ['user_id'])
op.create_index('idx_disputes_status', 'disputes', ['status'])
op.create_index('idx_disputes_created_at', 'disputes', ['created_at'])

# ✅ Use SELECT only needed columns
result = await db.execute(
    select(Dispute.id, Dispute.status, Dispute.amount)
    .where(Dispute.user_id == user_id)
)

# ❌ Avoid N+1 queries - use eager loading
# Bad:
disputes = await db.execute(select(Dispute))
for dispute in disputes:
    evidence = await db.execute(
        select(EvidenceFile).where(EvidenceFile.dispute_id == dispute.id)
    )  # N+1 query

# Good:
disputes = await db.execute(
    select(Dispute)
    .options(selectinload(Dispute.evidence_files))
)
```

### Caching Strategy

```python
# ✅ Cache frequently accessed, rarely changing data
from aiocache import cached

@cached(ttl=3600, key="dispute:{dispute_id}")
async def get_dispute_cached(dispute_id: UUID) -> Dispute:
    return await db.get(Dispute, dispute_id)

# ✅ Invalidate cache on updates
async def update_dispute_status(dispute_id: UUID, new_status: str):
    # ... update logic ...
    await cache.delete(f"dispute:{dispute_id}")
```

### Async Best Practices

```python
# ✅ Use connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True  # Verify connections before use
)

# ✅ Batch operations
async def create_audit_logs(logs: list[AuditLog]):
    async with AsyncSession(engine) as session:
        session.add_all(logs)
        await session.commit()
```

---

## Agent Behavior Guidelines

### When Generating Code

1. **Security First:**
   - Always validate inputs before processing
   - Never log sensitive data (PAN, SSN, passwords)
   - Use parameterized queries (ORM) to prevent SQL injection
   - Implement RBAC for all endpoints

2. **Compliance Awareness:**
   - Include audit logging for all state changes
   - Support data export and erasure (GDPR)
   - Maintain immutable audit trails
   - Document data retention policies

3. **Error Handling:**
   - Return structured error responses with error codes
   - Log errors with correlation IDs
   - Never expose internal details (stack traces, DB schema) to clients
   - Implement proper HTTP status codes

4. **Type Safety:**
   - Always include type hints
   - Use Pydantic for validation and serialization
   - Run mypy in strict mode
   - Handle Optional types explicitly

5. **Testing:**
   - Generate unit tests for business logic
   - Include edge cases in test suite
   - Test security boundaries (auth, RBAC)
   - Use fixtures for test data

### When Answering Questions

1. **Be Specific:**
   - Provide code examples with context
   - Reference specific files/functions from the spec
   - Explain the "why" behind recommendations

2. **Consider Compliance:**
   - Highlight regulatory implications (PCI, GDPR)
   - Suggest audit trail enhancements
   - Recommend security best practices

3. **Performance Context:**
   - Explain trade-offs (e.g., caching vs. consistency)
   - Provide latency targets
   - Suggest optimization strategies

---

## Example: Complete Feature Implementation

**Task:** Add email notification when dispute status changes

### Agent Should Generate:

```python
# src/services/notification_service.py
from typing import Optional
from uuid import UUID
import logging
from email.mime.text import MIMEText
import aiosmtplib

logger = logging.getLogger(__name__)

class NotificationService:
    """Handles sending notifications for dispute events."""
    
    async def send_status_change_email(
        self,
        user_email: str,
        dispute_external_id: str,
        old_status: str,
        new_status: str
    ) -> bool:
        """
        Send email notification for dispute status change.
        
        Args:
            user_email: Recipient email (already validated)
            dispute_external_id: Human-readable dispute ID (e.g., DIS-20260522-A7F3)
            old_status: Previous status
            new_status: Current status
            
        Returns:
            True if email sent successfully, False otherwise
        
        Security:
            - Does not include sensitive dispute details in email body
            - Logs send attempts (success/failure) for audit trail
        """
        try:
            message = MIMEText(
                f"Your dispute {dispute_external_id} status has changed from "
                f"{old_status} to {new_status}. Please log in to view details."
            )
            message["Subject"] = f"Dispute Update: {dispute_external_id}"
            message["From"] = "noreply@example.com"
            message["To"] = user_email
            
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                use_tls=True
            )
            
            logger.info(
                "Status change email sent",
                extra={
                    "dispute_external_id": dispute_external_id,
                    "recipient": user_email,  # OK for audit logs
                    "status_transition": f"{old_status} -> {new_status}"
                }
            )
            return True
            
        except Exception as exc:
            logger.error(
                "Failed to send status change email",
                extra={
                    "dispute_external_id": dispute_external_id,
                    "error": str(exc)
                },
                exc_info=True
            )
            return False  # Don't fail the status update if email fails

# Update status endpoint to call notification
@router.patch("/disputes/{dispute_id}/status")
async def update_dispute_status(
    dispute_id: UUID,
    request: StatusUpdateRequest,
    user: User = Depends(require_role("OPS_ANALYST")),
    db: AsyncSession = Depends(get_db),
    notification_service: NotificationService = Depends(get_notification_service)
):
    dispute = await dispute_service.update_status(
        dispute_id, request.new_status, user.id, request.notes, db
    )
    
    # Send notification asynchronously (fire-and-forget)
    asyncio.create_task(
        notification_service.send_status_change_email(
            user_email=dispute.user.email,
            dispute_external_id=dispute.external_id,
            old_status=request.old_status,
            new_status=request.new_status
        )
    )
    
    return DisputeResponse.from_orm(dispute)

# tests/unit/test_notification_service.py
import pytest
from unittest.mock import AsyncMock, patch

async def test_send_email_success(notification_service):
    with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        result = await notification_service.send_status_change_email(
            user_email="user@example.com",
            dispute_external_id="DIS-20260522-A7F3",
            old_status="SUBMITTED",
            new_status="UNDER_REVIEW"
        )
        assert result is True
        mock_send.assert_called_once()

async def test_send_email_failure_does_not_crash(notification_service):
    with patch('aiosmtplib.send', side_effect=Exception("SMTP error")):
        result = await notification_service.send_status_change_email(
            user_email="user@example.com",
            dispute_external_id="DIS-20260522-A7F3",
            old_status="SUBMITTED",
            new_status="UNDER_REVIEW"
        )
        assert result is False  # Graceful degradation
```

### Key Points Agent Demonstrated:

✅ Type hints on all functions  
✅ Async/await for I/O operations  
✅ Comprehensive docstrings with security notes  
✅ Proper error handling and logging  
✅ No sensitive data in email body  
✅ Fire-and-forget pattern (don't block main flow)  
✅ Unit tests with mocking  
✅ Graceful degradation on failure

---

## Quick Reference Checklist

Before submitting generated code, agents should verify:

- [ ] All functions have type hints
- [ ] No `float` used for monetary values (use `Decimal`)
- [ ] No sensitive data (PAN, passwords) in logs
- [ ] Input validation with Pydantic
- [ ] SQL queries use ORM (no raw SQL strings)
- [ ] Errors return structured JSON with error codes
- [ ] RBAC enforced on protected endpoints
- [ ] Tests cover happy path + edge cases
- [ ] Async operations use `async`/`await`
- [ ] Audit log entries created for state changes
- [ ] Documentation includes security considerations
- [ ] mypy passes in strict mode
- [ ] Bandit security scan shows no high-severity issues

---

**End of Agent Configuration**


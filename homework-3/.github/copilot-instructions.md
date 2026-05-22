# GitHub Copilot Instructions - Transaction Dispute System

## Project Context

This is a **financial transaction dispute system** requiring strict adherence to:
- **PCI DSS** (Payment Card Industry Data Security Standard)
- **SOC 2** compliance
- **GDPR/CCPA** privacy regulations
- **Banking-grade security** and audit trails

**Technology Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, AWS S3, Redis

---

## Critical Rules - NEVER Violate

### 🚨 Security & Compliance

1. **NEVER log or display full PAN (Primary Account Number)**
   - Always mask to last 4 digits: `****1234`
   - Use tokenization; store only token references

2. **NEVER use `float` for monetary values**
   - ✅ ALWAYS use `decimal.Decimal`
   - ✅ Database: `NUMERIC(15,2)` or higher precision
   - ❌ FORBIDDEN: `amount = 100.50` (float)

3. **NEVER expose stack traces or internal errors to API clients**
   - Return generic 500 errors with correlation IDs
   - Log detailed errors internally only

4. **NEVER hardcode secrets**
   - Use environment variables or AWS Secrets Manager
   - No API keys, passwords, or tokens in code

5. **NEVER skip input validation**
   - Use Pydantic models for all request/response data
   - Validate enums, ranges, formats before processing

---

## Code Generation Defaults

### Type Hints (Mandatory)

```python
# ✅ Always include type hints
async def create_dispute(
    user_id: UUID,
    amount: Decimal,
    reason: DisputeReason,
    db: AsyncSession
) -> Dispute:
    ...

# ❌ Never generate untyped code
def process(data):  # INCORRECT
    ...
```

### Async/Await Patterns

```python
# ✅ Use async for I/O operations
async def get_dispute(dispute_id: UUID, db: AsyncSession) -> Dispute:
    result = await db.execute(select(Dispute).where(Dispute.id == dispute_id))
    return result.scalar_one_or_none()

# ❌ Don't use blocking calls in async functions
response = requests.get(url)  # WRONG - blocks event loop
```

### Error Handling

```python
# ✅ Structured error responses
raise HTTPException(
    status_code=400,
    detail={
        "error_code": "VALIDATION_ERROR",
        "message": "Invalid dispute amount",
        "field": "amount"
    }
)

# ❌ Don't expose internals
raise Exception(f"DB error: {traceback.format_exc()}")  # WRONG
```

### Logging

```python
# ✅ Safe logging (no PII/PAN)
logger.info(
    "Dispute created",
    extra={
        "dispute_id": str(dispute.id),
        "user_id": str(user_id),
        "amount": str(amount)
    }
)

# ❌ Dangerous logging
logger.info(f"Created dispute for card {full_pan}")  # FORBIDDEN
```

---

## Naming Conventions

- **Files:** `snake_case.py` (e.g., `dispute_service.py`)
- **Classes:** `PascalCase` (e.g., `DisputeService`, `EvidenceFile`)
- **Functions/Variables:** `snake_case` (e.g., `create_dispute`, `user_id`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_EVIDENCE_FILES`, `DISPUTE_WINDOW_DAYS`)
- **Private:** Leading underscore (e.g., `_validate_internal()`)

---

## Pydantic Patterns

```python
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from enum import Enum

class DisputeReason(str, Enum):
    FRAUDULENT = "FRAUDULENT"
    DUPLICATE_CHARGE = "DUPLICATE_CHARGE"
    PRODUCT_NOT_RECEIVED = "PRODUCT_NOT_RECEIVED"

class DisputeCreateRequest(BaseModel):
    transaction_id: UUID
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    reason: DisputeReason
    narrative: str = Field(min_length=10, max_length=2000)
    
    @field_validator('narrative')
    def sanitize_narrative(cls, v):
        import bleach
        return bleach.clean(v, tags=[], strip=True)
    
    model_config = ConfigDict(from_attributes=True)
```

---

## Database Patterns

### SQLAlchemy Models

```python
from sqlalchemy import Column, String, NUMERIC, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class Dispute(Base):
    __tablename__ = "disputes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(NUMERIC(15, 2), nullable=False)  # NEVER use Float
    status = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking
    
    # Indexes for query performance
    __table_args__ = (
        Index('idx_disputes_user_status', 'user_id', 'status'),
        Index('idx_disputes_created', 'created_at'),
    )
```

### Async Queries

```python
# ✅ Correct async query
async def get_user_disputes(user_id: UUID, db: AsyncSession):
    result = await db.execute(
        select(Dispute)
        .where(Dispute.user_id == user_id)
        .options(selectinload(Dispute.evidence_files))  # Eager load
    )
    return result.scalars().all()

# ✅ Transaction with rollback
async def create_dispute_with_audit(request: DisputeCreateRequest, db: AsyncSession):
    async with db.begin():
        try:
            dispute = Dispute(**request.model_dump())
            db.add(dispute)
            await db.flush()  # Get dispute.id before commit
            
            audit_log = AuditLog(dispute_id=dispute.id, action="CREATED")
            db.add(audit_log)
            
            await db.commit()
            return dispute
        except Exception:
            await db.rollback()
            raise
```

---

## Security Checklist for Generated Code

When generating endpoints, services, or utilities, ensure:

- [ ] **Authentication:** JWT validation via `Depends(get_current_user)`
- [ ] **Authorization:** RBAC check with `require_role("ROLE_NAME")`
- [ ] **Input Validation:** Pydantic model with constraints
- [ ] **SQL Injection Prevention:** Use ORM, no raw SQL strings
- [ ] **XSS Prevention:** Sanitize user inputs (bleach, HTML escaping)
- [ ] **Rate Limiting:** Apply `@limiter.limit("10/hour")` for sensitive endpoints
- [ ] **Audit Logging:** Call `audit_service.log_event()` for state changes
- [ ] **Idempotency:** Accept `Idempotency-Key` header for POST/PATCH
- [ ] **Error Handling:** Return structured errors, log with correlation ID
- [ ] **No Secrets:** Use `settings.SECRET_NAME`, not hardcoded values

---

## Testing Patterns

### Unit Test

```python
import pytest
from decimal import Decimal
from uuid import uuid4

@pytest.mark.asyncio
async def test_create_dispute_success(db_session, sample_user, sample_transaction):
    service = DisputeService()
    
    dispute = await service.create_dispute(
        user_id=sample_user.id,
        transaction_id=sample_transaction.id,
        amount=Decimal("100.00"),
        reason=DisputeReason.FRAUDULENT,
        narrative="Unauthorized charge on my card",
        db_session=db_session
    )
    
    assert dispute.id is not None
    assert dispute.status == DisputeStatus.SUBMITTED
    assert dispute.amount == Decimal("100.00")

@pytest.mark.asyncio
async def test_create_dispute_invalid_amount(db_session, sample_user, sample_transaction):
    service = DisputeService()
    
    with pytest.raises(ValueError, match="amount must be positive"):
        await service.create_dispute(
            user_id=sample_user.id,
            transaction_id=sample_transaction.id,
            amount=Decimal("-50.00"),  # Negative amount
            reason=DisputeReason.FRAUDULENT,
            narrative="Test",
            db_session=db_session
        )
```

### Integration Test

```python
@pytest.mark.asyncio
async def test_dispute_creation_endpoint(client, user_token):
    response = await client.post(
        "/api/v1/disputes",
        json={
            "transaction_id": str(uuid4()),
            "amount": "125.50",
            "reason": "FRAUDULENT",
            "narrative": "This is a test dispute"
        },
        headers={
            "Authorization": f"Bearer {user_token}",
            "Idempotency-Key": str(uuid4())
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "SUBMITTED"
    assert data["amount"] == "125.50"
```

---

## Common FastAPI Endpoint Pattern

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["disputes"])

@router.post("/disputes", status_code=201, response_model=DisputeResponse)
async def create_dispute(
    request: DisputeCreateRequest,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    dispute_service: DisputeService = Depends(get_dispute_service),
    audit_service: AuditService = Depends(get_audit_service)
) -> DisputeResponse:
    """
    Create a new transaction dispute.
    
    Requires:
        - Valid JWT token (END_USER role or higher)
        - Idempotency-Key header (UUID)
    
    Returns:
        201: Dispute created successfully
        400: Invalid request data
        401: Unauthorized
        422: Business logic validation failed
        429: Rate limit exceeded
    """
    try:
        # Check idempotency
        cached = await check_idempotency(idempotency_key, request)
        if cached:
            return cached
        
        # Create dispute
        dispute = await dispute_service.create_dispute(
            user_id=current_user.id,
            request=request,
            db_session=db
        )
        
        # Audit log
        await audit_service.log_event(
            action="DISPUTE_CREATED",
            user_id=current_user.id,
            dispute_id=dispute.id,
            old_value=None,
            new_value=dispute.to_dict(),
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            request_id=request.state.request_id,
            db_session=db
        )
        
        # Cache response for idempotency
        await cache_response(idempotency_key, dispute)
        
        return DisputeResponse.from_orm(dispute)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DisputeWindowExpiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

---

## Financial Data Rules

### Money Calculations

```python
from decimal import Decimal, ROUND_HALF_UP

# ✅ Correct monetary calculations
total = Decimal("100.50") + Decimal("25.25")  # 125.75
fee = (total * Decimal("0.029")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# ✅ API serialization
class MoneyField(BaseModel):
    amount: Decimal
    currency: str = "USD"
    
    def to_api_dict(self):
        return {
            "amount": str(self.amount),  # String to preserve precision
            "currency": self.currency
        }

# ❌ FORBIDDEN
total = 100.50 + 25.25  # Float arithmetic - DO NOT USE
```

### Currency Handling

```python
# ✅ Always include currency code
class Transaction(Base):
    amount = Column(NUMERIC(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_positive'),
        CheckConstraint("currency IN ('USD', 'EUR', 'GBP')", name='valid_currency'),
    )
```

---

## Audit Logging Pattern

```python
# ✅ Always log state changes
async def update_dispute_status(
    dispute_id: UUID,
    new_status: DisputeStatus,
    actor_id: UUID,
    db: AsyncSession
):
    # Get old state
    dispute = await db.get(Dispute, dispute_id)
    old_status = dispute.status
    
    # Update
    dispute.status = new_status
    dispute.updated_at = datetime.utcnow()
    
    # Audit log
    await audit_service.log_event(
        action="STATUS_UPDATED",
        user_id=actor_id,
        dispute_id=dispute_id,
        old_value={"status": old_status},
        new_value={"status": new_status},
        # ... other metadata
    )
    
    await db.commit()
    return dispute
```

---

## File Upload Security

```python
import magic
from pathlib import Path

# ✅ Validate file type by magic bytes, not extension
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_file(file: UploadFile) -> bool:
    # Check size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes")
    
    # Check magic bytes
    file_bytes = await file.read(2048)
    mime_type = magic.from_buffer(file_bytes, mime=True)
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Invalid file type: {mime_type}")
    
    file.file.seek(0)  # Reset for upload
    return True

# ✅ Sanitize filename
def sanitize_filename(filename: str) -> str:
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    return safe_name[:100]  # Limit length
```

---

## Performance Optimization Hints

```python
# ✅ Use connection pooling
engine = create_async_engine(
    settings.database_url,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)

# ✅ Batch inserts
async def bulk_create_audit_logs(logs: list[AuditLog], db: AsyncSession):
    db.add_all(logs)
    await db.commit()

# ✅ Use pagination
@router.get("/disputes")
async def list_disputes(
    limit: int = Query(default=20, le=100),
    cursor: Optional[str] = None
):
    # Cursor-based pagination for large datasets
    ...

# ✅ Cache expensive queries
from aiocache import cached

@cached(ttl=300, key="dispute_stats:{user_id}")
async def get_user_dispute_stats(user_id: UUID):
    ...
```

---

## When You Generate Code

1. **Start with type hints and Pydantic models**
2. **Add input validation before business logic**
3. **Use async/await for all I/O operations**
4. **Include error handling with structured responses**
5. **Add audit logging for state changes**
6. **Write docstrings with security notes**
7. **Generate corresponding unit tests**
8. **Never skip security checks (auth, validation, sanitization)**

---

## What to Avoid in Suggestions

❌ Using `float` for money  
❌ Logging full PAN, SSN, passwords  
❌ Raw SQL queries with string interpolation  
❌ Hardcoded secrets or API keys  
❌ Exposing stack traces in API responses  
❌ Unvalidated user inputs  
❌ Blocking calls in async functions  
❌ Missing type hints  
❌ Generic `Exception` catches without logging  
❌ Direct file path manipulation (use Path library)

---

## Quick Reference

| When generating... | Must include... |
|--------------------|-----------------|
| **API Endpoint** | Auth, RBAC, validation, error handling, audit log |
| **Service Method** | Type hints, async, transaction handling, error handling |
| **Database Model** | Indexes, constraints, proper column types (NUMERIC for money) |
| **Pydantic Schema** | Validators, sanitizers, proper types (Decimal for money) |
| **Test** | Happy path + edge cases + security boundaries |
| **File Upload** | Magic byte validation, size limit, virus scan hook |
| **Query** | Pagination, indexes, eager loading (avoid N+1) |

---

**Remember:** This is a financial system. Security, compliance, and data integrity are non-negotiable. When in doubt, favor explicit validation and audit trails over convenience.


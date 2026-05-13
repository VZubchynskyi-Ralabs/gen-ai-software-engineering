# 🧪 API Test Log — Banking Transactions API

> **Date Tested**: May 9, 2026  
> **Server**: `http://localhost:3000`  
> **Node.js version**: v18+

All endpoints were tested via `curl` with the server running locally (`npm start`).

---

## Task 1 – Core API

### POST /transactions (deposit)

**Request:**
```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":500.00,"currency":"USD","type":"deposit"}'
```

**Response (201 Created):**
```json
{
    "id": "ce2cd1fc-738d-4bde-b79e-0764afdb26ae",
    "fromAccount": null,
    "toAccount": "ACC-12345",
    "amount": 500,
    "currency": "USD",
    "type": "deposit",
    "timestamp": "2026-05-09T07:23:52.653Z",
    "status": "completed"
}
```

---

### POST /transactions (withdrawal)

**Request:**
```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","amount":100.50,"currency":"USD","type":"withdrawal"}'
```

**Response (201 Created):**
```json
{
    "id": "530a366c-8618-4525-8004-2dd20501da6b",
    "fromAccount": "ACC-12345",
    "toAccount": null,
    "amount": 100.5,
    "currency": "USD",
    "type": "withdrawal",
    "timestamp": "2026-05-09T07:23:52.724Z",
    "status": "completed"
}
```

---

### POST /transactions (transfer)

**Request:**
```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":200.00,"currency":"EUR","type":"transfer"}'
```

**Response (201 Created):**
```json
{
    "id": "2658c4b5-12d8-4545-8dce-1a42b85633c4",
    "fromAccount": "ACC-12345",
    "toAccount": "ACC-67890",
    "amount": 200,
    "currency": "EUR",
    "type": "transfer",
    "timestamp": "2026-05-09T07:23:52.766Z",
    "status": "completed"
}
```

---

### GET /transactions (list all)

**Request:**
```bash
curl http://localhost:3000/transactions
```

**Response (200 OK):**
```json
[
    {
        "id": "ce2cd1fc-738d-4bde-b79e-0764afdb26ae",
        "fromAccount": null,
        "toAccount": "ACC-12345",
        "amount": 500,
        "currency": "USD",
        "type": "deposit",
        "timestamp": "2026-05-09T07:23:52.653Z",
        "status": "completed"
    },
    {
        "id": "530a366c-8618-4525-8004-2dd20501da6b",
        "fromAccount": "ACC-12345",
        "toAccount": null,
        "amount": 100.5,
        "currency": "USD",
        "type": "withdrawal",
        "timestamp": "2026-05-09T07:23:52.724Z",
        "status": "completed"
    },
    {
        "id": "2658c4b5-12d8-4545-8dce-1a42b85633c4",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 200,
        "currency": "EUR",
        "type": "transfer",
        "timestamp": "2026-05-09T07:23:52.766Z",
        "status": "completed"
    }
]
```

---

### GET /accounts/:accountId/balance

**Request:**
```bash
curl http://localhost:3000/accounts/ACC-12345/balance
```

**Response (200 OK):**
```json
{
    "accountId": "ACC-12345",
    "balance": {
        "USD": 399.5,
        "EUR": -200
    }
}
```

---

## Task 2 – Validation

### Invalid amount (negative number)

**Request:**
```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":-50,"currency":"USD","type":"deposit"}'
```

**Response (400 Bad Request):**
```json
{
    "error": "Validation failed",
    "details": [
        {
            "field": "amount",
            "message": "Amount must be a positive number"
        }
    ]
}
```

---

### Invalid currency code

**Request:**
```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":100,"currency":"XYZ","type":"deposit"}'
```

**Response (400 Bad Request):**
```json
{
    "error": "Validation failed",
    "details": [
        {
            "field": "currency",
            "message": "Invalid currency code. Must be a valid ISO 4217 code"
        }
    ]
}
```

---

### Transaction not found

**Request:**
```bash
curl http://localhost:3000/transactions/nonexistent-id
```

**Response (404 Not Found):**
```json
{
    "error": "Transaction not found"
}
```

---

## Task 3 – Transaction Filtering

### Filter by accountId

**Request:**
```bash
curl "http://localhost:3000/transactions?accountId=ACC-12345"
```

**Response (200 OK):** Returns all 3 transactions (ACC-12345 appears in all of them)

---

### Filter by type

**Request:**
```bash
curl "http://localhost:3000/transactions?type=transfer"
```

**Response (200 OK):**
```json
[
    {
        "id": "2658c4b5-12d8-4545-8dce-1a42b85633c4",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 200,
        "currency": "EUR",
        "type": "transfer",
        "timestamp": "2026-05-09T07:23:52.766Z",
        "status": "completed"
    }
]
```

---

## Task 4 – Account Summary (Option A)

### GET /accounts/:accountId/summary

**Request:**
```bash
curl http://localhost:3000/accounts/ACC-12345/summary
```

**Response (200 OK):**
```json
{
    "accountId": "ACC-12345",
    "transactionCount": 3,
    "totalDeposits": 500,
    "totalWithdrawals": 300.5,
    "lastTransactionDate": "2026-05-09T07:23:52.766Z"
}
```

---

✅ **All endpoints verified and working correctly.**


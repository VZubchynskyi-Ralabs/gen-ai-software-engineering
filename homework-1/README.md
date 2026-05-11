# 🏦 Homework 1: Banking Transactions API

**Student Name:** Volodymyr Zubchynskyi  
**Date Submitted:** May 9, 2026  
**AI Tools Used:** GitHub Copilot

---

## 📋 Project Overview

A minimal REST API for banking transactions built with **Node.js** and **Express**. It supports creating, listing, and filtering transactions, calculating account balances, and generating account summaries. All data is stored in-memory — no database required.

---

## ✅ Features Implemented

| Task | Feature | Status |
|------|---------|--------|
| Task 1 | Core API (CRUD endpoints + balance) | ✅ Done |
| Task 2 | Transaction validation | ✅ Done |
| Task 3 | Transaction history filtering | ✅ Done |
| Task 4 | Account summary endpoint (Option A) | ✅ Done |

---

## 🏗️ Architecture

```
src/
├── index.js                      # App entry point, Express setup
├── routes/
│   ├── transactions.js           # POST /transactions, GET /transactions, GET /transactions/:id
│   └── accounts.js               # GET /accounts/:accountId/balance, GET /accounts/:accountId/summary
├── models/
│   └── transaction.js            # createTransaction() factory — builds & freezes a transaction object
├── validators/
│   └── transactionValidator.js   # validateTransaction() — field-level rules, returns { valid, errors }
└── utils/
    └── helpers.js                # In-memory store, filterTransactions(), calculateBalance(), calculateSummary()
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Dynamic balance calculation | Balance is computed on-the-fly from transaction history, not stored separately — avoids sync issues |
| Multi-currency balance | Balance endpoint returns a per-currency map (e.g. `{ "USD": 450.00, "EUR": -200.00 }`) |
| Immutable transactions | `Object.freeze()` applied after creation to prevent accidental mutation |
| No external DB | Shared in-memory array for zero-dependency simplicity |
| UUIDs via `crypto.randomUUID()` | Built-in Node.js module, no extra dependency needed |

---

## 📝 Implementation Details

### Task 1 – Core API

**Endpoints:**

| Method | Endpoint | Status Code | Description |
|--------|----------|-------------|-------------|
| `POST` | `/transactions` | `201 Created` | Create a new transaction |
| `GET` | `/transactions` | `200 OK` | List all transactions |
| `GET` | `/transactions/:id` | `200 OK` / `404 Not Found` | Get a specific transaction by ID |
| `GET` | `/accounts/:accountId/balance` | `200 OK` | Get per-currency balance for an account |

**Transaction Model** (`src/models/transaction.js`):
```json
{
  "id": "auto-generated UUID (crypto.randomUUID)",
  "fromAccount": "string | null",
  "toAccount": "string | null",
  "amount": "number (parsed float)",
  "currency": "string (uppercased ISO 4217)",
  "type": "deposit | withdrawal | transfer",
  "timestamp": "ISO 8601 (new Date().toISOString())",
  "status": "completed"
}
```

**Balance calculation** (`src/utils/helpers.js` → `calculateBalance`):
- Iterates all `completed` transactions for the given `accountId`
- Adds `amount` when `toAccount === accountId` (credit)
- Subtracts `amount` when `fromAccount === accountId` (debit)
- Groups result by `currency`, rounded to 2 decimal places

---

### Task 2 – Transaction Validation

Implemented in `src/validators/transactionValidator.js`. Returns `{ valid: boolean, errors: [{field, message}] }`.

| Field | Rule |
|-------|------|
| `type` | Must be one of `deposit`, `withdrawal`, `transfer` |
| `amount` | Required, positive number, ≤ 2 decimal places |
| `currency` | Required, must exist in a 30-entry ISO 4217 `Set` |
| `fromAccount` | Required for `withdrawal`/`transfer`; must match `ACC-XXXXX` regex |
| `toAccount` | Required for `deposit`/`transfer`; must match `ACC-XXXXX` regex |

Account format regex: `/^ACC-[A-Z0-9]{5}$/i`

Error response shape:
```json
{
  "error": "Validation failed",
  "details": [
    { "field": "amount", "message": "Amount must be a positive number" }
  ]
}
```

---

### Task 3 – Transaction History Filtering

Implemented in `filterTransactions()` (`src/utils/helpers.js`). Accepts optional query params on `GET /transactions`:

| Query Param | Behaviour |
|-------------|-----------|
| `?accountId=ACC-XXXXX` | Matches `fromAccount` **or** `toAccount` |
| `?type=transfer` | Exact match on `type` |
| `?from=YYYY-MM-DD` | Includes transactions with `timestamp >= from` |
| `?to=YYYY-MM-DD` | Includes the full end-day (`to` date extended to `T23:59:59.999Z`) |

All filters can be combined.

---

### Task 4 – Account Summary (Option A)

**Endpoint:** `GET /accounts/:accountId/summary`

Implemented in `calculateSummary()` (`src/utils/helpers.js`):
- Finds all transactions where `fromAccount` or `toAccount` matches
- Sums **deposits**: `toAccount === accountId` and `type` is `deposit` or `transfer` (incoming)
- Sums **withdrawals**: `fromAccount === accountId` and `type` is `withdrawal` or `transfer` (outgoing)
- Tracks `lastTransactionDate` as the latest `timestamp`

Response shape:
```json
{
  "accountId": "ACC-12345",
  "transactionCount": 3,
  "totalDeposits": 500.00,
  "totalWithdrawals": 300.50,
  "lastTransactionDate": "2026-05-09T07:23:52.766Z"
}
```

---

## 🧪 Test Results

All endpoints tested via `curl` against a locally running server (`npm start`). Full request/response log: [`docs/API_TEST_LOG.md`](docs/API_TEST_LOG.md).

### Task 1 – Core API

<details>
<summary>POST /transactions — deposit</summary>

```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":500.00,"currency":"USD","type":"deposit"}'
```
```json
// 201 Created
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
</details>

<details>
<summary>POST /transactions — withdrawal</summary>

```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","amount":100.50,"currency":"USD","type":"withdrawal"}'
```
```json
// 201 Created
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
</details>

<details>
<summary>POST /transactions — transfer</summary>

```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":200.00,"currency":"EUR","type":"transfer"}'
```
```json
// 201 Created
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
</details>

<details>
<summary>GET /transactions — list all</summary>

```bash
curl http://localhost:3000/transactions
```
```json
// 200 OK — returns array of all 3 transactions
[
  { "id": "ce2cd1fc...", "type": "deposit",    "amount": 500,   "currency": "USD" },
  { "id": "530a366c...", "type": "withdrawal", "amount": 100.5, "currency": "USD" },
  { "id": "2658c4b5...", "type": "transfer",   "amount": 200,   "currency": "EUR" }
]
```
</details>

<details>
<summary>GET /accounts/:accountId/balance</summary>

```bash
curl http://localhost:3000/accounts/ACC-12345/balance
```
```json
// 200 OK
{
  "accountId": "ACC-12345",
  "balance": { "USD": 399.5, "EUR": -200 }
}
```
*(USD: +500 deposit − 100.50 withdrawal = 399.50 | EUR: −200 transfer outgoing)*
</details>

---

### Task 2 – Validation

<details>
<summary>Negative amount → 400</summary>

```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":-50,"currency":"USD","type":"deposit"}'
```
```json
// 400 Bad Request
{
  "error": "Validation failed",
  "details": [{ "field": "amount", "message": "Amount must be a positive number" }]
}
```
</details>

<details>
<summary>Invalid currency code → 400</summary>

```bash
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":100,"currency":"XYZ","type":"deposit"}'
```
```json
// 400 Bad Request
{
  "error": "Validation failed",
  "details": [{ "field": "currency", "message": "Invalid currency code. Must be a valid ISO 4217 code" }]
}
```
</details>

<details>
<summary>Transaction not found → 404</summary>

```bash
curl http://localhost:3000/transactions/nonexistent-id
```
```json
// 404 Not Found
{ "error": "Transaction not found" }
```
</details>

---

### Task 3 – Filtering

<details>
<summary>Filter by accountId</summary>

```bash
curl "http://localhost:3000/transactions?accountId=ACC-12345"
```
✅ Returns all 3 transactions (ACC-12345 appears in each as `fromAccount` or `toAccount`)
</details>

<details>
<summary>Filter by type</summary>

```bash
curl "http://localhost:3000/transactions?type=transfer"
```
```json
// 200 OK — returns only the EUR transfer
[{ "id": "2658c4b5...", "type": "transfer", "amount": 200, "currency": "EUR" }]
```
</details>

---

### Task 4 – Account Summary

```bash
curl http://localhost:3000/accounts/ACC-12345/summary
```
```json
// 200 OK
{
  "accountId": "ACC-12345",
  "transactionCount": 3,
  "totalDeposits": 500,
  "totalWithdrawals": 300.5,
  "lastTransactionDate": "2026-05-09T07:23:52.766Z"
}
```

✅ **All endpoints verified and working correctly.**

---

## 🚀 Quick Start

```bash
npm install
npm start
```

API runs at `http://localhost:3000`

See [`HOWTORUN.md`](HOWTORUN.md) for detailed setup instructions and sample requests.

---

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>

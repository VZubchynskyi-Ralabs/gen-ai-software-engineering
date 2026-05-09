## 🏦 Homework 1: Banking Transactions API
**Student Name:** Volodymyr Zubchynskyi **Date Submitted:** May 9, 2026 **AI Tools Used:** GitHub Copilot

## 📋 Project Overview

A minimal REST API for banking transactions built with **Node.js** and **Express**. It supports creating, listing, and filtering transactions, calculating account balances, and generating account summaries. All data is stored in-memory — no database required.

---

## ✅ Features Implemented

### Task 1 – Core API
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/transactions` | Create a new transaction |
| `GET` | `/transactions` | List all transactions |
| `GET` | `/transactions/:id` | Get a specific transaction by ID |
| `GET` | `/accounts/:accountId/balance` | Get account balance (per currency) |

### Task 2 – Transaction Validation
- Amount must be a positive number with at most 2 decimal places
- Account numbers must follow format `ACC-XXXXX` (alphanumeric)
- Currency must be a valid ISO 4217 code (30+ supported)
- Meaningful error responses with field-level details

### Task 3 – Transaction History Filtering
- Filter by account: `?accountId=ACC-12345`
- Filter by type: `?type=transfer`
- Filter by date range: `?from=2026-01-01&to=2026-12-31`
- Combine multiple filters

### Task 4 – Account Summary (Option A)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/accounts/:accountId/summary` | Returns deposits total, withdrawals total, transaction count, and last transaction date |

---

## 🏗️ Architecture

```
src/
├── index.js                      # App entry point, Express setup
├── routes/
│   ├── transactions.js           # Transaction route handlers
│   └── accounts.js               # Account route handlers
├── models/
│   └── transaction.js            # Transaction factory function
├── validators/
│   └── transactionValidator.js   # Input validation logic
└── utils/
    └── helpers.js                # In-memory store, filtering, balance/summary calc
```

### Key Design Decisions
- **Dynamic balance calculation**: Balance is computed on-the-fly from transaction history, not stored separately
- **Multi-currency balance**: Balance endpoint returns a per-currency breakdown (e.g., `{ "USD": 450.00, "EUR": 200.00 }`)
- **Immutable transactions**: Transaction objects are frozen after creation
- **No external DB**: Uses a shared in-memory array for simplicity

---

## 🚀 Quick Start

```bash
npm install
npm start
```

API runs at `http://localhost:3000`

---

<div align="center">

*This project was completed as part of the AI-Assisted Development course.*

</div>

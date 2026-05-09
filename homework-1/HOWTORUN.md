# ▶️ How to Run the Application

## Prerequisites

- [Node.js](https://nodejs.org/) v18 or later
- npm (comes with Node.js)

---

## 1. Install Dependencies

```bash
cd homework-1
npm install
```

## 2. Start the Server

```bash
npm start
```

Or with auto-reload during development:

```bash
npm run dev
```

The API will be available at `http://localhost:3000`.

---

## 3. Running via Demo Script

```bash
chmod +x demo/run.sh
./demo/run.sh
```

---

## 4. Test the API

### Using curl

```bash
# Create a deposit
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":500.00,"currency":"USD","type":"deposit"}'

# Create a transfer
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":200.00,"currency":"USD","type":"transfer"}'

# List all transactions
curl http://localhost:3000/transactions

# Filter by account
curl "http://localhost:3000/transactions?accountId=ACC-12345"

# Filter by type
curl "http://localhost:3000/transactions?type=transfer"

# Filter by date range
curl "http://localhost:3000/transactions?from=2026-01-01&to=2026-12-31"

# Get account balance
curl http://localhost:3000/accounts/ACC-12345/balance

# Get account summary
curl http://localhost:3000/accounts/ACC-12345/summary
```

### Using VS Code REST Client

Open `demo/sample-requests.http` and click **Send Request** next to any request.

---

## 5. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Port the server listens on |

To use a custom port:
```bash
PORT=8080 npm start
```

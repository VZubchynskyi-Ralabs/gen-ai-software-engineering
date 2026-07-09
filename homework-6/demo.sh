#!/usr/bin/env bash
# Zero-manual-steps demo of the multi-agent banking pipeline:
# starts the REST API gateway, submits every sample transaction through it,
# and prints the per-transaction results plus the run summary.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

PORT="${PORT:-8000}"
HOST="127.0.0.1"
BASE_URL="http://${HOST}:${PORT}"
PYTHON=".venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "No virtual environment found — setting one up..."
  python3 -m venv .venv
  .venv/bin/pip install --quiet -r requirements.txt
fi

echo "Resetting shared/ for a clean demo run..."
rm -rf shared/input shared/processing shared/output shared/results
mkdir -p shared/input shared/processing shared/output shared/results

SERVER_LOG="shared/results/api_server.log"
echo "Starting the REST API gateway on ${BASE_URL} (server log: ${SERVER_LOG}) ..."
"$PYTHON" -m uvicorn api.server:app --host "$HOST" --port "$PORT" --log-level warning \
  >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

printf "Waiting for the API to become healthy"
ready=0
for _ in $(seq 1 30); do
  if curl -sf "${BASE_URL}/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  printf "."
  sleep 0.5
done
echo

if [ "$ready" -ne 1 ]; then
  echo "API never became healthy; aborting." >&2
  exit 1
fi

echo "=== Submitting sample-transactions.json via POST ${BASE_URL}/transactions ==="
"$PYTHON" - "$BASE_URL" <<'PY'
import json
import sys
import urllib.request

base_url = sys.argv[1]
with open("sample-transactions.json", encoding="utf-8") as fh:
    transactions = json.load(fh)

for txn in transactions:
    body = json.dumps(txn).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/transactions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.load(resp)
    data = result["data"]
    status = data.get("final_status") or data.get("status")
    reason = data.get("reason") or data.get("rejection_reason") or data.get("policy_reason") or ""
    suffix = f" ({reason})" if reason else ""
    print(f"  {data.get('transaction_id')}: {status}{suffix}")
PY

echo
echo "=== Pipeline summary: GET ${BASE_URL}/summary ==="
curl -s "${BASE_URL}/summary" | "$PYTHON" -m json.tool

echo
echo "Demo complete. Full results are on disk under shared/results/."
echo "Browser console is served at ${BASE_URL}/ - submit transactions, edit"
echo "policy rules, and watch the ledger update live."

if [ "${KEEP_RUNNING:-0}" = "1" ]; then
  echo "KEEP_RUNNING=1: leaving the server up. Press Ctrl+C to stop."
  wait "$SERVER_PID"
fi

# How to Run — Multi-Agent Banking Pipeline

## 1. Prerequisites

- Python 3.11+
- Node.js + `npx` (only needed if you want to exercise the `context7` MCP
  server yourself; the pipeline itself has no Node dependency)

## 2. Set up the environment

```bash
cd homework-6
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 3. Run the pipeline

```bash
.venv/bin/python integrator.py --clear
```

- `--clear` wipes `shared/{input,processing,output,results}/` first so the
  run reflects only this invocation.
- Output: a per-transaction line as each agent processes it, then a
  `=== Pipeline Summary ===` block.
- Check the results:
  ```bash
  ls shared/results/
  cat shared/results/pipeline_summary.json
  cat shared/results/pipeline_run.log
  ```
- Expect: 8 result files (`TXN001.json` … `TXN008.json`), plus
  `pipeline_summary.json` and `pipeline_run.log`. With the bundled
  `sample-transactions.json`, the expected split is
  **3 approved / 3 flagged_for_review / 2 rejected** (`TXN005`'s reason now
  includes `policy_rule_flagged` too, from the rule engine — see step 4a).

Or, from inside Claude Code, run the `/run-pipeline` skill instead of the
raw command — it does the same thing and reports the summary for you.

## 4. Validate transactions without running the full pipeline

```bash
.venv/bin/python agents/transaction_validator.py --dry-run
```

Or use the `/validate-transactions` skill in Claude Code.

## 4a. Evaluate the configurable rule engine on its own

```bash
.venv/bin/python agents/rule_engine.py --dry-run
```

Rules live in `agents/rules_config.json` — a declarative list of
`{field, operator, value, action, reason}` entries (plus an optional
`min_amount`). Add or edit a rule there to change behavior; no code
changes needed. Point at an alternate rule set with `--rules path/to.json`.
The bundled rules: reject any transaction touching a sanctioned country
(`KP`, `IR`, `SY`, `CU`), and flag large cash withdrawals (> $5,000) or
large branch wire transfers (> $50,000) for manual review.

## 5. Run the tests (with coverage)

```bash
.venv/bin/python -m pytest
```

`pytest.ini` already wires up `--cov=agents --cov=integrator --cov=mcp
--cov=api --cov-report=term-missing --cov-fail-under=80`, so a plain
`pytest` run both runs the suite and enforces the 80% gate. Current
coverage on this codebase is ~98%.

## 6. Try the coverage-gate hook

The hook lives at `.claude/hooks/check-coverage-before-push.sh` and is wired
into `.claude/settings.json` as a `PreToolUse` hook on the `Bash` tool. It
only activates on commands containing `git push`; every other Bash command
passes straight through. Inside Claude Code, attempting `git push` will
run the test suite first and block the push (exit code 2) if coverage is
below 80%. You can also invoke it directly to see it fire:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' \
  | .claude/hooks/check-coverage-before-push.sh
echo "exit code: $?"
```

## 7. Try the custom MCP server (pipeline-status)

Run the pipeline at least once first (step 3), then:

```bash
.venv/bin/python -c "
import asyncio
from fastmcp import Client

async def main():
    async with Client('mcp/server.py') as client:
        print(await client.list_tools())
        print(await client.call_tool('get_transaction_status', {'transaction_id': 'TXN002'}))
        print(await client.call_tool('list_pipeline_results', {}))
        print(await client.read_resource('pipeline://summary'))

asyncio.run(main())
"
```

Or configure `.mcp.json` in your Claude Code client (already present in
this repo) and ask Claude: *"What's the status of TXN002?"*

## 8. Run the REST API gateway

```bash
.venv/bin/python -m uvicorn api.server:app --reload
```

Then open `http://127.0.0.1:8000/` in a browser for a small console
(`api/static/index.html`, served by `api/server.py` itself — no separate
process) with a transaction form, quick-fill demo scenarios, a live
ledger of results, a run summary, and an editor for the policy rule book
(`GET`/`PUT /rules`). It's the same API described below with a UI on top.

Or, in another terminal, drive the API directly:

```bash
# Submit a transaction (runs it through the full 4-agent pipeline)
curl -s -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{
        "transaction_id": "TXN901",
        "timestamp": "2026-07-09T09:00:00Z",
        "source_account": "ACC-1001",
        "destination_account": "ACC-2001",
        "amount": "1500.00",
        "currency": "USD",
        "transaction_type": "transfer",
        "metadata": {"channel": "online", "country": "US"}
      }'

# Fetch one transaction's result
curl -s http://127.0.0.1:8000/transactions/TXN901

# List every result on file
curl -s http://127.0.0.1:8000/transactions

# Run-level summary (same shape as pipeline_summary.json)
curl -s http://127.0.0.1:8000/summary

# Health check
curl -s http://127.0.0.1:8000/health

# Read the policy rule engine's current configuration
curl -s http://127.0.0.1:8000/rules

# Replace it — e.g. drop the withdrawal-flag threshold to $1,000
curl -s -X PUT http://127.0.0.1:8000/rules \
  -H "Content-Type: application/json" \
  -d '{
        "rules": [
          {
            "id": "large_withdrawal",
            "field": "transaction_type",
            "operator": "eq",
            "value": "withdrawal",
            "min_amount": "1000.00",
            "action": "flag",
            "reason": "large_cash_withdrawal"
          }
        ]
      }'
```

By default the API reads/writes the project's `shared/` directory, same
as the CLI; override with the `PIPELINE_SHARED_ROOT` env var to point it
elsewhere (used by `tests/test_api_gateway.py` to keep tests isolated).

`PUT /rules` fully replaces `agents/rule_engine.py`'s configuration — the
same file you'd otherwise hand-edit at `agents/rules_config.json` — so a
policy change can be pushed without touching disk or restarting the
server; the next `POST /transactions` picks it up immediately, since
`rule_engine.py` reloads the file on every call rather than caching it.
Each rule requires `id`, `field`, `operator` (`eq`/`neq`/`in`/`not_in`),
`action` (`reject`/`flag`), and `reason`; `value` and the optional
`min_amount` (a decimal string) depend on the rule. A malformed rule
(bad operator, non-numeric `min_amount`, etc.) is rejected with `422`
before it ever reaches disk.

## 9. Run the zero-manual-steps demo

```bash
./demo.sh
```

This single script: creates `.venv` and installs `requirements.txt` if
missing, clears `shared/`, starts the REST API gateway in the background,
waits for it to become healthy, submits every record in
`sample-transactions.json` via `POST /transactions`, prints each
transaction's final status as it comes back, prints the run summary from
`GET /summary`, and shuts the server down on exit. Nothing to type or
click beyond running the script.

## 10. Try context7 (research MCP)

`.mcp.json` also configures `context7`. Once your MCP client has it
connected, ask Claude to look up a library (e.g. "use context7 to look up
FastMCP's resource decorator") — `research-notes.md` documents two real
queries already made this way during development.

## 11. Regenerate the specification

Run the `/write-spec` skill in Claude Code (or read
`.claude/commands/write-spec.md`) to regenerate `specification.md` from
`specification-TEMPLATE-hint.md`.

## 12. Screenshots

See `docs/screenshots/README.md` for the exact commands to run for each of
the 5 required screenshots.

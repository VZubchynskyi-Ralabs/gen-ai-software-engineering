# Agent Configuration for the Multi-Agent Banking Pipeline

## Overview

This document defines how AI agents (Claude Code, GitHub Copilot, etc.) should
behave when generating code, tests, or documentation for the **Multi-Agent
Banking Pipeline** — a file-based transaction processing system built for
Homework 6. It extends the general FinTech conventions used across this
repository (see `../homework-3/agents.md` for the original dispute-system
version) with rules specific to this project's architecture: independent
agents that communicate exclusively through JSON messages on disk.

**Purpose:** Keep every agent (validator, fraud detector, compliance
checker, integrator, MCP server, tests) consistent in message format,
monetary handling, and logging, regardless of which tool generated the code.

---

## Project-Specific Context

- **Language/runtime:** Python 3.11+, standard library first; `pytest` +
  `pytest-cov` for testing.
- **Input:** `sample-transactions.json` — a flat list of raw transaction
  records (see file for schema).
- **Communication:** Agents never call each other's functions directly across
  process boundaries. They exchange **JSON message files** through
  `shared/{input,processing,output,results}/`, per the protocol in
  `specification.md`.
- **Pipeline order:** `transaction_validator` → `fraud_detector` →
  `compliance_checker`. The integrator (`integrator.py`) is the only
  component that knows this order; each agent only knows how to consume one
  message shape and produce the next.
- **Third agent choice:** Compliance Checker (cross-border / sanctioned
  country / restricted transaction-type rules), chosen over Settlement
  Processor and Reporting Agent because it composes naturally with the fraud
  detector's risk score to decide final disposition.
- **MCP servers:** `context7` (library/framework lookup during code
  generation — see `research-notes.md`) and a custom FastMCP server
  (`mcp/server.py`, exposed as `pipeline-status`) that makes pipeline results
  queryable.

## Technology Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Monetary type | `decimal.Decimal` (never `float`) |
| Currency validation | ISO 4217 code whitelist |
| Message format | JSON files, UTF-8, one message per file |
| Testing | `pytest`, `pytest-cov` |
| MCP | `fastmcp` (custom server), `@upstash/context7-mcp` (research) |
| CLI orchestration | Plain `argparse`-based scripts, no external framework |

---

## Domain Rules: Finance & Banking

### Financial Data Handling

1. **Monetary Values — CRITICAL**
   - ALWAYS parse and store amounts as `decimal.Decimal`, constructed from the
     original **string** (`Decimal("1500.00")`), never via `float`.
   - NEVER pass a `float` into `Decimal(...)` — it re-introduces binary
     rounding error before the value is even wrapped.
   - Round using `ROUND_HALF_UP` and quantize to the currency's minor unit
     (2 decimal places for USD/EUR/GBP) when computing derived amounts (e.g.
     fees, risk-adjusted thresholds).

2. **Currency Handling**
   - Validate `currency` against a fixed ISO 4217 allow-list
     (`USD, EUR, GBP, JPY, ...`). Reject unknown codes (e.g. `XYZ`) at the
     validator stage with a clear reason.
   - Never assume a default currency.

3. **Message Immutability**
   - An agent must not mutate the `data` payload of an inbound message in
     place. It reads the inbound message, computes a new payload, and writes
     a **new** message file for the next stage (or `results/` if terminal).

4. **PII**
   - Treat `source_account` / `destination_account` as sensitive. Logs may
     reference them masked (e.g. `ACC-...2001` → last 4 chars) but must never
     print full account identifiers or account holder names to stdout/log
     files at INFO level or below.

### Regulatory-Style Rules (for the Compliance Checker)

- Flag cross-border transactions (`source country != destination/metadata
  country`, inferred from `metadata.country` vs. a fixed "home country" of
  `US`) for review, not automatic rejection.
- Flag transaction types outside a known set
  (`transfer, wire_transfer, refund, payment, deposit, withdrawal`) as
  `unknown_type` rather than silently accepting them.
- Never hard-code a sanctioned-country list as a security control in
  production — this project's list is illustrative/test data only.

---

## Code Style & Conventions

```python
# Files: snake_case.py
agents/transaction_validator.py

# Classes: PascalCase (only where a class adds value, e.g. dataclasses)
class TransactionMessage:

# Functions/variables: snake_case
def process_message(message: dict) -> dict:

# Constants: UPPER_SNAKE_CASE
FRAUD_HIGH_VALUE_THRESHOLD = Decimal("10000.00")
```

- Every public function has type hints.
- Every agent module exposes a single `process_message(message: dict) -> dict`
  entry point plus a `main()` for standalone/dry-run invocation, so the
  integrator and the `validate-transactions` skill can both call it directly.
- No bare `except:`. Catch specific exceptions, log with context, and write a
  rejected-message result rather than crashing the pipeline.

## Logging Rules

Every agent operation logs one structured JSON line to stdout (and the
integrator persists a run log) with at minimum:

```json
{
  "timestamp": "2026-03-16T10:00:00Z",
  "agent": "fraud_detector",
  "transaction_id": "TXN002",
  "outcome": "flagged",
  "detail": "risk_score=0.82"
}
```

No PII (account numbers, names) may appear in the `detail` field or anywhere
else in a log line.

## Testing & Verification Expectations

- Coverage gate: `pytest --cov` must report **>= 80%** or the push-blocking
  hook (`.claude/settings.json`) rejects `git push`. Target **>= 90%**.
- Unit tests: one test module per agent, covering accept/reject/flag paths.
- Integration test: run the integrator against a temporary copy of
  `sample-transactions.json` (via `tmp_path`) and assert every transaction
  produces a terminal result file in a temp `shared/results/`.
- Tests must never read/write the real project-level `shared/` directory —
  always redirect agents to a `tmp_path`-based shared root.

## Agent Behavior Guidelines

### When Generating Code
1. Prefer the standard library over new dependencies; this project has no
   database, web framework, or network calls in the core pipeline.
2. Keep each agent a pure function of `(inbound message) -> outbound message`
   plus file I/O at the edges — this is what makes them independently unit
   testable.
3. Every new agent must be registered in `integrator.py`'s pipeline order and
   documented in `specification.md`'s Low-Level Tasks.

### When Answering Questions
- Reference `specification.md` for the authoritative behavior of each agent.
- Reference `research-notes.md` for framework/library decisions made via
  context7 during code generation.

---

**End of Agent Configuration**


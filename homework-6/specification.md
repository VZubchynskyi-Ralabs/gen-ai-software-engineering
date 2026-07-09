# Multi-Agent Banking Pipeline Specification

> Ingest the information from this file, implement the Low-Level Tasks, and
> generate the code that will satisfy the High and Mid-Level Objectives.
> Generated via the `/write-spec` skill from `specification-TEMPLATE-hint.md`.

---

## 1. High-Level Objective

Build a file-based multi-agent pipeline that ingests raw bank transaction
records, validates and risk-scores each one, checks it against compliance
rules, and produces an auditable, per-transaction disposition (`approved`,
`rejected`, or `flagged_for_review`) with a run-level summary report.

---

## 2. Mid-Level Objectives

- **MO-1 — Structural validation:** Every transaction is checked for
  required fields, a positive numeric amount, and an ISO 4217 currency code;
  invalid transactions are rejected with a specific reason before any
  downstream agent sees them.
- **MO-2 — Fraud risk scoring:** Transactions above **$10,000** (or
  currency-equivalent threshold), transactions initiated between 00:00–05:00
  UTC, and cross-border transactions each contribute to a numeric risk score
  (0.0–1.0); transactions scoring above **0.7** are flagged for fraud review.
- **MO-3 — Compliance disposition:** Transactions that pass validation and
  fraud scoring are checked for cross-border and transaction-type compliance
  rules and receive a final status of `approved`, `flagged_for_review`, or
  `rejected`.
- **MO-4 — Auditable output:** Every transaction — accepted, rejected, or
  flagged — is written as a JSON result file to `shared/results/` with a
  reason field, its full agent history, and no plaintext PII.
- **MO-5 — Traceable logging:** Every agent operation (validate, score,
  check) is logged as one structured line with an ISO 8601 timestamp, agent
  name, transaction ID, and outcome, so a full run can be reconstructed from
  logs alone.

---

## 3. Implementation Notes

- **Monetary values:** `decimal.Decimal`, constructed from the original
  string amount. Never `float`. Quantize to 2 decimal places using
  `ROUND_HALF_UP` for any derived value (e.g. risk-adjusted thresholds).
- **Currency codes:** ISO 4217 only. Allow-list:
  `USD, EUR, GBP, JPY, CAD, AUD, CHF`. Anything else (e.g. `XYZ`) is a
  validation failure.
- **Logging:** one JSON line per operation with `timestamp` (ISO 8601, UTC,
  `Z` suffix), `agent`, `transaction_id`, `outcome`, and an optional
  non-PII `detail` string. Emitted to stdout and appended to
  `shared/results/pipeline_run.log`.
- **PII:** `source_account` / `destination_account` are sensitive. They may
  be carried in message payloads (needed for settlement) but must never be
  logged in full — mask to last 4 characters wherever they appear in a log
  line or the human-readable summary.
- **Message protocol:** every inter-agent message is a JSON file matching
  the schema in Task 2 of `TASKS.md` (`message_id`, `timestamp`,
  `source_agent`, `target_agent`, `message_type`, `data`). Agents read from
  their inbound directory, move the file to `processing/` while working, and
  write a new message to `output/` (or a terminal result to `results/`).
- **Idempotency:** each message carries a `message_id` (UUID4); agents log
  it so re-runs are traceable, but the reference implementation runs each
  sample transaction exactly once per invocation.

---

## 4. Context

### Beginning State
- `sample-transactions.json` at the project root — 8 raw transaction
  records (see file), covering: normal transfers, a wire transfer over
  $10,000, a near-threshold amount, an off-hours EUR transfer, a very
  large wire transfer, an invalid currency (`XYZ`), a negative amount, and a
  mobile-channel transfer.
- Empty `shared/{input,processing,output,results}/` directories.

### Ending State
- Every transaction from `sample-transactions.json` has exactly one
  terminal JSON file in `shared/results/`.
- `shared/results/pipeline_summary.json` — a run-level report: total count,
  counts by final status, total flagged amount, rejection reasons breakdown.
- `shared/results/pipeline_run.log` — the full structured audit trail for
  the run.
- Test suite coverage **>= 90%** (gate enforced at >= 80% by the pre-push
  hook).

---

## 5. Low-Level Tasks

### Task: Transaction Validator

**Prompt:** "Write a Python module `agents/transaction_validator.py`
exposing `process_message(message: dict) -> dict` that validates a raw
transaction payload: required fields present
(`transaction_id, timestamp, source_account, destination_account, amount,
currency, transaction_type`), `amount` parses as a positive `Decimal`, and
`currency` is in the ISO 4217 allow-list. Return an outbound message with
`data.status` set to `validated` or `rejected` (+ `data.rejection_reason`).
Log every decision via the shared `agents/common.py` logger."

**File to CREATE:** `agents/transaction_validator.py`

**Function to CREATE:** `process_message(message: dict) -> dict`

**Details:** Checks required fields; parses `amount` as `Decimal` from
string (rejects non-numeric or <= 0 amounts); validates `currency` against
`VALID_CURRENCIES`; on success sets `data.status = "validated"` and forwards
`target_agent = "fraud_detector"`; on failure sets `data.status =
"rejected"` with a human-readable `rejection_reason` and no `target_agent`
(terminal — written straight to `shared/results/`).

---

### Task: Fraud Detector

**Prompt:** "Write a Python module `agents/fraud_detector.py` exposing
`process_message(message: dict) -> dict` that computes a 0.0–1.0 risk score
for a validated transaction based on high value (>$10,000), unusual timing
(00:00–05:00 UTC), and cross-border indicators (`metadata.country != 'US'`
for a same-currency-region heuristic), then sets `data.status` to
`flagged_for_review` (score > 0.7) or `fraud_cleared` and forwards to the
compliance checker."

**File to CREATE:** `agents/fraud_detector.py`

**Function to CREATE:** `process_message(message: dict) -> dict`

**Details:** Reads `amount`, `timestamp`, `metadata.country`,
`transaction_type` from the inbound message; computes
`risk_score = min(1.0, sum(weighted signals))` where high-value (> $10,000)
contributes 0.8, off-hours (00:00-05:00 UTC) contributes 0.3, cross-border
(`metadata.country != "US"`) contributes 0.3, wire transfer contributes 0.1
— so a high-value transaction alone already crosses the flag threshold, per
MO-2; attaches `data.risk_score` and `data.risk_factors` (list of triggered
signal names — no PII) to the outbound message; sets
`data.status = "flagged_for_review"` if `risk_score > 0.7` else
`"fraud_cleared"`; always forwards to `compliance_checker` (fraud flags are
advisory at this stage, final disposition happens in compliance).

---

### Task: Compliance Checker

**Prompt:** "Write a Python module `agents/compliance_checker.py` exposing
`process_message(message: dict) -> dict` that makes the final disposition
for a transaction: rejects unknown transaction types, flags cross-border
transactions and any transaction already `flagged_for_review` by fraud
detection for manual review, and approves everything else. Write a
`data.final_status` of `approved`, `flagged_for_review`, or `rejected` with
a `data.reason`."

**File to CREATE:** `agents/compliance_checker.py`

**Function to CREATE:** `process_message(message: dict) -> dict`

**Details:** Validates `transaction_type` against
`KNOWN_TRANSACTION_TYPES`; if unknown, `final_status = "rejected"`,
`reason = "unknown_transaction_type"`; else if inbound
`data.status == "flagged_for_review"` (from fraud detector) or the
transaction is cross-border, `final_status = "flagged_for_review"`; else
`final_status = "approved"`. This is the terminal agent — its output is
written directly to `shared/results/{transaction_id}.json`, not forwarded
further.

---

### Task: Integrator / Orchestrator

**Prompt:** "Write `integrator.py` that sets up the `shared/` directory
tree, loads `sample-transactions.json`, wraps each record as a
`message_type: "transaction"` message, and runs it through
`transaction_validator -> fraud_detector -> compliance_checker` in-process
(moving each message through `processing/`/`output/` for auditability),
then writes a `pipeline_summary.json` report and prints a human-readable
summary to stdout."

**File to CREATE:** `integrator.py`

**Function to CREATE:** `run_pipeline(input_path: Path, shared_root: Path) -> dict`

**Details:** Creates `shared/{input,processing,output,results}` if missing;
reads the input JSON array; for each record, builds the standard message
envelope, calls each agent's `process_message` in sequence (stopping early
on a terminal/rejected result), archives intermediate messages under
`processing/` and `output/` for traceability, and writes the final message
to `results/{transaction_id}.json`; aggregates counts by `final_status`
(or `status` for early-rejected messages) into `pipeline_summary.json`;
appends every agent log line to `pipeline_run.log`; supports a
`--clear` flag to wipe `shared/` before running (used by the
`/run-pipeline` skill).

---

### Task: MCP Pipeline-Status Server

**Prompt:** "Write a FastMCP server `mcp/server.py` exposing tool
`get_transaction_status(transaction_id: str)` that reads
`shared/results/{transaction_id}.json` and returns its status, tool
`list_pipeline_results()` that summarizes all files in `shared/results/`,
and resource `pipeline://summary` that returns the contents of
`pipeline_summary.json` as text."

**File to CREATE:** `mcp/server.py`

**Function to CREATE:** `get_transaction_status(transaction_id: str) -> dict`,
`list_pipeline_results() -> dict`, `pipeline_summary() -> str`

**Details:** All three read-only operations resolve paths relative to the
project's `shared/results/` directory; `get_transaction_status` returns a
clear "not found" payload (not an exception) for unknown IDs; the resource
returns the raw JSON summary as a formatted text block for human/LLM
consumption.

---

### Task: Test Suite

**Prompt:** "Write pytest unit tests for each agent module (accept, reject,
and flag paths) and one integration test that runs `run_pipeline` against a
temporary copy of `sample-transactions.json` and a `tmp_path`-based
`shared/`, asserting every transaction produces exactly one result file."

**File to CREATE:** `tests/test_transaction_validator.py`,
`tests/test_fraud_detector.py`, `tests/test_compliance_checker.py`,
`tests/test_integrator.py`

**Function to CREATE:** one `test_*` function per behavior branch listed
in each agent's Details section above.

**Details:** Tests never touch the real project-level `shared/` directory;
all file I/O in integration tests goes through `tmp_path`. Coverage target
>= 90%, gate enforced at >= 80%.

---

## Verification Summary

| Objective | Verification |
|---|---|
| MO-1 Structural validation | `tests/test_transaction_validator.py`; manual check on `TXN006` (bad currency) and `TXN007` (negative amount) |
| MO-2 Fraud risk scoring | `tests/test_fraud_detector.py`; manual check on `TXN002`, `TXN005` (high value), `TXN004` (off-hours + cross-border) |
| MO-3 Compliance disposition | `tests/test_compliance_checker.py` |
| MO-4 Auditable output | `tests/test_integrator.py` asserts one file per transaction in `shared/results/` |
| MO-5 Traceable logging | Manual review of `shared/results/pipeline_run.log` after a run |

---

**End of Specification**

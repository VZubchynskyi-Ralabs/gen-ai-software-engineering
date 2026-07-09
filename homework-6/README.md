# Multi-Agent Banking Pipeline

**Created by Volodymyr Zubchynskyi** — Homework 6 Capstone, Generative AI for
Software Engineering.

## What this is

This project is a file-based, multi-agent transaction processing pipeline
for a fictional bank. Raw transaction records (`sample-transactions.json`)
are pushed through four independent agents — a **Transaction Validator**,
a **Fraud Detector**, a **Policy Rule Engine**, and a **Compliance
Checker** — that communicate exclusively through JSON message files on
disk, the way independent services in a real payments system might
communicate through a message queue. Every transaction ends up with an
auditable, final disposition (`approved`, `flagged_for_review`, or
`rejected`) written to `shared/results/`, alongside a run-level summary
report and a structured audit log.

A **REST API gateway** (`api/server.py`) wraps this same pipeline behind
HTTP endpoints, and `demo.sh` drives the whole thing end to end with zero
manual steps — see [Try the REST API gateway](#try-the-rest-api-gateway)
below.

Beyond the pipeline itself, this repository is the **deliverable of a
meta-agent exercise**: four "meta-agents" (Claude Code skills/workflows)
were used to *build* the system — one to write the specification, one to
generate the pipeline code (using the `context7` MCP server to look up
FastMCP and `decimal` documentation live, see `research-notes.md`), one to
generate the test suite (gated by a coverage-checking Claude Code hook),
and one to generate this documentation.

## Agent Responsibilities

- **Transaction Validator** (`agents/transaction_validator.py`) — checks
  required fields, parses `amount` as a positive `decimal.Decimal`, and
  validates the currency against an ISO 4217 allow-list. Rejects invalid
  transactions before they reach fraud detection.
- **Fraud Detector** (`agents/fraud_detector.py`) — scores validated
  transactions 0.0–1.0 on high-value, off-hours, cross-border, and
  wire-transfer signals; flags anything scoring above 0.7.
- **Policy Rule Engine** (`agents/rule_engine.py`) — evaluates the
  transaction against a declarative rule set loaded from
  `agents/rules_config.json` (sanctioned countries, large-withdrawal /
  large-wire thresholds, etc.). A matching `reject` rule is terminal; any
  matching `flag` rules are attached as `data.policy_flags` for the
  compliance checker. New rules are added by editing the JSON config, not
  the code.
- **Compliance Checker** (`agents/compliance_checker.py`) — makes the final
  call: rejects unknown transaction types, flags cross-border transactions
  and anything already fraud- or policy-flagged, and approves the rest.
  Terminal agent — writes directly to `shared/results/`.
- **Integrator** (`integrator.py`) — orchestrator. Sets up `shared/`, loads
  `sample-transactions.json`, drives each transaction through the four
  agents in order, and writes the run summary + audit log. Also exposes
  `load_result`/`list_results`/`rebuild_summary` helpers reused by the REST
  API gateway.
- **REST API gateway** (`api/server.py`) — a FastAPI app that wraps the
  pipeline behind HTTP endpoints so transactions can be submitted and
  results retrieved via ordinary HTTP calls, and the policy rule engine's
  configuration can be read and replaced with `GET`/`PUT /rules` instead of
  hand-editing `agents/rules_config.json`; see
  [Try the REST API gateway](#try-the-rest-api-gateway).
- **Pipeline-status MCP server** (`mcp/server.py`) — a custom FastMCP
  server that makes pipeline results queryable by an LLM/MCP client.

## Architecture

```
   sample-transactions.json          HTTP: POST /transactions
   (batch CLI: integrator.py)         (api/server.py, FastAPI)
              │                                │
              └────────────────┬───────────────┘
                                ▼
                      ┌──────────────────┐
                      │    integrator    │  (orchestrator / shared helpers)
                      └──────────────────┘
                                │  wraps each record as a
                                │  standard message envelope
                                ▼
   shared/input/ ──▶ ┌───────────────────────────┐
                      │   transaction_validator   │──reject──▶ shared/results/
                      └───────────────────────────┘             {id}.json
                                │ validated
                                ▼
                      ┌───────────────────────────┐
                      │      fraud_detector        │
                      └───────────────────────────┘
                                │ risk-scored (always forwards)
                                ▼
                      ┌───────────────────────────┐
                      │       rule_engine          │──reject──▶ shared/results/
                      │  (agents/rules_config.json)│             {id}.json
                      └───────────────────────────┘
                                │ flags attached (always forwards)
                                ▼
                      ┌───────────────────────────┐
                      │    compliance_checker      │──approved/flagged/──▶ shared/results/
                      └───────────────────────────┘   rejected              {id}.json
                                                              │
                                                              ▼
                                                  pipeline_summary.json
                                                  pipeline_run.log

   Every hop above also persists an intermediate message under
   shared/processing/ and shared/output/ for auditability.

                      ┌───────────────────────────┐
   HTTP client ──────▶│  api/server.py (FastAPI)   │──reads/writes──▶ shared/
   (curl, demo.sh)     │  POST /transactions        │
                       │  GET /transactions[/{id}]  │
                       │  GET /summary, /health      │
                       │  GET/PUT /rules ───────────┼──▶ agents/rules_config.json
                       └───────────────────────────┘

                      ┌───────────────────────────┐
   MCP client ───────▶│  mcp/server.py (FastMCP)   │──reads──▶ shared/results/
   (Claude, etc.)      │  get_transaction_status    │
                       │  list_pipeline_results     │
                       │  pipeline://summary        │
                       └───────────────────────────┘
```

## Tech Stack

| Concern | Choice |
|---|---|
| Language | Python 3.11+ |
| Monetary type | `decimal.Decimal` (never `float`) |
| Message format | JSON files on disk (`shared/{input,processing,output,results}/`) |
| Testing | `pytest` + `pytest-cov` |
| MCP servers | `context7` (research) + custom `fastmcp` server (`mcp/server.py`) |
| REST API gateway | `fastapi` + `uvicorn` (`api/server.py`) |
| Rule config | Declarative JSON (`agents/rules_config.json`) |
| Automation | Claude Code skills (`.claude/commands/`) + coverage-gate hook (`.claude/settings.json`) + `demo.sh` |

## Repository Map

| Path | Purpose |
|---|---|
| `specification.md` | Full technical spec (Agent 1 output) |
| `specification-TEMPLATE-hint.md` | Template the spec was generated from |
| `agents.md` | Project-specific AI agent behavior rules |
| `agents/` | The four pipeline agents + shared utilities + `rules_config.json` |
| `integrator.py` | Orchestrator / entry point + read/summary helpers reused by the API |
| `api/server.py` | REST API gateway (FastAPI) over the pipeline |
| `mcp/server.py` | Custom FastMCP server |
| `.mcp.json` / `mcp.json` | context7 + pipeline-status MCP server config |
| `research-notes.md` | Live context7 queries made while building `mcp/server.py` |
| `.claude/commands/` | `/write-spec`, `/run-pipeline`, `/validate-transactions` skills |
| `.claude/settings.json` + `.claude/hooks/` | Coverage-gate pre-push hook |
| `tests/` | Unit + integration test suite |
| `demo.sh` | Zero-manual-steps demo: starts the API, submits all sample transactions, prints results |
| `docs/screenshots/` | Required screenshots (see `docs/screenshots/README.md`) |
| `HOWTORUN.md` | Step-by-step setup and demo instructions |

See `HOWTORUN.md` to run the pipeline yourself.

## Try the REST API gateway

```bash
./demo.sh
```

This starts `api/server.py` via `uvicorn`, submits every record in
`sample-transactions.json` through `POST /transactions`, prints each
transaction's final status, and prints the run summary from `GET
/summary` — no manual steps. See `HOWTORUN.md` for the individual `curl`
commands if you want to drive the API by hand.

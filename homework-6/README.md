# Multi-Agent Banking Pipeline

**Created by Volodymyr Zubchynskyi** — Homework 6 Capstone, Generative AI for
Software Engineering.

## What this is

This project is a file-based, multi-agent transaction processing pipeline
for a fictional bank. Raw transaction records (`sample-transactions.json`)
are pushed through three independent agents — a **Transaction Validator**,
a **Fraud Detector**, and a **Compliance Checker** — that communicate
exclusively through JSON message files on disk, the way independent
services in a real payments system might communicate through a message
queue. Every transaction ends up with an auditable, final disposition
(`approved`, `flagged_for_review`, or `rejected`) written to
`shared/results/`, alongside a run-level summary report and a structured
audit log.

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
- **Compliance Checker** (`agents/compliance_checker.py`) — makes the final
  call: rejects unknown transaction types, flags cross-border transactions
  and anything already fraud-flagged, and approves the rest. Terminal agent
  — writes directly to `shared/results/`.
- **Integrator** (`integrator.py`) — orchestrator. Sets up `shared/`, loads
  `sample-transactions.json`, drives each transaction through the three
  agents in order, and writes the run summary + audit log.
- **Pipeline-status MCP server** (`mcp/server.py`) — a custom FastMCP
  server that makes pipeline results queryable by an LLM/MCP client.

## Architecture

```
                         sample-transactions.json
                                    │
                                    ▼
                          ┌──────────────────┐
                          │    integrator    │  (orchestrator)
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
                      │    compliance_checker      │──approved/flagged/──▶ shared/results/
                      └───────────────────────────┘   rejected              {id}.json
                                                              │
                                                              ▼
                                                  pipeline_summary.json
                                                  pipeline_run.log

   Every hop above also persists an intermediate message under
   shared/processing/ and shared/output/ for auditability.

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
| Automation | Claude Code skills (`.claude/commands/`) + coverage-gate hook (`.claude/settings.json`) |

## Repository Map

| Path | Purpose |
|---|---|
| `specification.md` | Full technical spec (Agent 1 output) |
| `specification-TEMPLATE-hint.md` | Template the spec was generated from |
| `agents.md` | Project-specific AI agent behavior rules |
| `agents/` | The three pipeline agents + shared utilities |
| `integrator.py` | Orchestrator / entry point |
| `mcp/server.py` | Custom FastMCP server |
| `.mcp.json` / `mcp.json` | context7 + pipeline-status MCP server config |
| `research-notes.md` | Live context7 queries made while building `mcp/server.py` |
| `.claude/commands/` | `/write-spec`, `/run-pipeline`, `/validate-transactions` skills |
| `.claude/settings.json` + `.claude/hooks/` | Coverage-gate pre-push hook |
| `tests/` | Unit + integration test suite |
| `docs/screenshots/` | Required screenshots (see `docs/screenshots/README.md`) |
| `HOWTORUN.md` | Step-by-step setup and demo instructions |

See `HOWTORUN.md` to run the pipeline yourself.

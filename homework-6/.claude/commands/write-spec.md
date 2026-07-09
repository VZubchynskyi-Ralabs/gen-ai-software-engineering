---
description: Generate or refresh specification.md from the project template
---

Generate (or refresh) `specification.md` for the Multi-Agent Banking Pipeline
following the structure in `specification-TEMPLATE-hint.md`.

Steps:
1. Read `specification-TEMPLATE-hint.md` for the required section structure.
2. Read `agents.md` for project-specific context (stack, agent roles, domain
   rules) and `sample-transactions.json` for the actual shape of the input
   data.
3. Read `TASKS.md` to confirm the required deliverables and the minimum set
   of agents (Transaction Validator, Fraud Detector, and at least one of
   Compliance Checker / Settlement Processor / Reporting Agent).
4. Write `specification.md` with exactly these sections, in order:
   1. High-Level Objective — one sentence.
   2. Mid-Level Objectives — 4-5 concrete, testable bullets.
   3. Implementation Notes — monetary types, currency codes, logging,
      PII handling, message protocol.
   4. Context — Beginning State and Ending State.
   5. Low-Level Tasks — one entry per agent (including the
      integrator/orchestrator and the MCP server), each with the exact
      `Task / Prompt / File to CREATE / Function to CREATE / Details` shape
      shown in `TASKS.md`.
5. Cross-check every Mid-Level Objective has at least one corresponding
   Low-Level Task and appears in a closing Verification Summary table.
6. Do not invent requirements beyond what `TASKS.md` and the sample data
   support — flag anything ambiguous instead of guessing.

Report a short diff summary of what changed versus the previous
`specification.md`, if one existed.

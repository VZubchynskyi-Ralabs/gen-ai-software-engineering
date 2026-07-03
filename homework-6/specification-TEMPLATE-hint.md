# Specification Template (Hint)

> This is the structural template for `specification.md`. It is a distilled,
> project-agnostic version of the fuller Homework 3 specification template
> (`../homework-3/specification-TEMPLATE-example.md`), scoped to what a
> file-based multi-agent pipeline needs. Fill in every section — do not
> delete headings even if a section is short.

---

## High-Level Objective

One sentence. What does the pipeline do, end to end, for whom?

## Mid-Level Objectives

4–5 bullets. Each one must be independently testable/observable — someone
should be able to look at pipeline output and say yes/no whether the
objective was met. Avoid vague verbs ("improve", "handle") in favor of
concrete, checkable outcomes ("flagged", "written to", "logged with").

## Implementation Notes

Cross-cutting rules that apply to every agent in the pipeline:
- Monetary value representation (type, rounding rules)
- Currency/code standards in use
- Logging format and audit trail fields
- PII / sensitive-data handling rules
- Any other invariant every agent must respect (idempotency, message schema, etc.)

## Context

**Beginning state** — what exists before any agent runs (input files, empty
directories, configuration).

**Ending state** — what exists after a full pipeline run (output files,
directories, reports, coverage bar).

## Low-Level Tasks

One entry per agent/component, in execution order. Each entry uses this
exact shape:

```
Task: [Agent Name]
Prompt: "[Exact prompt you would give an AI coding assistant to build this agent]"
File to CREATE: path/to/file.py
Function to CREATE: function_signature(...) -> ReturnType
Details: [What the agent checks, transforms, decides, and what it writes/emits]
```

---

*Invoke `/write-spec` to regenerate `specification.md` from this template
using the current project context in `agents.md` and `sample-transactions.json`.*

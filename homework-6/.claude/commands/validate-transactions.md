---
description: Validate transactions in sample-transactions.json without running the full pipeline
---

Validate all transactions in `sample-transactions.json` without processing
them through fraud detection or compliance.

Steps:
1. Run `python3 agents/transaction_validator.py --dry-run` (optionally with
   `--input <path>` for a different transactions file).
2. Parse the JSON report it prints: `total`, `valid_count`, `invalid_count`,
   and the `invalid` list (`transaction_id` + `reason` per rejected
   transaction).
3. Show a table of results: one row per transaction with `transaction_id`,
   `status` (`validated` / `rejected`), and `reason` (blank for validated
   rows).
4. Summarize at the end: "`X` of `Y` transactions are structurally valid;
   `Z` would be rejected before reaching fraud detection or compliance,
   for these reasons: ...".

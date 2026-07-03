---
description: Run the multi-agent banking pipeline end-to-end
---

Run the multi-agent banking pipeline end-to-end.

Steps:
1. Check that `sample-transactions.json` exists at the project root; stop
   and report if it's missing.
2. Run `python3 integrator.py --clear` (the `--clear` flag wipes
   `shared/input`, `shared/processing`, `shared/output`, `shared/results`
   before the run, so results reflect only this run).
3. Read `shared/results/pipeline_summary.json` and show a summary table:
   total transactions, and counts by final status
   (`approved` / `flagged_for_review` / `rejected`).
4. List every transaction that was `rejected`, with its
   `rejection_reason`, and every transaction `flagged_for_review`, with its
   `risk_score` and `reason`.
5. Point out where the full audit trail lives
   (`shared/results/pipeline_run.log`) and where the per-transaction result
   files are (`shared/results/{transaction_id}.json`).

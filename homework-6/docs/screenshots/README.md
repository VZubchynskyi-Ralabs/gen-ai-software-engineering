# Screenshots

Commands used to produce each required screenshot in this folder. Run these
from the project root (`homework-6/`) with the virtualenv activated
(`source .venv/bin/activate`) unless noted otherwise.

| File | How it was captured |
|---|---|
| `pipeline-run.png` | Run `python integrator.py --clear` and screenshot the full terminal output (directory setup, per-transaction validator/fraud/compliance log lines, and the final summary). |
| `test-coverage.png` | Run `python -m pytest --cov-report=term-missing` and screenshot the coverage table plus the `Required test coverage of 80% reached` line. |
| `skill-run-pipeline.png` / `skill-run-pipeline-2.png` | In Claude Code, run `/run-pipeline` and screenshot it executing (dir clear + pipeline run) and the results summary it reports back. |
| `hook-trigger.png` | Drop test coverage below 80% (or attempt `git push` normally) so `.claude/hooks/check-coverage-before-push.sh` fires, and screenshot the blocking output. |
| `mcp-interaction.png` / `mcp-interaction-2.png` | In Claude Code, ask a context7 question (e.g. "use context7 to look up FastMCP's resource decorator") for one screenshot, and call a custom MCP tool (e.g. "what's the status of TXN002?" → `get_transaction_status`) for the other. |

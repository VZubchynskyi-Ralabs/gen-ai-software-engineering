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
  **3 approved / 3 flagged_for_review / 2 rejected**.

Or, from inside Claude Code, run the `/run-pipeline` skill instead of the
raw command — it does the same thing and reports the summary for you.

## 4. Validate transactions without running the full pipeline

```bash
.venv/bin/python agents/transaction_validator.py --dry-run
```

Or use the `/validate-transactions` skill in Claude Code.

## 5. Run the tests (with coverage)

```bash
.venv/bin/python -m pytest
```

`pytest.ini` already wires up `--cov=agents --cov=integrator --cov=mcp
--cov-report=term-missing --cov-fail-under=80`, so a plain `pytest` run
both runs the suite and enforces the 80% gate. Current coverage on this
codebase is ~99%.

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

## 8. Try context7 (research MCP)

`.mcp.json` also configures `context7`. Once your MCP client has it
connected, ask Claude to look up a library (e.g. "use context7 to look up
FastMCP's resource decorator") — `research-notes.md` documents two real
queries already made this way during development.

## 9. Regenerate the specification

Run the `/write-spec` skill in Claude Code (or read
`.claude/commands/write-spec.md`) to regenerate `specification.md` from
`specification-TEMPLATE-hint.md`.

## 10. Screenshots

See `docs/screenshots/README.md` for the exact commands to run for each of
the 5 required screenshots.

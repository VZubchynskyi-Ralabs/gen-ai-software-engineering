#!/usr/bin/env bash
# PreToolUse hook: blocks `git push` unless pytest coverage is >= 80%.
#
# Claude Code invokes this with the tool-call JSON on stdin
# ({"tool_name": "Bash", "tool_input": {"command": "..."}, ...}).
# Exit 0 to allow the tool call, exit 2 to block it (stderr is shown as
# the block reason).
set -euo pipefail

INPUT_JSON="$(cat)"
COMMAND=$(printf '%s' "$INPUT_JSON" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print('')
    sys.exit(0)
print(data.get('tool_input', {}).get('command', ''))
")

case "$COMMAND" in
  *"git push"*) ;;
  *) exit 0 ;;
esac

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

PY="$PROJECT_DIR/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="python3"
fi

LOG_FILE="$PROJECT_DIR/.claude/hooks/coverage-gate.log"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

COV_OUTPUT="$("$PY" -m pytest --cov=agents --cov=integrator --cov=mcp --cov-report=term-missing -q 2>&1)" || true
echo "$COV_OUTPUT" >&2

COVERAGE_PCT=$(printf '%s' "$COV_OUTPUT" | grep -E '^TOTAL' | awk '{print $NF}' | tr -d '%')

if [ -z "$COVERAGE_PCT" ]; then
  echo "[$TIMESTAMP] git push BLOCKED: could not determine coverage percentage" >> "$LOG_FILE"
  echo "COVERAGE GATE: could not determine test coverage — blocking push to be safe." >&2
  exit 2
fi

if [ "$COVERAGE_PCT" -lt 80 ]; then
  echo "[$TIMESTAMP] git push BLOCKED: coverage ${COVERAGE_PCT}% < 80%" >> "$LOG_FILE"
  echo "COVERAGE GATE: total coverage is ${COVERAGE_PCT}%, below the required 80%. Push blocked. Add tests before pushing." >&2
  exit 2
fi

echo "[$TIMESTAMP] git push ALLOWED: coverage ${COVERAGE_PCT}% >= 80%" >> "$LOG_FILE"
echo "COVERAGE GATE: total coverage is ${COVERAGE_PCT}% (>= 80%). Push allowed." >&2
exit 0

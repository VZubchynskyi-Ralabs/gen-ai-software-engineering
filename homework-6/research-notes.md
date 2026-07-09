# Research Notes — context7 Queries

These queries were made live against the `context7` MCP server (configured
in `.mcp.json` / `mcp.json`) while building `mcp/server.py` (Agent 2 /
code-generation) and the shared `Decimal` handling in `agents/common.py`.
Both were executed as real MCP tool calls (`resolve-library-id` then
`query-docs`) via a `fastmcp.Client`, not simulated.

---

## Query 1: FastMCP tool & resource decorator patterns

- **Search:** `resolve-library-id(query="FastMCP python server tools and
  resources", libraryName="FastMCP")`
- **context7 library ID:** `/prefecthq/fastmcp` (High source reputation,
  4105 code snippets, benchmark score 84.56)
- **Follow-up:** `query-docs(libraryId="/prefecthq/fastmcp", query="How to
  define a tool with @mcp.tool() and a resource with @mcp.resource()
  including path parameters")`
- **Result excerpt:**
  ```python
  @mcp.tool
  def add(a: int, b: int) -> int:
      """Adds two integer numbers together."""
      return a + b

  @mcp.resource("weather://{city}/current")
  def get_weather(city: str) -> str:
      """Provides weather information for a specific city."""
      ...
  ```
- **Applied:** Confirmed `mcp/server.py`'s `@mcp.tool()` /
  `@mcp.resource("pipeline://summary")` usage matches the current FastMCP
  API exactly (decorator directly on the function, plain return values —
  no manual JSON-RPC envelope needed). Used the same pattern for
  `get_transaction_status`, `list_pipeline_results`, and the
  `pipeline://summary` resource.

---

## Query 2: Python `decimal` module for monetary arithmetic

- **Search:** `resolve-library-id(query="Python decimal module for
  monetary arithmetic", libraryName="Python")`
- **context7 library ID:** `/python/cpython` (High source reputation,
  47991 code snippets, benchmark score 80.4)
- **Follow-up:** `query-docs(libraryId="/python/cpython", query="decimal
  module Decimal class construct from string and ROUND_HALF_UP rounding
  for monetary values")`
- **Result excerpt:**
  ```python
  >>> round(Decimal('0.70') * Decimal('1.05'), 2)
  Decimal('0.74')
  >>> round(.70 * 1.05, 2)
  0.73          # binary float error — wrong for money

  >>> Decimal(str(2.0 ** 0.5))
  Decimal('1.4142135623730951')   # constructing from str(float) avoids
                                   # importing the float's binary noise
  ```
- **Applied:** Confirmed the project rule in `agents.md` /
  `specification.md` — `agents/common.py::parse_amount()` explicitly
  rejects a `float` input outright (`isinstance(raw, float): return None`)
  and only ever constructs `Decimal` from the original JSON **string**
  value (e.g. `Decimal("25000.00")`), never from a float or from a
  float-derived string. This is what the fraud detector and compliance
  checker rely on for exact threshold comparisons (`amount >
  HIGH_VALUE_THRESHOLD`) without binary rounding drift.

---

## Notes on tooling

- Both queries were run through `fastmcp.Client({"mcpServers": {"context7":
  {"command": "npx", "args": ["-y", "@upstash/context7-mcp@latest"]}}})`,
  the same transport configuration declared in `.mcp.json`.
- Screenshot of a live query + result: see `docs/screenshots/mcp-interaction.png`
  (capture instructions in `docs/screenshots/README.md`).

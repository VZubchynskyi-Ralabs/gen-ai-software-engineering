# How to Run

## Prerequisites

- **Node.js** ≥ 18 (for `npx`-based servers)
- **Python** ≥ 3.10 with **uv** installed (`pip install uv` or `brew install uv`)
- **Claude Code** CLI

---

## 1. Create Required Tokens

### GitHub Personal Access Token (PAT)

1. Go to <https://github.com/settings/tokens> → **Generate new token (classic)**
2. Select scopes: `repo`, `read:org`, `read:user`
3. Copy the token

### Jira API Token

1. Go to <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Click **Create API token**, give it a name, copy the token
3. Note your Atlassian email and your Jira base URL (e.g. `https://mycompany.atlassian.net`)

---

## 2. Configure `.mcp.json`

Edit `.mcp.json` in this directory and replace all placeholder values:

```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<paste your GitHub PAT here>"
      }
    },
    "jira": {
      "env": {
        "JIRA_URL": "https://<your-domain>.atlassian.net",
        "JIRA_USERNAME": "<your-atlassian-email>",
        "JIRA_API_TOKEN": "<paste your Jira API token here>"
      }
    }
  }
}
```

The `filesystem` and `lorem-ipsum` servers require no credentials.

---

## 3. Install Custom MCP Server Dependencies

```bash
cd custom-mcp-server
pip install -r requirements.txt
```

Or with uv (recommended):

```bash
cd custom-mcp-server
uv pip install -r requirements.txt
```

---

## 4. Start the Custom MCP Server (standalone test)

```bash
python custom-mcp-server/server.py
```

The server starts and listens on stdin/stdout (MCP transport). You can also run it via FastMCP's CLI:

```bash
fastmcp run custom-mcp-server/server.py
```

---

## 5. Connect MCP Servers to Claude Code

Claude Code reads `.mcp.json` automatically from the project root when you open the project. To confirm all servers are registered:

```bash
claude mcp list
```

To add them from the CLI explicitly:

```bash
# GitHub
claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=<your-token> -- npx -y @modelcontextprotocol/server-github

# Filesystem
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /Users/volodymyr/projects/gen-ai-software-engineering

# Jira
claude mcp add jira -e JIRA_URL=https://<domain>.atlassian.net -e JIRA_USERNAME=<email> -e JIRA_API_TOKEN=<token> -- uvx mcp-atlassian

# Custom lorem-ipsum
claude mcp add lorem-ipsum -- python /path/to/homework-5/custom-mcp-server/server.py
```

---

## 6. Test the `read` Tool

Once Claude Code is running with the MCP servers connected, prompt it:

```
Use the lorem-ipsum read tool with word_count=50
```

Expected response: exactly 50 words from `lorem-ipsum.md`.

You can also read the resource directly by URI:

```
Read the resource lorem://ipsum/50
```

---

## 7. Test Other Servers

**GitHub:**
```
List my recent pull requests on the gen-ai-software-engineering repository
```

**Filesystem:**
```
List the files in the gen-ai-software-engineering directory
```

**Jira:**
```
Give me the tickets of the last 5 bugs in project <YOUR_PROJECT_KEY>
```

---

## Dependency Verification

| Dependency | Where | Version |
|-----------|-------|---------|
| `fastmcp` | `custom-mcp-server/requirements.txt` | `>=2.0.0` |
| `@modelcontextprotocol/server-github` | `.mcp.json` (via npx) | latest |
| `@modelcontextprotocol/server-filesystem` | `.mcp.json` (via npx) | latest |
| `mcp-atlassian` | `.mcp.json` (via uvx) | latest |
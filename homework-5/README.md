# Homework 5: Configure MCP Servers

**Author:** Volodymyr Zubchynskyi

## Description

This homework demonstrates configuring and using four MCP (Model Context Protocol) servers with Claude Code:

1. **GitHub MCP** — connects Claude to GitHub via the official `@modelcontextprotocol/server-github` server, enabling interactions such as listing pull requests, reading commits, and creating issues directly from the AI client.

2. **Filesystem MCP** — connects Claude to a local directory via `@modelcontextprotocol/server-filesystem`, allowing file listing, reading, and directory summarization.

3. **Jira MCP** — connects Claude to an Atlassian Jira workspace via `mcp-atlassian`, enabling ticket querying (e.g. listing the last 5 bug tickets in a project).

4. **Custom MCP Server (FastMCP)** — a hand-written MCP server built with [FastMCP](https://github.com/jlowin/fastmcp). It exposes:
   - A **Resource** at `lorem://ipsum/{word_count}` that reads from `lorem-ipsum.md` and returns the requested number of words.
   - A **Tool** named `read` that Claude can call with an optional `word_count` argument to fetch content from the same source.

### Resources vs Tools

| Concept | What it is |
|---------|-----------|
| **Resource** | A URI that Claude can read from passively — analogous to a file or API endpoint. Claude fetches it by URI (e.g. `lorem://ipsum/50`). |
| **Tool** | An action Claude can actively invoke with arguments — analogous to a function call. Claude calls `read(word_count=50)` and receives the result. |

## Project Structure

```
homework-5/
├── README.md
├── HOWTORUN.md
├── .mcp.json                          # MCP server configuration
├── custom-mcp-server/
│   ├── server.py                      # FastMCP server implementation
│   ├── lorem-ipsum.md                 # Source text for the resource/tool
│   └── requirements.txt               # Python dependencies (fastmcp)
└── docs/
    └── screenshots/
        ├── github-mcp-result.png
        ├── filesystem-mcp-result.png
        ├── jira-or-notion-mcp-result.png
        └── custom-mcp-read-tool-result.png
```
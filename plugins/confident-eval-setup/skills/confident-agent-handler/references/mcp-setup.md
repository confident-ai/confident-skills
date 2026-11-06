# Connecting the Confident AI MCP Server

The Confident AI MCP server is hosted, signs in with OAuth, and acts as the
user across every project their account can reach. No API key is needed.

| Region | MCP server URL |
| --- | --- |
| US (default) | `https://mcp.confident-ai.com/mcp` |
| EU | `https://eu.mcp.confident-ai.com/mcp` |
| Self-hosted | The deployment's own `/mcp` URL |

## Claude Code

```bash
claude mcp add --transport http confident-ai https://mcp.confident-ai.com/mcp
```

Then run `/mcp` inside Claude Code and pick the server to sign in.

## Cursor

Add the server to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json`
(global):

```json
{
  "mcpServers": {
    "confident-ai": {
      "url": "https://mcp.confident-ai.com/mcp"
    }
  }
}
```

Then open **Cursor Settings → MCP** and choose **Authenticate** on the server.

## Other clients

Any MCP client that supports remote servers and OAuth works. Add the URL above
as a remote (HTTP) server and complete the browser sign-in the first time the
client connects.

Full instructions: https://www.confident-ai.com/docs/reference/mcp

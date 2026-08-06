# sqlfluff-mcp

An [MCP](https://modelcontextprotocol.io) server that exposes [SQLFluff](https://sqlfluff.com)'s
linting, fixing, and parsing over the Model Context Protocol, so any MCP-aware
client (Claude, other agents, IDE integrations) can lint and fix SQL directly.

This project is independent of the SQLFluff maintainers — it's a thin wrapper
around the public `sqlfluff` Python package.

## Tools

| Tool | Input | Config resolution |
|---|---|---|
| `lint_file` | path on disk | walks up from the file for `.sqlfluff` / `pyproject.toml` / etc. |
| `fix_file` | path on disk (+ `write` flag) | same directory walk |
| `parse_file` | path on disk | same directory walk |
| `lint_sql` | raw SQL text + `dialect` | none — dialect supplied explicitly |
| `fix_sql` | raw SQL text + `dialect` | none — dialect supplied explicitly |
| `parse_sql` | raw SQL text + `dialect` | none — dialect supplied explicitly |
| `list_dialects` | — | lists supported dialect names |

The `*_file` tools honor project config the same way the `sqlfluff` CLI does
(via `FluffConfig.from_path`, which walks up the directory tree looking for
`.sqlfluff`, `pyproject.toml`, `setup.cfg`, or `tox.ini`). The `*_sql` tools
are for content that hasn't been written to disk (e.g. streamed from an
editor buffer) and require you to pass `dialect` explicitly since there's no
file location to resolve config from.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

## Install

```bash
git clone <this-repo-url>
cd sqlfluff-mcp
uv sync            # or: pip install -e ".[dev]"
```

## Run

```bash
uv run sqlfluff-mcp          # or: sqlfluff-mcp, if installed on PATH
```

This starts the server over stdio, the standard transport for MCP clients
that launch servers as a subprocess (Claude Desktop, Claude Code, etc.).

### Registering with an MCP client

Example Claude Desktop / Claude Code config entry:

```json
{
  "mcpServers": {
    "sqlfluff": {
      "command": "uv",
      "args": ["--directory", "/path/to/sqlfluff-mcp", "run", "sqlfluff-mcp"]
    }
  }
}
```

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

## Notes on dependencies

- `mcp` is pinned to `<2.0.0`. The SDK's 2.0 line restructured the
  high-level server API (no more `mcp.server.fastmcp.FastMCP`); this project
  hasn't been migrated yet.
- `sqlfluff` is left unpinned above `3.0.0` — SQLFluff releases fairly often
  and this server only depends on its stable `Linter` / `FluffConfig` API.

## License

MIT — see [LICENSE](LICENSE).

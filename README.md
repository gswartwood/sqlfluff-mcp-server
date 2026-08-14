# sqlfluff-mcp-server

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
| `clear_config_cache` | — | clears SQLFluff's cached config-file contents |

The `*_file` tools honor project config the same way the `sqlfluff` CLI does
(via `FluffConfig.from_path`, which walks up the directory tree looking for
`.sqlfluff`, `pyproject.toml`, `setup.cfg`, or `tox.ini`). The `*_sql` tools
are for content that hasn't been written to disk (e.g. streamed from an
editor buffer) and require you to pass `dialect` explicitly since there's no
file location to resolve config from.

### Config caching

SQLFluff caches the contents of config files it reads while walking a
directory tree, for the lifetime of the process. Because this server is
long-running (unlike the `sqlfluff` CLI, which is a fresh process per
invocation), editing a `.sqlfluff` file after the server has started won't
be picked up by `lint_file` / `fix_file` / `parse_file` until you call
`clear_config_cache`. Call it whenever config on disk changes, or just
proactively before a lint/fix/parse call if you're unsure.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pipx`/`pip`

## Registering with an MCP client

This package is published on [PyPI](https://pypi.org/project/sqlfluff-mcp-server/),
so there's nothing to clone or install ahead of time. Point your MCP
client's config (e.g. `.claude.json` / `.mcp.json` for Claude Code, or
Claude Desktop's config file) at it via `uvx`, and it's fetched into an
isolated cache and launched on demand:

```json
{
  "mcpServers": {
    "sqlfluff": {
      "command": "uvx",
      "args": ["sqlfluff-mcp-server"]
    }
  }
}
```

No `uv`? `pipx run sqlfluff-mcp-server` as the `command`/`args` works the
same way.

For stdio-based servers like this one, the client itself launches the
process — automatically, when the client session starts, not when a prompt
first needs it. Once it's registered, just ask the client to lint or fix a
SQL file; the server is already running in the background and the tools are
already available. If the server process crashes, the client restarts it
for you.

### Running it manually (for local testing/debugging)

```bash
uvx sqlfluff-mcp-server
```

This starts the server over stdio and blocks, waiting for an MCP client to
speak the protocol to it on stdin/stdout — it's not something you'd run
interactively day to day, just useful for sanity-checking the install or
piping through the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector).

## Development

Clone the repo to work on the server itself (rather than just consuming it
via `uvx`):

```bash
git clone <this-repo-url>
cd sqlfluff-mcp-server
uv sync --extra dev
uv run pytest
uv run ruff check .
```

To point an MCP client at your local checkout instead of the PyPI release
(e.g. to test unreleased changes):

```json
{
  "mcpServers": {
    "sqlfluff": {
      "command": "uv",
      "args": ["--directory", "/path/to/sqlfluff-mcp-server", "run", "sqlfluff-mcp-server"]
    }
  }
}
```

## Notes on dependencies

- `mcp` is pinned to `>=2.0.0,<3.0.0`. The SDK's 2.0 line renamed
  `mcp.server.fastmcp.FastMCP` to `mcp.server.mcpserver.MCPServer` and moved
  transport selection to `run(transport=...)`; the `@mcp.tool()` decorator
  API is unchanged.
- `sqlfluff` is left unpinned above `3.0.0` — SQLFluff releases fairly often
  and this server only depends on its stable `Linter` / `FluffConfig` API.

## License

MIT — see [LICENSE](LICENSE).

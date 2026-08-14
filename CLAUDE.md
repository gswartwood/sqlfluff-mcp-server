# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An MCP server that exposes SQLFluff's lint/fix/parse functionality as MCP
tools, so any MCP-aware client can lint and fix SQL. It's a thin wrapper
around the `sqlfluff` Python package — all the real work happens in
SQLFluff's `Linter` / `FluffConfig` APIs; this project just adapts them to
the MCP tool interface via `mcp.server.fastmcp.FastMCP`.

## Commands

```bash
uv sync --extra dev        # install with dev deps (pytest, ruff)
uv run pytest               # run tests
uv run pytest -v tests/test_server.py::test_fix_sql_returns_cleaned_sql  # single test
uv run ruff check .         # lint
uv run sqlfluff-mcp-server  # run the server manually over stdio (for debugging/MCP Inspector)
```

CI (`.github/workflows/ci.yml`) runs `ruff check .` and `pytest -v` on
Python 3.10/3.11/3.12 via plain `pip install -e ".[dev]"` (not `uv`).

## Architecture

Everything lives in one file, `src/sqlfluff_mcp/server.py`. There are two
parallel families of tools, both defined as `@mcp.tool()` functions:

- **`*_file` tools** (`lint_file`, `fix_file`, `parse_file`): take a path on
  disk. Config is resolved via `FluffConfig.from_path`, which walks up from
  the file's directory looking for `.sqlfluff`, `pyproject.toml`,
  `setup.cfg`, or `tox.ini` — the same resolution the `sqlfluff` CLI uses.
  An optional `config_path` layers on an extra config file (like the CLI's
  `--config`).
- **`*_sql` tools** (`lint_sql`, `fix_sql`, `parse_sql`): take raw SQL text
  directly (e.g. from an editor buffer that hasn't been saved) and require
  an explicit `dialect` argument, since there's no file location to resolve
  config from. Built via `FluffConfig.from_kwargs(dialect=..., rules=...)`.

Plus two utility tools: `list_dialects` and `clear_config_cache`.

**Config caching gotcha**: SQLFluff caches config file *contents* for the
lifetime of the process (keyed by file path). Since this server is
long-running (unlike the `sqlfluff` CLI, which is a fresh process per
invocation), edits to `.sqlfluff`/`pyproject.toml`/etc. made after the
server started won't be picked up by the `*_file` tools until
`clear_config_cache()` (which calls `sqlfluff.core.config.clear_config_caches`)
is invoked. Keep this in mind if adding new file-resolution logic or
debugging stale-config test failures.

Shared helpers at the top of `server.py`:
- `_config_for_path` / `_config_for_dialect` — build a `FluffConfig` for
  each tool family.
- `_read_file` — validates a path exists, raising `SQLFluffUserError` if not.
- `_violations_to_dicts` — converts SQLFluff violation objects to
  JSON-serializable dicts for the MCP response.

## Testing approach

`tests/test_server.py` calls the `@mcp.tool()`-decorated functions directly
(bypassing the MCP transport/stdio layer entirely), since FastMCP's
decorator leaves the underlying function callable as-is. Follow this
pattern for new tests rather than spinning up a full MCP client/transport.

## Dependency notes

- `mcp` is pinned `>=2.0.0,<3.0.0`. The 2.0 line renamed
  `mcp.server.fastmcp.FastMCP` to `mcp.server.mcpserver.MCPServer` and moved
  transport selection to `run(transport=...)`; the `@mcp.tool()` decorator
  API itself is unchanged, so tool functions didn't need edits.
- `sqlfluff` is unpinned above `3.0.0` since only its stable `Linter` /
  `FluffConfig` API is used.

"""MCP server exposing SQLFluff's lint, fix, and parse capabilities.

Two families of tools are provided:

* ``*_file`` tools take a path on disk. Configuration is resolved the same
  way the ``sqlfluff`` CLI resolves it: by walking up from the file's
  directory looking for ``.sqlfluff``, ``pyproject.toml``, ``setup.cfg``,
  or ``tox.ini`` (via :meth:`sqlfluff.core.FluffConfig.from_path`).
* ``*_sql`` tools take SQL content directly (e.g. streamed from a client
  that hasn't written it to disk) and require an explicit ``dialect``,
  since there is no file location to resolve config from.

Both families can lint, fix, or parse.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlfluff.core import FluffConfig, Linter
from sqlfluff.core.errors import SQLFluffUserError

logger = logging.getLogger("sqlfluff_mcp")

mcp = FastMCP(
    name="sqlfluff",
    instructions=(
        "Lint, fix, and parse SQL using SQLFluff. Use the *_file tools when "
        "you have a path on disk so project .sqlfluff config is honored. "
        "Use the *_sql tools when you only have SQL text in hand and must "
        "specify a dialect explicitly."
    ),
)


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------


def _violations_to_dicts(violations: list[Any]) -> list[dict[str, Any]]:
    """Convert SQLFluff violation objects to plain JSON-serializable dicts."""
    out = []
    for v in violations:
        if hasattr(v, "to_dict"):
            out.append(v.to_dict())
        else:
            out.append({"description": str(v)})
    return out


def _config_for_path(path: Path, config_path: str | None) -> FluffConfig:
    """Resolve config by walking up from ``path``'s directory.

    Mirrors what the SQLFluff CLI does: looks for .sqlfluff / pyproject.toml
    / setup.cfg / tox.ini starting at the file's own directory and walking
    upward. ``config_path`` can point at an additional config file to layer
    on top (equivalent to the CLI's --config flag).
    """
    search_root = str(path if path.is_dir() else path.parent)
    return FluffConfig.from_path(search_root, extra_config_path=config_path)


def _config_for_dialect(dialect: str, rules: list[str] | None = None) -> FluffConfig:
    return FluffConfig.from_kwargs(dialect=dialect, rules=rules)


def _read_file(path_str: str) -> Path:
    path = Path(path_str).expanduser()
    if not path.is_file():
        raise SQLFluffUserError(f"No such file: {path}")
    return path


# --------------------------------------------------------------------------
# File-based tools (honor .sqlfluff config walking)
# --------------------------------------------------------------------------


@mcp.tool()
def lint_file(path: str, config_path: str | None = None) -> dict[str, Any]:
    """Lint a SQL file on disk, honoring any .sqlfluff / pyproject.toml config
    found by walking up from the file's directory.

    Args:
        path: Path to the SQL file to lint.
        config_path: Optional path to an extra config file to layer on top
            of whatever is discovered by walking the directory tree.
    """
    file_path = _read_file(path)
    config = _config_for_path(file_path, config_path)
    linter = Linter(config=config)
    result = linter.lint_string(file_path.read_text(encoding="utf-8"), fname=str(file_path))
    violations = _violations_to_dicts(result.get_violations())
    return {
        "path": str(file_path),
        "dialect": config.get("dialect"),
        "violation_count": len(violations),
        "violations": violations,
    }


@mcp.tool()
def fix_file(path: str, write: bool = False, config_path: str | None = None) -> dict[str, Any]:
    """Fix a SQL file on disk, honoring discovered .sqlfluff config.

    Args:
        path: Path to the SQL file to fix.
        write: If True, overwrite the file in place with the fixed SQL.
            If False (default), just return the fixed SQL without touching
            the file.
        config_path: Optional path to an extra config file to layer on top
            of whatever is discovered by walking the directory tree.
    """
    file_path = _read_file(path)
    config = _config_for_path(file_path, config_path)
    linter = Linter(config=config)
    original = file_path.read_text(encoding="utf-8")
    result = linter.lint_string(original, fname=str(file_path), fix=True)
    fixed_sql, _success = result.fix_string()

    if write and fixed_sql != original:
        file_path.write_text(fixed_sql, encoding="utf-8")

    return {
        "path": str(file_path),
        "dialect": config.get("dialect"),
        "changed": fixed_sql != original,
        "written": bool(write and fixed_sql != original),
        "fixed_sql": fixed_sql,
        "remaining_violations": _violations_to_dicts(result.get_violations()),
    }


@mcp.tool()
def parse_file(path: str, config_path: str | None = None) -> dict[str, Any]:
    """Parse a SQL file on disk and return its parse tree, honoring
    discovered .sqlfluff config.

    Args:
        path: Path to the SQL file to parse.
        config_path: Optional path to an extra config file to layer on top
            of whatever is discovered by walking the directory tree.
    """
    file_path = _read_file(path)
    config = _config_for_path(file_path, config_path)
    linter = Linter(config=config)
    parsed = linter.parse_string(file_path.read_text(encoding="utf-8"), fname=str(file_path))
    root_variant = parsed.root_variant()
    return {
        "path": str(file_path),
        "dialect": config.get("dialect"),
        "parse_tree": root_variant.tree.stringify() if root_variant else None,
        "parsing_violations": _violations_to_dicts(parsed.violations),
    }


# --------------------------------------------------------------------------
# Inline-content tools (streamed SQL text + explicit dialect)
# --------------------------------------------------------------------------


@mcp.tool()
def lint_sql(sql: str, dialect: str, rules: list[str] | None = None) -> dict[str, Any]:
    """Lint a raw SQL string using an explicitly specified dialect.

    Args:
        sql: The SQL text to lint.
        dialect: SQLFluff dialect name, e.g. "ansi", "bigquery", "snowflake",
            "postgres". See sqlfluff.list_dialects() for the full set.
        rules: Optional list of rule codes/names to restrict linting to.
    """
    config = _config_for_dialect(dialect, rules)
    linter = Linter(config=config)
    result = linter.lint_string(sql)
    violations = _violations_to_dicts(result.get_violations())
    return {
        "dialect": dialect,
        "violation_count": len(violations),
        "violations": violations,
    }


@mcp.tool()
def fix_sql(sql: str, dialect: str, rules: list[str] | None = None) -> dict[str, Any]:
    """Fix a raw SQL string using an explicitly specified dialect and return
    the fixed SQL text (does not touch any file).

    Args:
        sql: The SQL text to fix.
        dialect: SQLFluff dialect name, e.g. "ansi", "bigquery", "snowflake",
            "postgres".
        rules: Optional list of rule codes/names to restrict fixing to.
    """
    config = _config_for_dialect(dialect, rules)
    linter = Linter(config=config)
    result = linter.lint_string(sql, fix=True)
    fixed_sql, _success = result.fix_string()
    return {
        "dialect": dialect,
        "changed": fixed_sql != sql,
        "fixed_sql": fixed_sql,
        "remaining_violations": _violations_to_dicts(result.get_violations()),
    }


@mcp.tool()
def parse_sql(sql: str, dialect: str) -> dict[str, Any]:
    """Parse a raw SQL string using an explicitly specified dialect and
    return its parse tree.

    Args:
        sql: The SQL text to parse.
        dialect: SQLFluff dialect name, e.g. "ansi", "bigquery", "snowflake",
            "postgres".
    """
    config = _config_for_dialect(dialect)
    linter = Linter(config=config)
    parsed = linter.parse_string(sql)
    root_variant = parsed.root_variant()
    return {
        "dialect": dialect,
        "parse_tree": root_variant.tree.stringify() if root_variant else None,
        "parsing_violations": _violations_to_dicts(parsed.violations),
    }


@mcp.tool()
def list_dialects() -> list[dict[str, str]]:
    """List the SQL dialects SQLFluff supports (for use with lint_sql /
    fix_sql / parse_sql)."""
    import sqlfluff

    return [{"label": d.label, "name": d.name} for d in sqlfluff.list_dialects()]


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()

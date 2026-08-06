"""Smoke tests for the sqlfluff-mcp-server tool functions.

These call the tool functions directly (bypassing the MCP transport layer)
since FastMCP's @mcp.tool() decorator leaves the underlying function
callable as-is.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlfluff.core.errors import SQLFluffUserError

from sqlfluff_mcp.server import fix_file, fix_sql, lint_file, lint_sql, list_dialects, parse_sql

BAD_SQL = "select   1,2 from foo\n"


def test_lint_sql_finds_violations():
    result = lint_sql(BAD_SQL, dialect="ansi")
    assert result["violation_count"] > 0
    assert all("code" in v for v in result["violations"])


def test_fix_sql_returns_cleaned_sql():
    result = fix_sql(BAD_SQL, dialect="ansi")
    assert result["changed"] is True
    # LT09 puts each select target on its own line; LT01 fixes comma spacing.
    assert "1,\n    2" in result["fixed_sql"]


def test_parse_sql_returns_tree():
    result = parse_sql("SELECT 1\n", dialect="ansi")
    assert result["parse_tree"] is not None
    assert "select_statement" in result["parse_tree"]


def test_parse_sql_handles_templating_failure_gracefully():
    # Malformed Jinja produces zero successfully-parsed variants; this must
    # not raise, it should report parse_tree=None plus violations instead.
    result = parse_sql("select {% if %} 1 from foo", dialect="ansi")
    assert result["parse_tree"] is None
    assert len(result["parsing_violations"]) > 0


def test_list_dialects_includes_ansi():
    dialects = list_dialects()
    assert any(d["label"] == "ansi" for d in dialects)


def test_lint_file_honors_sqlfluff_config(tmp_path: Path):
    # A .sqlfluff file in the same directory should be picked up via
    # FluffConfig.from_path's directory walk, without us passing a dialect.
    (tmp_path / ".sqlfluff").write_text("[sqlfluff]\ndialect = ansi\n", encoding="utf-8")
    sql_file = tmp_path / "query.sql"
    sql_file.write_text(BAD_SQL, encoding="utf-8")

    result = lint_file(str(sql_file))

    assert result["dialect"] == "ansi"
    assert result["violation_count"] > 0


def test_fix_file_write_flag(tmp_path: Path):
    (tmp_path / ".sqlfluff").write_text("[sqlfluff]\ndialect = ansi\n", encoding="utf-8")
    sql_file = tmp_path / "query.sql"
    sql_file.write_text(BAD_SQL, encoding="utf-8")

    result = fix_file(str(sql_file), write=True)

    assert result["written"] is True
    assert sql_file.read_text(encoding="utf-8") == result["fixed_sql"]


def test_lint_file_missing_file_raises(tmp_path: Path):
    with pytest.raises(SQLFluffUserError):
        lint_file(str(tmp_path / "does_not_exist.sql"))

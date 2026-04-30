"""Tests for CLI help output and command structure.
# spec: ticket-lifecycle ticket-relationships ticket-fields ticket-content ticket-query
"""
from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


# spec: ticket-lifecycle requirement=create-ticket
# spec: ticket-relationships requirement=add-dependency
# spec: ticket-query requirement=list-tickets
class TestHelpSections:
    """Help output is organized into named sections."""

    def test_top_level_help_shows_sections(self) -> None:
        result = run_tq("--help")
        assert result.returncode == 0
        output = result.stdout
        for section in ["View", "Lifecycle", "Relationships", "Fields", "Content"]:
            assert section in output, f"Missing section '{section}' in help output"

    def test_top_level_help_shows_description(self) -> None:
        result = run_tq("--help")
        assert "minimal ticket system" in result.stdout.lower()

    def test_top_level_help_lists_all_commands(self) -> None:
        result = run_tq("--help")
        output = result.stdout
        commands = [
            "create", "start", "close", "cancel", "reopen",
            "dep", "undep", "nest", "unnest", "link", "unlink",
            "assign", "change-prio", "change-type",
            "tag", "untag", "xref",
            "describe", "add-note",
            "show", "info", "path", "deps", "ls", "tags", "links", "archive",
        ]
        for cmd in commands:
            assert cmd in output, f"Command '{cmd}' missing from help output"


class TestCommandHelp:
    """Each command has its own --help with argument descriptions."""

    def test_create_help(self) -> None:
        result = run_tq("create", "--help")
        assert result.returncode == 0
        for flag in ["-d", "--description", "-t", "--type", "-p", "--priority",
                     "-A", "--assignee", "--xref", "--parent", "--tag", "--dep"]:
            assert flag in result.stdout, f"Flag '{flag}' missing from create help"

    def test_ls_help(self) -> None:
        result = run_tq("ls", "--help")
        assert result.returncode == 0
        for flag in ["--status", "--ready", "--blocked", "--completed",
                     "--canceled", "--assignee", "--tag", "--type",
                     "--sort", "--limit", "--jsonl"]:
            assert flag in result.stdout, f"Flag '{flag}' missing from ls help"

    def test_show_help(self) -> None:
        result = run_tq("show", "--help")
        assert result.returncode == 0
        assert "--json" in result.stdout

    def test_info_help(self) -> None:
        result = run_tq("info", "--help")
        assert result.returncode == 0
        assert "--json" in result.stdout

    def test_show_deps_help(self) -> None:
        result = run_tq("deps", "--help")
        assert result.returncode == 0
        assert "--full" in result.stdout

    def test_nest_help(self) -> None:
        result = run_tq("nest", "--help")
        assert result.returncode == 0
        assert "parent" in result.stdout.lower()

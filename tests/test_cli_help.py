"""Tests for CLI help output matching the v1.2 spec.

Ground truth: docs/cli-design-v1.2.md (NOT the current implementation).
These tests are intentionally written to the v1.2 spec and WILL FAIL
against the pre-v1.2 implementation.

# spec: ticket-lifecycle ticket-edit ticket-query
"""

from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


class TestHelpSections:
    """Top-level help is organized into v1.2 sections."""

    def test_top_level_help_exits_zero(self) -> None:
        result = run_tq("--help")
        assert result.returncode == 0

    def test_top_level_help_shows_description(self) -> None:
        result = run_tq("--help")
        assert "minimal ticket system" in result.stdout.lower()

    def test_help_has_frequently_used_section(self) -> None:
        result = run_tq("--help")
        assert "Frequently Used" in result.stdout

    def test_help_has_commands_section(self) -> None:
        result = run_tq("--help")
        assert "Commands" in result.stdout

    def test_help_has_lifecycle_section(self) -> None:
        result = run_tq("--help")
        assert "Lifecycle" in result.stdout

    def test_help_has_view_section(self) -> None:
        result = run_tq("--help")
        assert "View" in result.stdout

    def test_help_has_maintenance_section(self) -> None:
        result = run_tq("--help")
        assert "Maintenance" in result.stdout

    def test_help_has_examples_section(self) -> None:
        result = run_tq("--help")
        assert "Examples" in result.stdout

    def test_old_relationships_section_absent(self) -> None:
        result = run_tq("--help")
        # v1.2 collapses Relationships, Fields, Content into edit
        assert "Relationships" not in result.stdout

    def test_old_fields_section_absent(self) -> None:
        result = run_tq("--help")
        assert "Fields" not in result.stdout

    def test_old_content_section_absent(self) -> None:
        result = run_tq("--help")
        assert "Content" not in result.stdout


class TestHelpCommands:
    """v1.2 commands appear; removed verbs do not."""

    def test_create_in_help(self) -> None:
        result = run_tq("--help")
        assert "create" in result.stdout

    def test_edit_in_help(self) -> None:
        result = run_tq("--help")
        assert "edit" in result.stdout

    def test_start_in_help(self) -> None:
        result = run_tq("--help")
        assert "start" in result.stdout

    def test_close_in_help(self) -> None:
        result = run_tq("--help")
        assert "close" in result.stdout

    def test_cancel_in_help(self) -> None:
        result = run_tq("--help")
        assert "cancel" in result.stdout

    def test_reopen_in_help(self) -> None:
        result = run_tq("--help")
        assert "reopen" in result.stdout

    def test_archive_in_help(self) -> None:
        result = run_tq("--help")
        assert "archive" in result.stdout

    def test_ls_in_help(self) -> None:
        result = run_tq("--help")
        assert "ls" in result.stdout

    def test_show_in_help(self) -> None:
        result = run_tq("--help")
        assert "show" in result.stdout

    def test_info_in_help(self) -> None:
        result = run_tq("--help")
        assert "info" in result.stdout

    def test_path_in_help(self) -> None:
        result = run_tq("--help")
        assert "path" in result.stdout

    def test_deps_in_help(self) -> None:
        result = run_tq("--help")
        assert "deps" in result.stdout

    def test_links_in_help(self) -> None:
        result = run_tq("--help")
        assert "links" in result.stdout

    def test_tags_in_help(self) -> None:
        result = run_tq("--help")
        assert "tags" in result.stdout

    def test_validate_in_help(self) -> None:
        result = run_tq("--help")
        assert "validate" in result.stdout

    def test_autofix_in_help(self) -> None:
        result = run_tq("--help")
        assert "autofix" in result.stdout

    # Removed verbs must not appear
    def test_tag_verb_absent(self) -> None:
        result = run_tq("--help")
        # "tag" appears in --tag flag descriptions, so we check for
        # "  tag " (indented as a command) not just the substring
        # The removed standalone verb was listed as a top-level command;
        # in v1.2 it should not be listed as a command.
        lines = result.stdout.splitlines()
        command_lines = [
            l for l in lines if l.startswith("  ") and not l.startswith("   ")
        ]
        # No line should start with "  tag " as a standalone command entry
        assert not any(l.strip().startswith("tag ") for l in command_lines), (
            "removed 'tag' verb should not appear as a command"
        )

    def test_untag_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(l.strip().startswith("untag ") for l in lines), (
            "removed 'untag' verb should not appear as a command"
        )

    def test_dep_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(
            l.strip() == "dep" or l.strip().startswith("dep ") for l in lines
        ), "removed 'dep' verb should not appear as a command"

    def test_undep_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(l.strip().startswith("undep ") for l in lines)

    def test_nest_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(
            l.strip() == "nest" or l.strip().startswith("nest ") for l in lines
        )

    def test_unnest_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(l.strip().startswith("unnest ") for l in lines)

    def test_link_verb_absent(self) -> None:
        """The standalone 'link' command is removed; --link flag on edit is still present."""
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        # Must not appear as a top-level command (two-space indent, not under edit's flags)
        command_level = [
            l for l in lines if l.startswith("  ") and not l.startswith("   ")
        ]
        assert not any(
            l.strip() == "link" or l.strip().startswith("link ") for l in command_level
        )

    def test_unlink_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        command_level = [
            l for l in lines if l.startswith("  ") and not l.startswith("   ")
        ]
        assert not any(l.strip().startswith("unlink ") for l in command_level)

    def test_assign_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(
            l.strip() == "assign" or l.strip().startswith("assign ") for l in lines
        )

    def test_change_prio_absent(self) -> None:
        result = run_tq("--help")
        assert "change-prio" not in result.stdout

    def test_change_type_absent(self) -> None:
        result = run_tq("--help")
        assert "change-type" not in result.stdout

    def test_describe_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        assert not any(
            l.strip() == "describe" or l.strip().startswith("describe ") for l in lines
        )

    def test_add_note_verb_absent(self) -> None:
        result = run_tq("--help")
        assert "add-note" not in result.stdout

    def test_xref_verb_absent(self) -> None:
        result = run_tq("--help")
        lines = result.stdout.splitlines()
        # xref appears as a flag name (--xref) but NOT as a standalone command
        assert not any(
            l.strip() == "xref" or l.strip().startswith("xref ") for l in lines
        )


class TestHelpStatusVocabulary:
    """Help uses 'closed' (not 'completed') as the terminal status name."""

    def test_closed_appears_in_help(self) -> None:
        result = run_tq("--help")
        assert "closed" in result.stdout

    def test_completed_not_used_as_status_name(self) -> None:
        result = run_tq("--help")
        # 'completed' must not appear as a status value description
        assert "completed" not in result.stdout

    def test_close_describes_closed_status(self) -> None:
        result = run_tq("--help")
        # The close command description must say "closed"
        assert (
            "status to closed" in result.stdout
            or "Set status to closed" in result.stdout
        )


class TestEditHelp:
    """edit subcommand help reflects v1.2 field-flag vocabulary."""

    def test_edit_help_exits_zero(self) -> None:
        result = run_tq("edit", "--help")
        assert result.returncode == 0

    def test_edit_help_has_title_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--title" in result.stdout

    def test_edit_help_has_untag_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--untag" in result.stdout

    def test_edit_help_has_undep_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--undep" in result.stdout

    def test_edit_help_has_unlink_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--unlink" in result.stdout

    def test_edit_help_has_unset_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--unset" in result.stdout

    def test_edit_help_has_description_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--description" in result.stdout or "-d" in result.stdout

    def test_edit_help_has_tag_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--tag" in result.stdout

    def test_edit_help_has_dep_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--dep" in result.stdout

    def test_edit_help_has_link_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--link" in result.stdout

    def test_edit_help_has_note_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--note" in result.stdout

    def test_edit_help_has_parent_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--parent" in result.stdout

    def test_edit_help_has_priority_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--priority" in result.stdout or "-p" in result.stdout

    def test_edit_help_has_type_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--type" in result.stdout or "-t" in result.stdout

    def test_edit_help_has_assignee_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--assignee" in result.stdout or "-A" in result.stdout

    def test_edit_help_has_xref_flag(self) -> None:
        result = run_tq("edit", "--help")
        assert "--xref" in result.stdout


class TestCreateHelp:
    """create subcommand help: title is required positional, gains --link and --note."""

    def test_create_help_exits_zero(self) -> None:
        result = run_tq("create", "--help")
        assert result.returncode == 0

    def test_create_help_has_link_flag(self) -> None:
        result = run_tq("create", "--help")
        assert "--link" in result.stdout

    def test_create_help_has_note_flag(self) -> None:
        result = run_tq("create", "--help")
        assert "--note" in result.stdout

    def test_create_help_has_all_shared_flags(self) -> None:
        result = run_tq("create", "--help")
        for flag in [
            "-d",
            "--description",
            "-t",
            "--type",
            "-p",
            "--priority",
            "-A",
            "--assignee",
            "--xref",
            "--parent",
            "--tag",
            "--dep",
        ]:
            assert flag in result.stdout, f"Flag '{flag}' missing from create help"


class TestLsHelp:
    """ls subcommand help uses 'closed' in --status choices; no -T short."""

    def test_ls_help_exits_zero(self) -> None:
        result = run_tq("ls", "--help")
        assert result.returncode == 0

    def test_ls_help_shows_closed_in_status_choices(self) -> None:
        result = run_tq("ls", "--help")
        assert "closed" in result.stdout

    def test_ls_help_no_T_short_for_tag(self) -> None:
        result = run_tq("ls", "--help")
        # -T was removed in v1.2; --tag is the only form
        assert "-T" not in result.stdout

    def test_ls_help_has_all_filters(self) -> None:
        result = run_tq("ls", "--help")
        for flag in [
            "--status",
            "--ready",
            "--blocked",
            "--assignee",
            "--tag",
            "--type",
            "--sort",
            "--limit",
            "--jsonl",
        ]:
            assert flag in result.stdout, f"Flag '{flag}' missing from ls help"


class TestRemovedCommandsAreGone:
    """Removed verbs are rejected by argparse, not aliased."""

    def test_tag_command_rejected(self) -> None:
        result = run_tq("tag", "t-001", "foo")
        assert result.returncode != 0

    def test_untag_command_rejected(self) -> None:
        result = run_tq("untag", "t-001", "foo")
        assert result.returncode != 0

    def test_dep_command_rejected(self) -> None:
        result = run_tq("dep", "t-001", "t-002")
        assert result.returncode != 0

    def test_undep_command_rejected(self) -> None:
        result = run_tq("undep", "t-001", "t-002")
        assert result.returncode != 0

    def test_nest_command_rejected(self) -> None:
        result = run_tq("nest", "t-001", "p-001")
        assert result.returncode != 0

    def test_unnest_command_rejected(self) -> None:
        result = run_tq("unnest", "t-001")
        assert result.returncode != 0

    def test_link_command_rejected(self) -> None:
        result = run_tq("link", "t-001", "t-002")
        assert result.returncode != 0

    def test_unlink_command_rejected(self) -> None:
        result = run_tq("unlink", "t-001", "t-002")
        assert result.returncode != 0

    def test_assign_command_rejected(self) -> None:
        result = run_tq("assign", "t-001", "Alice")
        assert result.returncode != 0

    def test_change_prio_command_rejected(self) -> None:
        result = run_tq("change-prio", "t-001", "1")
        assert result.returncode != 0

    def test_change_type_command_rejected(self) -> None:
        result = run_tq("change-type", "t-001", "bug")
        assert result.returncode != 0

    def test_describe_command_rejected(self) -> None:
        result = run_tq("describe", "t-001", "body")
        assert result.returncode != 0

    def test_add_note_command_rejected(self) -> None:
        result = run_tq("add-note", "t-001", "note text")
        assert result.returncode != 0

    def test_xref_command_rejected(self) -> None:
        result = run_tq("xref", "t-001", "gh-1")
        assert result.returncode != 0

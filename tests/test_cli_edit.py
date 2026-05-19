"""Tests for `tq edit` -- the consolidated post-creation mutation surface.
# spec: ticket-edit
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tiquette.store import Ticket, read_ticket, write_ticket


def run_tq(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
        env=run_env,
    )


def _make_dir(tmp_path: Path, name: str = "tickets") -> Path:
    td = tmp_path / name
    td.mkdir(parents=True, exist_ok=True)
    return td


def _write(td: Path, ticket: Ticket) -> None:
    write_ticket(ticket, td)


def _read(td: Path, tid: str) -> Ticket:
    return read_ticket(tid, td)


def _content(td: Path, tid: str) -> str:
    return (td / f"{tid}.md").read_text()


# ---------------------------------------------------------------------------
# Requirement: Edit command
# ---------------------------------------------------------------------------

class TestEditCommand:
    """tq edit <id> [field-options] is the single mutation surface.
    # spec: ticket-edit requirement=edit-command
    """

    # spec: ticket-edit requirement=edit-command scenario=edit-changes-a-single-field
    def test_single_field_change(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-001", title="Fixture", priority=2))
        result = run_tq("edit", "edit-001", "-p", "0", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-001").priority == 0

    # spec: ticket-edit requirement=edit-command scenario=edit-changes-multiple-fields-in-one-call
    def test_multiple_fields_in_one_call(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-001", title="Fixture", priority=2, assignee="Alice"))
        result = run_tq(
            "edit", "edit-001",
            "-p", "0", "-A", "Bob", "--tag", "urgent",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-001")
        assert t.priority == 0
        assert t.assignee == "Bob"
        assert "urgent" in t.tags

    # spec: ticket-edit requirement=edit-command scenario=edit-with-no-flags-is-an-error
    def test_no_flags_exits_nonzero(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-001", title="Fixture"))
        result = run_tq("edit", "edit-001", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert result.stderr  # some message about needing at least one field-option

    # spec: ticket-edit requirement=edit-command scenario=edit-on-missing-id
    def test_missing_id_exits_nonzero(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        result = run_tq("edit", "nonexistent", "-p", "0", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "not found" in result.stderr.lower()

    def test_edit_subcommand_exists(self, tmp_path: Path) -> None:
        """edit must be a recognised subcommand (not 'invalid choice')."""
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-001", title="Fixture"))
        result = run_tq("edit", "edit-001", "-p", "1", env={"TICKETS_DIR": str(td)})
        # We don't want argparse "invalid choice: 'edit'" error
        assert "invalid choice" not in result.stderr
        assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Requirement: Rename via --title
# ---------------------------------------------------------------------------

class TestTitle:
    """--title renames the ticket title while keeping the id.
    # spec: ticket-edit requirement=rename-via---title
    """

    # spec: ticket-edit requirement=rename-via---title scenario=rename-a-ticket
    def test_rename_changes_title(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-002", title="Old title"))
        result = run_tq("edit", "edit-002", "--title", "New title", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-002")
        assert t.title == "New title"

    # spec: ticket-edit requirement=rename-via---title scenario=rename-a-ticket
    def test_rename_preserves_id(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-002", title="Old title"))
        run_tq("edit", "edit-002", "--title", "New title", env={"TICKETS_DIR": str(td)})
        t = _read(td, "edit-002")
        assert t.id == "edit-002"


# ---------------------------------------------------------------------------
# Requirement: Description replace via --description
# ---------------------------------------------------------------------------

class TestDescription:
    """--description replaces the body; last value wins on repetition.
    # spec: ticket-edit requirement=description-replace-via---description
    """

    # spec: ticket-edit requirement=description-replace-via---description scenario=replace-description
    def test_replace_description(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-003", title="Fixture", description="old body"))
        result = run_tq("edit", "edit-003", "-d", "new body", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        content = _content(td, "edit-003")
        assert "new body" in content
        assert "old body" not in content

    # spec: ticket-edit requirement=description-replace-via---description scenario=last---description-wins
    def test_last_description_wins(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-003", title="Fixture"))
        result = run_tq(
            "edit", "edit-003", "-d", "first", "-d", "second",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        content = _content(td, "edit-003")
        assert "second" in content
        assert "first" not in content


# ---------------------------------------------------------------------------
# Requirement: Notes append via --note
# ---------------------------------------------------------------------------

class TestNotes:
    """--note appends a timestamped note; all notes in one call share a timestamp.
    # spec: ticket-edit requirement=notes-append-via---note
    """

    # spec: ticket-edit requirement=notes-append-via---note scenario=single-note
    def test_single_note_appended(self, tmp_path: Path) -> None:
        import re
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-004", title="Fixture"))
        result = run_tq("edit", "edit-004", "--note", "kickoff", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        content = _content(td, "edit-004")
        assert "## Notes" in content
        assert "kickoff" in content
        # ISO 8601 timestamp check (basic: contains a date-like pattern)
        assert re.search(r"\d{4}-\d{2}-\d{2}", content)

    # spec: ticket-edit requirement=notes-append-via---note scenario=multiple-notes-share-a-timestamp
    def test_multiple_notes_share_timestamp(self, tmp_path: Path) -> None:
        import re
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-004", title="Fixture"))
        result = run_tq(
            "edit", "edit-004", "--note", "first", "--note", "second",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        content = _content(td, "edit-004")
        assert "first" in content
        assert "second" in content
        # Both notes appear; extract timestamps to verify they share one
        timestamps = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", content)
        assert len(timestamps) >= 2
        assert len(set(timestamps)) == 1, f"Expected one shared timestamp, got {set(timestamps)}"

    # spec: ticket-edit requirement=notes-append-via---note scenario=multiple-notes-share-a-timestamp
    def test_multiple_notes_appear_in_order(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-004", title="Fixture"))
        run_tq("edit", "edit-004", "--note", "first", "--note", "second",
               env={"TICKETS_DIR": str(td)})
        content = _content(td, "edit-004")
        assert content.index("first") < content.index("second")


# ---------------------------------------------------------------------------
# Requirement: Tag add/remove
# ---------------------------------------------------------------------------

class TestTagAddRemove:
    """--tag adds, --untag removes; both idempotent and repeatable.
    # spec: ticket-edit requirement=tag-add/remove
    """

    # spec: ticket-edit requirement=tag-add/remove scenario=add-and-remove-tags-in-one-call
    def test_add_and_remove_tags(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-005", title="Fixture", tags=["stale", "backend"]))
        result = run_tq(
            "edit", "edit-005", "--tag", "urgent", "--untag", "stale",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-005")
        assert "urgent" in t.tags
        assert "backend" in t.tags
        assert "stale" not in t.tags

    # spec: ticket-edit requirement=tag-add/remove scenario=re-adding-a-tag-is-a-no-op
    def test_readding_tag_is_noop(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-005", title="Fixture", tags=["urgent"]))
        result = run_tq("edit", "edit-005", "--tag", "urgent", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-005")
        assert t.tags.count("urgent") == 1

    # spec: ticket-edit requirement=tag-add/remove
    def test_removing_absent_tag_is_noop(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-005", title="Fixture", tags=["backend"]))
        result = run_tq("edit", "edit-005", "--untag", "nothere", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-005")
        assert "backend" in t.tags

    # spec: ticket-edit requirement=tag-add/remove
    def test_multiple_tag_flags(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-005", title="Fixture", tags=[]))
        result = run_tq(
            "edit", "edit-005", "--tag", "alpha", "--tag", "beta",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-005")
        assert "alpha" in t.tags
        assert "beta" in t.tags


# ---------------------------------------------------------------------------
# Requirement: Dependency add/remove
# ---------------------------------------------------------------------------

class TestDepAddRemove:
    """--dep adds, --undep removes; cycles rejected.
    # spec: ticket-edit requirement=dependency-add/remove
    """

    # spec: ticket-edit requirement=dependency-add/remove scenario=add-and-remove-deps-in-one-call
    def test_add_and_remove_deps(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-006", title="Fixture", deps=["edit-006a"]))
        _write(td, Ticket(id="edit-006a", title="Dep A"))
        _write(td, Ticket(id="edit-006b", title="Dep B"))
        result = run_tq(
            "edit", "edit-006", "--dep", "edit-006b", "--undep", "edit-006a",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-006")
        assert "edit-006b" in t.deps
        assert "edit-006a" not in t.deps

    # spec: ticket-edit requirement=dependency-add/remove scenario=add-dep-that-would-cycle-is-rejected
    def test_dep_cycle_rejected(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-006", title="Fixture", deps=["edit-006b"]))
        _write(td, Ticket(id="edit-006b", title="Dep B"))
        result = run_tq("edit", "edit-006b", "--dep", "edit-006", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        stderr_lower = result.stderr.lower()
        assert "cycle" in stderr_lower or "circular" in stderr_lower or "loop" in stderr_lower

    # spec: ticket-edit requirement=dependency-add/remove
    def test_removing_absent_dep_is_noop(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-006", title="Fixture", deps=["edit-006a"]))
        _write(td, Ticket(id="edit-006a", title="Dep A"))
        result = run_tq("edit", "edit-006", "--undep", "nothere", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-006")
        assert "edit-006a" in t.deps


# ---------------------------------------------------------------------------
# Requirement: Link add/remove
# ---------------------------------------------------------------------------

class TestLinkAddRemove:
    """--link adds symmetrically, --unlink removes symmetrically.
    # spec: ticket-edit requirement=link-add/remove
    """

    # spec: ticket-edit requirement=link-add/remove scenario=link-is-symmetric
    def test_link_is_symmetric(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-007", title="A"))
        _write(td, Ticket(id="edit-007b", title="B"))
        result = run_tq("edit", "edit-007", "--link", "edit-007b", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert "edit-007b" in _read(td, "edit-007").links
        assert "edit-007" in _read(td, "edit-007b").links

    # spec: ticket-edit requirement=link-add/remove scenario=unlink-is-symmetric
    def test_unlink_is_symmetric(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-007", title="A", links=["edit-007b"]))
        _write(td, Ticket(id="edit-007b", title="B", links=["edit-007"]))
        result = run_tq("edit", "edit-007", "--unlink", "edit-007b", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert "edit-007b" not in _read(td, "edit-007").links
        assert "edit-007" not in _read(td, "edit-007b").links

    # spec: ticket-edit requirement=link-add/remove
    def test_link_multiple_targets(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-007", title="A"))
        _write(td, Ticket(id="edit-007b", title="B"))
        _write(td, Ticket(id="edit-007c", title="C"))
        result = run_tq(
            "edit", "edit-007", "--link", "edit-007b", "--link", "edit-007c",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-007")
        assert "edit-007b" in t.links
        assert "edit-007c" in t.links


# ---------------------------------------------------------------------------
# Requirement: Parent set via --parent
# ---------------------------------------------------------------------------

class TestParentSet:
    """--parent sets parent; cycle rejected.
    # spec: ticket-edit requirement=parent-set-via---parent
    """

    # spec: ticket-edit requirement=parent-set-via---parent scenario=re-parent-a-ticket
    def test_reparent(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-008", title="Child", parent="edit-008a"))
        _write(td, Ticket(id="edit-008a", title="Old parent"))
        _write(td, Ticket(id="edit-008b", title="New parent"))
        result = run_tq("edit", "edit-008", "--parent", "edit-008b", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-008").parent == "edit-008b"

    # spec: ticket-edit requirement=parent-set-via---parent scenario=parent-assignment-that-would-cycle-is-rejected
    def test_parent_cycle_rejected(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-008", title="Parent"))
        _write(td, Ticket(id="edit-008c", title="Child", parent="edit-008"))
        result = run_tq("edit", "edit-008", "--parent", "edit-008c", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        stderr_lower = result.stderr.lower()
        assert "cycle" in stderr_lower or "circular" in stderr_lower or "ancestor" in stderr_lower


# ---------------------------------------------------------------------------
# Requirement: Single-value field clear via --unset
# ---------------------------------------------------------------------------

class TestUnset:
    """--unset clears single-value fields; --unset description is rejected.
    # spec: ticket-edit requirement=single-value-field-clear-via---unset
    """

    # spec: ticket-edit requirement=single-value-field-clear-via---unset scenario=clear-assignee
    def test_unset_assignee(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture", assignee="Alice"))
        result = run_tq("edit", "edit-009", "--unset", "assignee", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-009")
        assert t.assignee is None

    # spec: ticket-edit requirement=single-value-field-clear-via---unset scenario=clear-multiple-fields-in-one-call
    def test_unset_multiple_fields(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture", assignee="Alice", xref="gh-1"))
        result = run_tq(
            "edit", "edit-009", "--unset", "assignee", "--unset", "xref",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-009")
        assert t.assignee is None
        assert t.xref is None

    # spec: ticket-edit requirement=single-value-field-clear-via---unset scenario=--unset-description-is-rejected
    def test_unset_description_rejected(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture"))
        result = run_tq("edit", "edit-009", "--unset", "description", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()

    # spec: ticket-edit requirement=single-value-field-clear-via---unset scenario=--unset-on-an-already-empty-field-is-a-no-op
    def test_unset_already_empty_is_noop(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture", assignee=None))
        result = run_tq("edit", "edit-009", "--unset", "assignee", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-009").assignee is None

    # spec: ticket-edit requirement=single-value-field-clear-via---unset
    def test_unset_parent(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture", parent="edit-009a"))
        _write(td, Ticket(id="edit-009a", title="Parent"))
        result = run_tq("edit", "edit-009", "--unset", "parent", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-009").parent is None

    # spec: ticket-edit requirement=single-value-field-clear-via---unset
    def test_unset_xref(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture", xref="gh-99"))
        result = run_tq("edit", "edit-009", "--unset", "xref", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-009").xref is None

    # spec: ticket-edit requirement=single-value-field-clear-via---unset
    def test_unset_invalid_field_rejected(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-009", title="Fixture"))
        result = run_tq("edit", "edit-009", "--unset", "title", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Requirement: Set/unset conflict
# ---------------------------------------------------------------------------

class TestSetUnsetConflict:
    """Setting and unsetting the same field in one call is an error.
    # spec: ticket-edit requirement=set/unset-conflict
    """

    # spec: ticket-edit requirement=set/unset-conflict scenario=setting-and-unsetting-the-same-field-is-rejected
    def test_set_and_unset_same_field_rejected(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-010", title="Fixture", assignee="Original"))
        result = run_tq(
            "edit", "edit-010", "-A", "Bob", "--unset", "assignee",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode != 0

    # spec: ticket-edit requirement=set/unset-conflict scenario=setting-and-unsetting-the-same-field-is-rejected
    def test_conflict_stderr_names_field(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-010", title="Fixture", assignee="Original"))
        result = run_tq(
            "edit", "edit-010", "-A", "Bob", "--unset", "assignee",
            env={"TICKETS_DIR": str(td)},
        )
        assert "assignee" in result.stderr

    # spec: ticket-edit requirement=set/unset-conflict scenario=setting-and-unsetting-the-same-field-is-rejected
    def test_conflict_ticket_unchanged(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-010", title="Fixture", assignee="Original"))
        run_tq(
            "edit", "edit-010", "-A", "Bob", "--unset", "assignee",
            env={"TICKETS_DIR": str(td)},
        )
        # ticket must be unchanged
        t = _read(td, "edit-010")
        assert t.assignee == "Original"

    # spec: ticket-edit requirement=set/unset-conflict
    def test_set_and_unset_parent_conflict(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-010", title="Fixture"))
        _write(td, Ticket(id="edit-010p", title="Parent"))
        result = run_tq(
            "edit", "edit-010", "--parent", "edit-010p", "--unset", "parent",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode != 0
        assert "parent" in result.stderr

    # spec: ticket-edit requirement=set/unset-conflict
    def test_set_and_unset_xref_conflict(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-010", title="Fixture"))
        result = run_tq(
            "edit", "edit-010", "--xref", "gh-1", "--unset", "xref",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode != 0
        assert "xref" in result.stderr


# ---------------------------------------------------------------------------
# Requirement: Type and priority via --type / --priority
# ---------------------------------------------------------------------------

class TestTypeAndPriority:
    """--type and --priority set those fields.
    # spec: ticket-edit requirement=type-and-priority-via---type-/---priority
    """

    # spec: ticket-edit requirement=type-and-priority-via---type-/---priority scenario=change-type
    def test_change_type(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-011", title="Fixture", type="task"))
        result = run_tq("edit", "edit-011", "-t", "bug", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-011").type == "bug"

    # spec: ticket-edit requirement=type-and-priority-via---type-/---priority scenario=change-priority
    def test_change_priority(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-011", title="Fixture", priority=2))
        result = run_tq("edit", "edit-011", "-p", "0", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-011").priority == 0

    # spec: ticket-edit requirement=type-and-priority-via---type-/---priority
    def test_long_flags(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-011", title="Fixture"))
        result = run_tq(
            "edit", "edit-011", "--type", "feature", "--priority", "1",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode == 0, result.stderr
        t = _read(td, "edit-011")
        assert t.type == "feature"
        assert t.priority == 1


# ---------------------------------------------------------------------------
# Requirement: External reference via --xref
# ---------------------------------------------------------------------------

class TestXref:
    """--xref sets the external reference field.
    # spec: ticket-edit requirement=external-reference-via---xref
    """

    # spec: ticket-edit requirement=external-reference-via---xref scenario=set-external-reference
    def test_set_xref(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-012", title="Fixture"))
        result = run_tq("edit", "edit-012", "--xref", "gh-42", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-012").xref == "gh-42"

    # spec: ticket-edit requirement=external-reference-via---xref
    def test_clear_xref_via_unset(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-012", title="Fixture", xref="old-ref"))
        result = run_tq("edit", "edit-012", "--unset", "xref", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert _read(td, "edit-012").xref is None


# ---------------------------------------------------------------------------
# Requirement: Atomicity
# ---------------------------------------------------------------------------

class TestAtomicity:
    """All changes apply atomically; a validation failure leaves files unchanged.
    # spec: ticket-edit requirement=atomicity
    """

    # spec: ticket-edit requirement=atomicity scenario=failed-dep-target-leaves-ticket-unchanged
    def test_failed_dep_leaves_ticket_unchanged(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-013", title="Fixture", priority=2))
        result = run_tq(
            "edit", "edit-013", "-p", "0", "--dep", "nonexistent",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode != 0
        # priority must still be 2
        assert _read(td, "edit-013").priority == 2

    # spec: ticket-edit requirement=atomicity
    def test_cycle_rejection_leaves_ticket_unchanged(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="edit-013", title="A", deps=["edit-013b"], priority=2))
        _write(td, Ticket(id="edit-013b", title="B"))
        result = run_tq(
            "edit", "edit-013b", "--dep", "edit-013", "-p", "0",
            env={"TICKETS_DIR": str(td)},
        )
        assert result.returncode != 0
        # edit-013b priority must be unchanged
        assert _read(td, "edit-013b").priority == 2


# ---------------------------------------------------------------------------
# Requirement: Partial ID resolution applies to field-option values
# spec: id-resolution requirement=id-resolution-across-commands
# ---------------------------------------------------------------------------

class TestPartialIDOnFieldValues:
    """`tq edit` and `tq create` must resolve partial IDs in the *values* of
    --dep, --link, --parent (and --undep, --unlink), not only in the subject
    <id>. Regression coverage for a bug where these checked exact filenames
    only.
    """

    # spec: id-resolution requirement=id-resolution-across-commands scenario=partial-id-with-edit-dep
    def test_edit_dep_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-aaaa", title="Subject"))
        _write(td, Ticket(id="part-bbbb", title="Target"))
        r = run_tq("edit", "aaaa", "--dep", "bbbb", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-aaaa").deps == ["part-bbbb"]

    # spec: id-resolution requirement=id-resolution-across-commands scenario=partial-id-with-edit-link
    def test_edit_link_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-cccc", title="Subject"))
        _write(td, Ticket(id="part-dddd", title="Target"))
        r = run_tq("edit", "cccc", "--link", "dddd", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-cccc").links == ["part-dddd"]
        # symmetric
        assert _read(td, "part-dddd").links == ["part-cccc"]

    def test_edit_parent_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-eeee", title="Child"))
        _write(td, Ticket(id="part-ffff", title="Parent"))
        r = run_tq("edit", "eeee", "--parent", "ffff", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-eeee").parent == "part-ffff"

    def test_edit_undep_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-gggg", title="Subject", deps=["part-hhhh"]))
        _write(td, Ticket(id="part-hhhh", title="Target"))
        r = run_tq("edit", "gggg", "--undep", "hhhh", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-gggg").deps == []

    def test_edit_unlink_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-iiii", title="A", links=["part-jjjj"]))
        _write(td, Ticket(id="part-jjjj", title="B", links=["part-iiii"]))
        r = run_tq("edit", "iiii", "--unlink", "jjjj", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-iiii").links == []
        assert _read(td, "part-jjjj").links == []

    def test_create_dep_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-kkkk", title="Target"))
        r = run_tq(
            "create", "New ticket", "--dep", "kkkk",
            env={"TICKETS_DIR": str(td)},
        )
        assert r.returncode == 0, r.stderr
        new_id = r.stdout.strip()
        assert _read(td, new_id).deps == ["part-kkkk"]

    def test_create_parent_accepts_partial(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-llll", title="Parent"))
        r = run_tq(
            "create", "Child ticket", "--parent", "llll",
            env={"TICKETS_DIR": str(td)},
        )
        assert r.returncode == 0, r.stderr
        new_id = r.stdout.strip()
        assert _read(td, new_id).parent == "part-llll"

    def test_edit_dep_unresolved_partial_errors(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-mmmm", title="Subject"))
        r = run_tq("edit", "mmmm", "--dep", "nope", env={"TICKETS_DIR": str(td)})
        assert r.returncode != 0
        assert "not found" in r.stderr

    def test_edit_undep_ambiguous_partial_errors(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-aa11", title="Subject", deps=["part-aa22", "part-aa33"]))
        _write(td, Ticket(id="part-aa22", title="Dep A"))
        _write(td, Ticket(id="part-aa33", title="Dep B"))
        # "aa" matches both part-aa22 and part-aa33
        r = run_tq("edit", "aa11", "--undep", "aa", env={"TICKETS_DIR": str(td)})
        assert r.returncode != 0
        assert "ambiguous" in r.stderr.lower()

    def test_edit_unlink_ambiguous_partial_errors(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-bb11", title="Subject", links=["part-bb22", "part-bb33"]))
        _write(td, Ticket(id="part-bb22", title="Link A", links=["part-bb11"]))
        _write(td, Ticket(id="part-bb33", title="Link B", links=["part-bb11"]))
        # "bb" matches both part-bb22 and part-bb33
        r = run_tq("edit", "bb11", "--unlink", "bb", env={"TICKETS_DIR": str(td)})
        assert r.returncode != 0
        assert "ambiguous" in r.stderr.lower()

    def test_lifecycle_accepts_partial(self, tmp_path: Path) -> None:
        """tq start/close/cancel/reopen must accept partial IDs too."""
        td = _make_dir(tmp_path)
        _write(td, Ticket(id="part-nnnn", title="Lifecycle"))
        r = run_tq("start", "nnnn", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-nnnn").status == "in_progress"
        r = run_tq("close", "nnnn", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert _read(td, "part-nnnn").status == "closed"

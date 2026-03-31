"""Tests for field command argument parsing and behavior.
# spec: ticket-fields
"""
from __future__ import annotations

import os
import subprocess
import typing as T
from pathlib import Path


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


def run_tq_env(
    *args: str, env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True, text=True, env=merged,
    )


class TestAssignArgs:
    """Argument parsing for `tq assign`."""

    # spec: ticket-fields requirement=assign scenario=assign-a-user
    def test_assign_accepts_id_and_assignee(self) -> None:
        result = run_tq("assign", "t-001", "Alice")
        assert result.returncode == 0

    # spec: ticket-fields requirement=assign scenario=assign-clears-when-omitted
    def test_assign_without_assignee_clears(self) -> None:
        result = run_tq("assign", "t-001")
        assert result.returncode == 0

    def test_assign_requires_id(self) -> None:
        result = run_tq("assign")
        assert result.returncode != 0


class TestChangePrioArgs:
    """Argument parsing for `tq change-prio`."""

    # spec: ticket-fields requirement=change-priority scenario=change-priority
    def test_change_prio_requires_id_and_priority(self) -> None:
        result = run_tq("change-prio", "t-001")
        assert result.returncode != 0

    def test_change_prio_accepts_valid_priority(self) -> None:
        for p in ["0", "1", "2", "3", "4"]:
            result = run_tq("change-prio", "t-001", p)
            assert result.returncode == 0, f"Priority {p} should be valid"

    # spec: ticket-fields requirement=change-priority scenario=invalid-priority-rejected
    def test_change_prio_rejects_invalid_priority(self) -> None:
        result = run_tq("change-prio", "t-001", "5")
        assert result.returncode != 0

    # spec: ticket-fields requirement=change-priority scenario=invalid-priority-rejected
    def test_change_prio_rejects_negative_priority(self) -> None:
        result = run_tq("change-prio", "t-001", "-1")
        assert result.returncode != 0


class TestChangeTypeArgs:
    """Argument parsing for `tq change-type`."""

    # spec: ticket-fields requirement=change-type scenario=change-type
    def test_change_type_requires_id_and_type(self) -> None:
        result = run_tq("change-type", "t-001")
        assert result.returncode != 0

    def test_change_type_accepts_valid_types(self) -> None:
        for t in ["bug", "feature", "task", "epic", "chore"]:
            result = run_tq("change-type", "t-001", t)
            assert result.returncode == 0, f"Type '{t}' should be valid"

    # spec: ticket-fields requirement=change-type scenario=invalid-type-rejected
    def test_change_type_rejects_invalid_type(self) -> None:
        result = run_tq("change-type", "t-001", "invalid")
        assert result.returncode != 0


class TestTagArgs:
    """Argument parsing for `tq tag` / `tq untag`."""

    # spec: ticket-fields requirement=tag-management scenario=add-tags
    def test_tag_requires_id_and_tags(self) -> None:
        result = run_tq("tag", "t-001")
        assert result.returncode != 0

    # spec: ticket-fields requirement=tag-management scenario=add-tags
    def test_tag_accepts_single_tag(self) -> None:
        result = run_tq("tag", "t-001", "urgent")
        assert result.returncode == 0

    # spec: ticket-fields requirement=tag-management scenario=add-tags
    def test_tag_accepts_multiple_tags(self) -> None:
        result = run_tq("tag", "t-001", "ui", "backend")
        assert result.returncode == 0

    # spec: ticket-fields requirement=tag-management scenario=remove-tags
    def test_untag_requires_id_and_tags(self) -> None:
        result = run_tq("untag", "t-001")
        assert result.returncode != 0

    def test_untag_accepts_multiple_tags(self) -> None:
        result = run_tq("untag", "t-001", "ui", "backend")
        assert result.returncode == 0


class TestXrefArgs:
    """Argument parsing for `tq xref`."""

    # spec: ticket-fields requirement=external-reference scenario=set-reference
    def test_xref_accepts_id_and_ref(self) -> None:
        result = run_tq("xref", "t-001", "gh-123")
        assert result.returncode == 0

    # spec: ticket-fields requirement=external-reference scenario=clear-reference
    def test_xref_without_ref_clears(self) -> None:
        result = run_tq("xref", "t-001")
        assert result.returncode == 0

    def test_xref_requires_id(self) -> None:
        result = run_tq("xref")
        assert result.returncode != 0


def _make_ticket(tickets_dir: Path, **overrides: T.Any) -> None:
    from tiquette.store import Ticket, write_ticket
    defaults: dict[str, T.Any] = dict(id="t-001", title="Test ticket")
    defaults.update(overrides)
    write_ticket(Ticket(**defaults), tickets_dir)


class TestFieldsBehavior:
    """End-to-end behavioral tests for field mutation commands."""

    def test_assign_sets_assignee(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path)
        result = run_tq_env("assign", "t-001", "Alice", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).assignee == "Alice"

    def test_assign_reassigns(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, assignee="Alice")
        result = run_tq_env("assign", "t-001", "Bob", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).assignee == "Bob"

    def test_assign_clears_assignee(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, assignee="Alice")
        result = run_tq_env("assign", "t-001", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).assignee is None

    def test_change_prio_updates_priority(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, priority=2)
        result = run_tq_env("change-prio", "t-001", "0", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).priority == 0

    def test_change_type_updates_type(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, type="task")
        result = run_tq_env("change-type", "t-001", "bug", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).type == "bug"

    def test_tag_adds_tags(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path)
        result = run_tq_env("tag", "t-001", "ui", "backend", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert set(read_ticket("t-001", tmp_path).tags) == {"ui", "backend"}

    def test_tag_is_additive(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, tags=["ui"])
        result = run_tq_env("tag", "t-001", "backend", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert set(read_ticket("t-001", tmp_path).tags) == {"ui", "backend"}

    def test_tag_deduplicates(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, tags=["ui"])
        result = run_tq_env("tag", "t-001", "ui", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).tags == ["ui"]

    def test_untag_removes_tags(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, tags=["ui", "backend"])
        result = run_tq_env("untag", "t-001", "backend", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).tags == ["ui"]

    def test_xref_sets_reference(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path)
        result = run_tq_env("xref", "t-001", "gh-123", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).xref == "gh-123"

    def test_xref_clears_reference(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket
        _make_ticket(tmp_path, xref="gh-123")
        result = run_tq_env("xref", "t-001", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode == 0
        assert read_ticket("t-001", tmp_path).xref is None

    def test_assign_nonexistent_ticket_fails(self, tmp_path: Path) -> None:
        result = run_tq_env("assign", "t-999", "Alice", env={"TICKETS_DIR": str(tmp_path)})
        assert result.returncode != 0

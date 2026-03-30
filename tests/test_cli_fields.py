"""Tests for field command argument parsing.
# spec: ticket-fields
"""
from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


class TestAssignArgs:
    """Argument parsing for `tq assign` / `tq unassign`."""

    # spec: ticket-fields requirement=assign scenario=assign-a-user
    def test_assign_requires_id_and_assignee(self) -> None:
        result = run_tq("assign", "t-001")
        assert result.returncode != 0

    def test_assign_accepts_id_and_assignee(self) -> None:
        result = run_tq("assign", "t-001", "Alice")
        assert result.returncode == 0

    # spec: ticket-fields requirement=unassign scenario=unassign-a-user
    def test_unassign_requires_id(self) -> None:
        result = run_tq("unassign")
        assert result.returncode != 0

    def test_unassign_accepts_id(self) -> None:
        result = run_tq("unassign", "t-001")
        assert result.returncode == 0


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

    def test_tag_accepts_comma_separated_tags(self) -> None:
        result = run_tq("tag", "t-001", "ui,backend")
        assert result.returncode == 0

    # spec: ticket-fields requirement=tag-management scenario=add-tags
    def test_tag_accepts_single_tag(self) -> None:
        result = run_tq("tag", "t-001", "urgent")
        assert result.returncode == 0

    # spec: ticket-fields requirement=tag-management scenario=remove-tags
    def test_untag_requires_id_and_tags(self) -> None:
        result = run_tq("untag", "t-001")
        assert result.returncode != 0

    def test_untag_accepts_comma_separated_tags(self) -> None:
        result = run_tq("untag", "t-001", "ui,backend")
        assert result.returncode == 0


class TestRefArgs:
    """Argument parsing for `tq set-ref` / `tq unset-ref`."""

    # spec: ticket-fields requirement=external-reference scenario=set-reference
    def test_set_ref_requires_id_and_ref(self) -> None:
        result = run_tq("set-ref", "t-001")
        assert result.returncode != 0

    def test_set_ref_accepts_id_and_ref(self) -> None:
        result = run_tq("set-ref", "t-001", "gh-123")
        assert result.returncode == 0

    # spec: ticket-fields requirement=external-reference scenario=clear-reference
    def test_unset_ref_requires_id(self) -> None:
        result = run_tq("unset-ref")
        assert result.returncode != 0

    def test_unset_ref_accepts_id(self) -> None:
        result = run_tq("unset-ref", "t-001")
        assert result.returncode == 0

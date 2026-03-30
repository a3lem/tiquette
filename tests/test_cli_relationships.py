"""Tests for relationship command argument parsing.
# spec: ticket-relationships
"""
from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


class TestDepArgs:
    """Argument parsing for `tq dep`."""

    # spec: ticket-relationships requirement=add-dependency scenario=add-a-dependency
    def test_dep_requires_two_args(self) -> None:
        result = run_tq("dep", "only-one")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=add-dependency scenario=add-a-dependency
    def test_dep_accepts_two_ids(self) -> None:
        result = run_tq("dep", "task-0001", "task-0002")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=add-dependency
    def test_dep_accepts_multiple_dep_ids(self) -> None:
        result = run_tq("dep", "task-0001", "task-0002", "task-0003")
        assert result.returncode == 0


class TestUndepArgs:
    """Argument parsing for `tq undep`."""

    # spec: ticket-relationships requirement=remove-dependency scenario=remove-a-dependency
    def test_undep_requires_two_args(self) -> None:
        result = run_tq("undep", "only-one")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=remove-dependency scenario=remove-a-dependency
    def test_undep_accepts_two_ids(self) -> None:
        result = run_tq("undep", "task-0001", "task-0002")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=remove-dependency scenario=remove-multiple-dependencies
    def test_undep_accepts_multiple_dep_ids(self) -> None:
        result = run_tq("undep", "task-0001", "task-0002", "task-0003")
        assert result.returncode == 0


class TestNestArgs:
    """Argument parsing for `tq nest`."""

    # spec: ticket-relationships requirement=nest-tickets scenario=nest-a-child-under-a-parent
    def test_nest_requires_at_least_two_args(self) -> None:
        result = run_tq("nest", "only-one")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=nest-tickets scenario=nest-a-child-under-a-parent
    def test_nest_accepts_child_and_parent(self) -> None:
        result = run_tq("nest", "child-001", "parent-001")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=nest-tickets scenario=nest-multiple-children
    def test_nest_accepts_multiple_children_and_parent(self) -> None:
        result = run_tq("nest", "child-001", "child-002", "parent-001")
        assert result.returncode == 0


class TestUnnestArgs:
    """Argument parsing for `tq unnest`."""

    # spec: ticket-relationships requirement=unnest-tickets scenario=unnest-a-ticket
    def test_unnest_requires_id(self) -> None:
        result = run_tq("unnest")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=unnest-tickets scenario=unnest-a-ticket
    def test_unnest_accepts_id(self) -> None:
        result = run_tq("unnest", "child-001")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=unnest-tickets
    def test_unnest_accepts_multiple_ids(self) -> None:
        result = run_tq("unnest", "child-001", "child-002")
        assert result.returncode == 0


class TestLinkArgs:
    """Argument parsing for `tq link`."""

    # spec: ticket-relationships requirement=link-tickets scenario=link-two-tickets
    def test_link_requires_two_args(self) -> None:
        result = run_tq("link", "only-one")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=link-tickets scenario=link-two-tickets
    def test_link_accepts_two_ids(self) -> None:
        result = run_tq("link", "link-0001", "link-0002")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=link-tickets scenario=link-three-tickets
    def test_link_accepts_three_ids(self) -> None:
        result = run_tq("link", "link-0001", "link-0002", "link-0003")
        assert result.returncode == 0


class TestUnlinkArgs:
    """Argument parsing for `tq unlink`."""

    # spec: ticket-relationships requirement=unlink-tickets scenario=unlink-two-tickets
    def test_unlink_requires_two_args(self) -> None:
        result = run_tq("unlink", "only-one")
        assert result.returncode != 0

    # spec: ticket-relationships requirement=unlink-tickets scenario=unlink-two-tickets
    def test_unlink_accepts_two_ids(self) -> None:
        result = run_tq("unlink", "link-0001", "link-0002")
        assert result.returncode == 0

    # spec: ticket-relationships requirement=unlink-tickets scenario=unlink-multiple-targets
    def test_unlink_accepts_three_ids(self) -> None:
        result = run_tq("unlink", "link-0001", "link-0002", "link-0003")
        assert result.returncode == 0

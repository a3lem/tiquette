"""Tests for relationship command argument parsing and behavior.
# spec: ticket-relationships
"""
from __future__ import annotations

import os
import subprocess
import typing as T
from pathlib import Path

from tiquette.store import Ticket, read_ticket, write_ticket


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


def run_tq_env(
    *args: str, env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True, text=True, env=run_env,
    )


def _make_ticket(tickets_dir: Path, ticket_id: str, **kwargs: T.Any) -> Ticket:
    tickets_dir.mkdir(parents=True, exist_ok=True)
    t = Ticket(id=ticket_id, title=f"Test {ticket_id}", **kwargs)
    write_ticket(t, tickets_dir)
    return t


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


class TestDepBehavior:
    """Behavioral tests for dep/undep/cycle detection."""

    def test_dep_adds_dependency(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001")
        _make_ticket(td, "task-0002")
        result = run_tq_env("dep", "task-0001", "task-0002", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "task-0002" in read_ticket("task-0001", td).deps

    def test_dep_is_idempotent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001")
        _make_ticket(td, "task-0002")
        env = {"TICKETS_DIR": str(td)}
        run_tq_env("dep", "task-0001", "task-0002", env=env)
        result = run_tq_env("dep", "task-0001", "task-0002", env=env)
        assert result.returncode == 0
        assert read_ticket("task-0001", td).deps.count("task-0002") == 1

    def test_dep_nonexistent_target(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001")
        result = run_tq_env("dep", "task-0001", "nonexistent", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "ticket 'nonexistent' not found" in result.stderr

    def test_dep_nonexistent_source(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001")
        result = run_tq_env("dep", "nonexistent", "task-0001", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "ticket 'nonexistent' not found" in result.stderr

    def test_dep_direct_cycle_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-a")
        _make_ticket(td, "task-b")
        env = {"TICKETS_DIR": str(td)}
        run_tq_env("dep", "task-a", "task-b", env=env)
        result = run_tq_env("dep", "task-b", "task-a", env=env)
        assert result.returncode != 0
        assert "cycle" in result.stderr.lower()

    def test_dep_transitive_cycle_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-a")
        _make_ticket(td, "task-b")
        _make_ticket(td, "task-c")
        env = {"TICKETS_DIR": str(td)}
        run_tq_env("dep", "task-a", "task-b", env=env)
        run_tq_env("dep", "task-b", "task-c", env=env)
        result = run_tq_env("dep", "task-c", "task-a", env=env)
        assert result.returncode != 0
        assert "cycle" in result.stderr.lower()

    def test_undep_removes_dependency(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001", deps=["task-0002"])
        _make_ticket(td, "task-0002")
        result = run_tq_env("undep", "task-0001", "task-0002", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "task-0002" not in read_ticket("task-0001", td).deps

    def test_undep_removes_multiple(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001", deps=["task-0002", "task-0003"])
        _make_ticket(td, "task-0002")
        _make_ticket(td, "task-0003")
        result = run_tq_env("undep", "task-0001", "task-0002", "task-0003", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert read_ticket("task-0001", td).deps == []

    def test_undep_nonexistent_dep(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001")
        _make_ticket(td, "task-0002")
        result = run_tq_env("undep", "task-0001", "task-0002", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0


class TestLinkBehavior:
    """Behavioral tests for link/unlink (symmetric)."""

    def test_link_two_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a")
        _make_ticket(td, "link-b")
        result = run_tq_env("link", "link-a", "link-b", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "link-b" in read_ticket("link-a", td).links
        assert "link-a" in read_ticket("link-b", td).links

    def test_link_three_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a")
        _make_ticket(td, "link-b")
        _make_ticket(td, "link-c")
        result = run_tq_env("link", "link-a", "link-b", "link-c", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        a, b, c = (read_ticket(x, td) for x in ("link-a", "link-b", "link-c"))
        assert "link-b" in a.links and "link-c" in a.links
        assert "link-a" in b.links and "link-c" in b.links
        assert "link-a" in c.links and "link-b" in c.links

    def test_link_is_idempotent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a")
        _make_ticket(td, "link-b")
        env = {"TICKETS_DIR": str(td)}
        run_tq_env("link", "link-a", "link-b", env=env)
        result = run_tq_env("link", "link-a", "link-b", env=env)
        assert result.returncode == 0
        assert read_ticket("link-a", td).links.count("link-b") == 1

    def test_link_nonexistent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a")
        result = run_tq_env("link", "link-a", "nonexistent", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "ticket 'nonexistent' not found" in result.stderr

    def test_unlink_two_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a", links=["link-b"])
        _make_ticket(td, "link-b", links=["link-a"])
        result = run_tq_env("unlink", "link-a", "link-b", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "link-b" not in read_ticket("link-a", td).links
        assert "link-a" not in read_ticket("link-b", td).links

    def test_unlink_multiple(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a", links=["link-b", "link-c"])
        _make_ticket(td, "link-b", links=["link-a"])
        _make_ticket(td, "link-c", links=["link-a"])
        result = run_tq_env("unlink", "link-a", "link-b", "link-c", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert read_ticket("link-a", td).links == []

    def test_unlink_nonexistent_link(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "link-a")
        _make_ticket(td, "link-b")
        result = run_tq_env("unlink", "link-a", "link-b", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0


class TestNestBehavior:
    """Behavioral tests for nest/unnest."""

    def test_nest_child_under_parent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "child-001")
        _make_ticket(td, "parent-001")
        result = run_tq_env("nest", "child-001", "parent-001", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert read_ticket("child-001", td).parent == "parent-001"

    def test_nest_multiple_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "c1")
        _make_ticket(td, "c2")
        _make_ticket(td, "parent")
        result = run_tq_env("nest", "c1", "c2", "parent", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert read_ticket("c1", td).parent == "parent"
        assert read_ticket("c2", td).parent == "parent"

    def test_unnest_ticket(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "child-001", parent="parent-001")
        _make_ticket(td, "parent-001")
        result = run_tq_env("unnest", "child-001", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert read_ticket("child-001", td).parent is None

"""Tests for query command argument parsing and behavior.
# spec: ticket-query
"""
from __future__ import annotations

import json
import os
import subprocess
import typing as T
from pathlib import Path

from tiquette.store import Ticket, write_ticket


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


def run_tq_env(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run tq with custom environment (for TICKETS_DIR isolation)."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
        env=run_env,
    )


class TestShowArgs:
    """Argument parsing for `tq show`."""

    # spec: ticket-query requirement=show-ticket scenario=show-displays-ticket-content
    def test_show_requires_id(self) -> None:
        result = run_tq("show")
        assert result.returncode != 0

    def test_show_accepts_id(self) -> None:
        result = run_tq("show", "show-001")
        assert result.returncode == 0

    # spec: ticket-query requirement=show-ticket scenario=show-as-json
    def test_show_accepts_json_flag(self) -> None:
        result = run_tq("show", "show-001", "--json")
        assert result.returncode == 0


class TestInfoArgs:
    """Argument parsing for `tq info`."""

    # spec: ticket-query requirement=info-command scenario=info-displays-frontmatter-and-relationships
    def test_info_requires_id(self) -> None:
        result = run_tq("info")
        assert result.returncode != 0

    def test_info_accepts_id(self) -> None:
        result = run_tq("info", "info-001")
        assert result.returncode == 0

    # spec: ticket-query requirement=info-command scenario=info-as-json
    def test_info_accepts_json_flag(self) -> None:
        result = run_tq("info", "info-001", "--json")
        assert result.returncode == 0


class TestPathArgs:
    """Argument parsing for `tq path`."""

    # spec: ticket-query requirement=path-command scenario=path-prints-file-location
    def test_path_requires_id(self) -> None:
        result = run_tq("path")
        assert result.returncode != 0

    def test_path_accepts_id(self) -> None:
        result = run_tq("path", "test-001")
        assert result.returncode == 0


class TestShowDepsArgs:
    """Argument parsing for `tq deps`."""

    # spec: ticket-query requirement=show-dependency-tree scenario=dependency-tree-shows-transitive-deps
    def test_deps_requires_id(self) -> None:
        result = run_tq("deps")
        assert result.returncode != 0

    def test_deps_accepts_id(self) -> None:
        result = run_tq("deps", "task-0001")
        assert result.returncode == 0

    # spec: ticket-query requirement=show-dependency-tree scenario=full-tree-disables-deduplication
    def test_deps_accepts_full_flag(self) -> None:
        result = run_tq("deps", "task-0001", "--full")
        assert result.returncode == 0


class TestLsArgs:
    """Argument parsing for `tq ls`."""

    # spec: ticket-query requirement=list-tickets scenario=list-all-open-tickets
    def test_ls_no_args(self) -> None:
        result = run_tq("ls")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=list-with---status-open
    def test_ls_status_filter(self) -> None:
        for status in ["open", "in_progress", "closed", "canceled"]:
            result = run_tq("ls", "--status", status)
            assert result.returncode == 0, f"Status '{status}' should be valid"

    # spec: ticket-query requirement=list-tickets scenario=list-with--s-closed
    def test_ls_short_status_flag(self) -> None:
        result = run_tq("ls", "-s", "closed")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=--status-completed-is-rejected
    def test_ls_status_completed_rejected(self) -> None:
        result = run_tq("ls", "--status", "completed")
        assert result.returncode != 0
        assert result.stderr  # should point toward autofix / 'closed'

    # spec: ticket-query requirement=list-tickets scenario=--completed-flag-is-rejected
    def test_ls_completed_flag_rejected(self) -> None:
        result = run_tq("ls", "--completed")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=--canceled-flag-is-rejected
    def test_ls_canceled_flag_rejected(self) -> None:
        result = run_tq("ls", "--canceled")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=invalid-status-rejected
    def test_ls_invalid_status(self) -> None:
        result = run_tq("ls", "--status", "invalid")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=ready-filter
    def test_ls_ready_flag(self) -> None:
        result = run_tq("ls", "--ready")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=blocked-filter
    def test_ls_blocked_flag(self) -> None:
        result = run_tq("ls", "--blocked")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=ready-and-blocked-are-mutually-exclusive
    def test_ls_ready_and_blocked_are_mutually_exclusive(self) -> None:
        result = run_tq("ls", "--ready", "--blocked")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-assignee-long-form
    def test_ls_assignee_filter(self) -> None:
        result = run_tq("ls", "--assignee", "Alice")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=-a-is-short-for---assignee
    def test_ls_assignee_short_flag(self) -> None:
        result = run_tq("ls", "-A", "Alice")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=-a-is-no-longer-short-for---assignee
    def test_ls_lowercase_a_no_longer_assignee(self) -> None:
        # `-a` now means --all (boolean), so `-a Alice` should fail (Alice unparsed)
        result = run_tq("ls", "-a", "Alice")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-source-axis scenario=-a-shows-active-and-archived
    def test_ls_all_short_flag(self) -> None:
        result = run_tq("ls", "-a")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-source-axis scenario=--archived-shows-only-archived-tickets
    def test_ls_archived_flag(self) -> None:
        result = run_tq("ls", "--archived")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-source-axis scenario=--all-and---archived-mutually-exclusive
    def test_ls_all_and_archived_mutually_exclusive(self) -> None:
        result = run_tq("ls", "--all", "--archived")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-tag-long-form
    def test_ls_tag_filter(self) -> None:
        result = run_tq("ls", "--tag", "ui")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=-t-is-not-accepted-as-a-short-for---tag
    def test_ls_tag_short_flag_rejected(self) -> None:
        result = run_tq("ls", "-T", "ui")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-type
    def test_ls_type_filter(self) -> None:
        result = run_tq("ls", "--type", "bug")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=sort-by-mtime
    def test_ls_sort(self) -> None:
        for sort in ["priority", "mtime"]:
            result = run_tq("ls", "--sort", sort)
            assert result.returncode == 0, f"Sort '{sort}' should be valid"

    # spec: ticket-query requirement=list-tickets scenario=invalid-sort-rejected
    def test_ls_invalid_sort(self) -> None:
        result = run_tq("ls", "--sort", "invalid")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=limit
    def test_ls_limit(self) -> None:
        result = run_tq("ls", "--limit", "10")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=limit-must-be-positive
    def test_ls_limit_must_be_positive(self) -> None:
        result = run_tq("ls", "--limit", "0")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=jsonl-output
    def test_ls_jsonl_flag(self) -> None:
        result = run_tq("ls", "--jsonl")
        assert result.returncode == 0


class TestTagsArgs:
    """Argument parsing for `tq tags`."""

    # spec: ticket-query requirement=tags-listing scenario=tags-sorted-by-count-descending
    def test_tags_no_args(self) -> None:
        result = run_tq("tags")
        assert result.returncode == 0


class TestLinksArgs:
    """Argument parsing for `tq links`."""

    # spec: ticket-query requirement=links-listing
    def test_links_no_args(self) -> None:
        result = run_tq("links")
        assert result.returncode == 0


class TestArchiveArgs:
    """Argument parsing for `tq archive`."""

    # spec: ticket-query requirement=archive scenario=archive-moves-closed-tickets
    def test_archive_no_args(self) -> None:
        result = run_tq("archive")
        assert result.returncode == 0


# ── Behavioral tests ─────────────────────────────────────────
# Each class creates its own TICKETS_DIR for isolation.


def _make_env(tickets_dir: Path) -> dict[str, str]:
    return {"TICKETS_DIR": str(tickets_dir)}


class TestShowBehavior:
    """Behavioral tests for `tq show`."""

    def test_show_displays_ticket_content(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-001", title="Test ticket"), td)
        r = run_tq_env("show", "show-001", env=_make_env(td))
        assert r.returncode == 0
        assert "id: show-001" in r.stdout
        assert "# Test ticket" in r.stdout

    def test_show_displays_all_frontmatter_fields(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(
            id="show-002", title="Full ticket",
            deps=["dep-a"], links=["link-a"],
            type="bug", priority=1,
        ), td)
        r = run_tq_env("show", "show-002", env=_make_env(td))
        assert r.returncode == 0
        for field in ("status:", "deps:", "links:", "type:", "priority:"):
            assert field in r.stdout, f"missing {field}"

    def test_show_displays_blockers_section(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-003", title="Blocked", deps=["show-004"]), td)
        write_ticket(Ticket(id="show-004", title="Blocker", status="open"), td)
        r = run_tq_env("show", "show-003", env=_make_env(td))
        assert "## Blockers" in r.stdout
        assert "show-004" in r.stdout
        assert "[open]" in r.stdout

    def test_show_hides_blockers_when_all_deps_closed(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-005", title="Unblocked", deps=["show-006"]), td)
        write_ticket(Ticket(id="show-006", title="Done dep", status="closed"), td)
        r = run_tq_env("show", "show-005", env=_make_env(td))
        assert "## Blockers" not in r.stdout

    def test_show_displays_blocking_section(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-007", title="Dependency"), td)
        write_ticket(Ticket(id="show-008", title="Depends on 007", deps=["show-007"]), td)
        r = run_tq_env("show", "show-007", env=_make_env(td))
        assert "## Blocking" in r.stdout
        assert "show-008" in r.stdout

    def test_show_displays_children_section(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-009", title="Parent"), td)
        write_ticket(Ticket(id="show-010", title="Child", parent="show-009"), td)
        r = run_tq_env("show", "show-009", env=_make_env(td))
        assert "## Children" in r.stdout
        assert "show-010" in r.stdout

    def test_show_displays_linked_section(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-011", title="Linked", links=["show-012"]), td)
        write_ticket(Ticket(id="show-012", title="Other linked", links=["show-011"]), td)
        r = run_tq_env("show", "show-011", env=_make_env(td))
        assert "## Linked" in r.stdout
        assert "show-012" in r.stdout

    def test_show_nonexistent_ticket(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        r = run_tq_env("show", "nonexistent", env=_make_env(td))
        assert r.returncode != 0
        assert "ticket 'nonexistent' not found" in r.stderr

    def test_show_with_partial_id(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="show-partial-001", title="Partial match"), td)
        r = run_tq_env("show", "partial-001", env=_make_env(td))
        assert r.returncode == 0
        assert "show-partial-001" in r.stdout

    def test_show_as_json(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(
            id="show-json", title="JSON test",
            status="open", type="task", priority=2,
            description="Some body text",
        ), td)
        r = run_tq_env("show", "show-json", "--json", env=_make_env(td))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["id"] == "show-json"
        assert data["status"] == "open"
        assert data["type"] == "task"
        assert data["priority"] == 2
        assert data["title"] == "JSON test"
        assert "body" in data


class TestInfoBehavior:
    """Behavioral tests for `tq info`."""

    def test_info_displays_frontmatter_and_relationships(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="info-001", title="Info ticket", deps=["info-002"]), td)
        write_ticket(Ticket(id="info-002", title="Dep ticket"), td)
        r = run_tq_env("info", "info-001", env=_make_env(td))
        assert r.returncode == 0
        assert "id: info-001" in r.stdout
        assert "status:" in r.stdout
        # Info should NOT contain the body/description
        assert "# Info ticket" not in r.stdout

    def test_info_as_json(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="info-json", title="JSON info"), td)
        r = run_tq_env("info", "info-json", "--json", env=_make_env(td))
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert data["id"] == "info-json"
        assert "body" not in data

    def test_info_nonexistent_ticket(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        r = run_tq_env("info", "nonexistent", env=_make_env(td))
        assert r.returncode != 0
        assert "ticket 'nonexistent' not found" in r.stderr


class TestPathBehavior:
    """Behavioral tests for `tq path`."""

    def test_path_prints_file_location(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="test-001", title="Path ticket"), td)
        r = run_tq_env("path", "test-001", env=_make_env(td))
        assert r.returncode == 0
        assert ".tickets/test-001.md" in r.stdout


class TestLsBehavior:
    """Behavioral tests for `tq ls`."""

    def test_list_all_open_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-001", title="Open", status="open"), td)
        write_ticket(Ticket(id="ls-002", title="In progress", status="in_progress"), td)
        write_ticket(Ticket(id="ls-003", title="Closed", status="closed"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert r.returncode == 0
        assert "ls-001" in r.stdout
        assert "ls-002" in r.stdout
        assert "ls-003" in r.stdout

    def test_list_with_status_filter(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-004", title="Open", status="open"), td)
        write_ticket(Ticket(id="ls-005", title="Closed", status="closed"), td)
        r = run_tq_env("ls", "--status", "open", env=_make_env(td))
        assert "ls-004" in r.stdout
        assert "ls-005" not in r.stdout

    def test_list_shows_dependencies(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-006", title="Has dep", deps=["ls-007"]), td)
        write_ticket(Ticket(id="ls-007", title="Dep"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "<- [ls-007]" in r.stdout

    def test_list_with_no_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        r = run_tq_env("ls", env=_make_env(td))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_ready_filter(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-ready-1", title="Ready", priority=1), td)
        write_ticket(Ticket(id="ls-ready-2", title="Blocked", deps=["ls-ready-3"]), td)
        write_ticket(Ticket(id="ls-ready-3", title="Open dep", status="open"), td)
        r = run_tq_env("ls", "--ready", env=_make_env(td))
        assert "ls-ready-1" in r.stdout
        assert "ls-ready-3" in r.stdout  # has no deps, is ready
        assert "ls-ready-2" not in r.stdout  # blocked by open dep

    def test_ready_includes_tickets_with_all_deps_closed(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-rc-1", title="All closed deps", deps=["ls-rc-2"]), td)
        write_ticket(Ticket(id="ls-rc-2", title="Closed dep", status="closed"), td)
        r = run_tq_env("ls", "--ready", env=_make_env(td))
        assert "ls-rc-1" in r.stdout

    def test_ready_excludes_closed_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-rx-1", title="Closed", status="closed"), td)
        write_ticket(Ticket(id="ls-rx-2", title="Open"), td)
        r = run_tq_env("ls", "--ready", env=_make_env(td))
        assert "ls-rx-1" not in r.stdout
        assert "ls-rx-2" in r.stdout

    def test_ready_excludes_parent_with_open_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-rp-1", title="Parent"), td)
        write_ticket(Ticket(id="ls-rp-child", title="Open child", parent="ls-rp-1", status="open"), td)
        r = run_tq_env("ls", "--ready", env=_make_env(td))
        assert "ls-rp-1" not in r.stdout

    def test_ready_sorts_by_priority_then_id(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-rs-b", title="Low prio", priority=3), td)
        write_ticket(Ticket(id="ls-rs-a", title="High prio", priority=1), td)
        write_ticket(Ticket(id="ls-rs-c", title="High prio 2", priority=1), td)
        r = run_tq_env("ls", "--ready", env=_make_env(td))
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        # P1 before P3, and among P1s, sorted by id
        assert lines[0].startswith("ls-rs-a")
        assert lines[1].startswith("ls-rs-c")
        assert lines[2].startswith("ls-rs-b")

    def test_blocked_by_open_dependency(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-bl-1", title="Blocked", deps=["ls-bl-2"]), td)
        write_ticket(Ticket(id="ls-bl-2", title="Open dep", status="open"), td)
        write_ticket(Ticket(id="ls-bl-3", title="Not blocked"), td)
        r = run_tq_env("ls", "--blocked", env=_make_env(td))
        assert "ls-bl-1" in r.stdout
        assert "ls-bl-3" not in r.stdout

    def test_blocked_by_open_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-bc-1", title="Parent"), td)
        write_ticket(Ticket(id="ls-bc-child", title="Child", parent="ls-bc-1", status="open"), td)
        r = run_tq_env("ls", "--blocked", env=_make_env(td))
        assert "ls-bc-1" in r.stdout

    def test_blocked_excludes_tickets_with_all_deps_closed(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-be-1", title="All deps closed", deps=["ls-be-2"]), td)
        write_ticket(Ticket(id="ls-be-2", title="Closed", status="closed"), td)
        r = run_tq_env("ls", "--blocked", env=_make_env(td))
        assert "ls-be-1" not in r.stdout

    # spec: ticket-query requirement=list-tickets scenario=list-with--s-closed
    def test_closed_filter(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-comp", title="Closed", status="closed"), td)
        write_ticket(Ticket(id="ls-canc", title="Canceled", status="canceled"), td)
        write_ticket(Ticket(id="ls-open", title="Open", status="open"), td)
        r = run_tq_env("ls", "--status", "closed", env=_make_env(td))
        assert "ls-comp" in r.stdout
        assert "ls-canc" not in r.stdout
        assert "ls-open" not in r.stdout

    # spec: ticket-query requirement=list-tickets scenario=--status-completed-is-rejected
    def test_completed_filter_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-comp-rej", title="Closed", status="closed"), td)
        r = run_tq_env("ls", "--status", "completed", env=_make_env(td))
        assert r.returncode != 0
        assert r.stderr  # should contain autofix hint

    # spec: ticket-query requirement=list-tickets scenario=list-with---status-canceled
    def test_canceled_filter(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-comp2", title="Closed", status="closed"), td)
        write_ticket(Ticket(id="ls-canc2", title="Canceled", status="canceled"), td)
        r = run_tq_env("ls", "--status", "canceled", env=_make_env(td))
        assert "ls-canc2" in r.stdout
        assert "ls-comp2" not in r.stdout

    def test_limit(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        for i in range(5):
            write_ticket(Ticket(id=f"ls-lim-{i:03d}", title=f"Ticket {i}"), td)
        r = run_tq_env("ls", "--limit", "2", env=_make_env(td))
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) == 2

    def test_jsonl_output(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(
            id="ls-jsonl", title="JSONL test",
            deps=["dep1"], links=["link1"],
            type="bug", priority=1,
        ), td)
        r = run_tq_env("ls", "--jsonl", env=_make_env(td))
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        assert len(lines) >= 1
        data = json.loads(lines[0])
        for key in ("id", "status", "deps", "links", "type", "priority"):
            assert key in data, f"missing key {key}"

    def test_filter_by_assignee(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-a1", title="Alice ticket", assignee="Alice"), td)
        write_ticket(Ticket(id="ls-a2", title="Bob ticket", assignee="Bob"), td)
        r = run_tq_env("ls", "--assignee", "Alice", env=_make_env(td))
        assert "ls-a1" in r.stdout
        assert "ls-a2" not in r.stdout

    def test_filter_by_tag(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-t1", title="UI ticket", tags=["ui"]), td)
        write_ticket(Ticket(id="ls-t2", title="Backend", tags=["backend"]), td)
        r = run_tq_env("ls", "--tag", "ui", env=_make_env(td))
        assert "ls-t1" in r.stdout
        assert "ls-t2" not in r.stdout

    def test_filter_by_type(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ls-ty1", title="Bug", type="bug"), td)
        write_ticket(Ticket(id="ls-ty2", title="Task", type="task"), td)
        r = run_tq_env("ls", "--type", "bug", env=_make_env(td))
        assert "ls-ty1" in r.stdout
        assert "ls-ty2" not in r.stdout

    def test_sort_by_mtime(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        import time
        write_ticket(Ticket(id="ls-mt-old", title="Old"), td)
        time.sleep(0.05)
        write_ticket(Ticket(id="ls-mt-new", title="New"), td)
        r = run_tq_env("ls", "--sort", "mtime", env=_make_env(td))
        lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
        # Most recently modified first
        assert lines[0].startswith("ls-mt-new")

    def test_tree_rendering_parent_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="tree-p", title="Parent", priority=2), td)
        write_ticket(Ticket(id="tree-c1", title="Child 1", parent="tree-p", priority=1), td)
        write_ticket(Ticket(id="tree-c2", title="Child 2", parent="tree-p", priority=2), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "├──" in r.stdout or "└──" in r.stdout

    def test_tree_rendering_nested_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="nest-p", title="Parent"), td)
        write_ticket(Ticket(id="nest-c1", title="Child", parent="nest-p"), td)
        write_ticket(Ticket(id="nest-gc1", title="Grandchild", parent="nest-c1"), td)
        r = run_tq_env("ls", env=_make_env(td))
        # Grandchild should have deeper indentation
        lines = r.stdout.strip().splitlines()
        gc_line = [l for l in lines if "nest-gc1" in l]
        assert len(gc_line) == 1
        # Should have more leading space than child
        c_line = [l for l in lines if "nest-c1" in l][0]
        assert len(gc_line[0]) - len(gc_line[0].lstrip()) > len(c_line) - len(c_line.lstrip()) or "│" in gc_line[0]

    def test_tree_orphan_at_root(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="tree-orphan", title="Orphan"), td)
        write_ticket(Ticket(id="tree-par", title="Parent"), td)
        write_ticket(Ticket(id="tree-ch", title="Child", parent="tree-par"), td)
        r = run_tq_env("ls", env=_make_env(td))
        lines = r.stdout.strip().splitlines()
        orphan_line = [l for l in lines if "tree-orphan" in l]
        assert len(orphan_line) == 1
        # Orphan should be at root level (no tree prefix)
        assert not orphan_line[0].startswith("├") and not orphan_line[0].startswith("└") and not orphan_line[0].startswith("│")

    def test_tree_parent_shown_as_context_in_filtered_view(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ctx-p", title="Parent", assignee="Alice"), td)
        write_ticket(Ticket(id="ctx-c", title="Child", parent="ctx-p", assignee="Bob"), td)
        r = run_tq_env("ls", "--assignee", "Bob", env=_make_env(td))
        # Parent should appear as context heading
        assert "ctx-p" in r.stdout
        assert "ctx-c" in r.stdout

    def test_tree_parent_hidden_when_all_children_filtered_out(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="hid-p", title="Parent", assignee="Alice"), td)
        write_ticket(Ticket(id="hid-c", title="Child", parent="hid-p", assignee="Alice"), td)
        r = run_tq_env("ls", "--assignee", "Bob", env=_make_env(td))
        assert "hid-p" not in r.stdout
        assert "hid-c" not in r.stdout


class TestLsArchivedAndAll:
    """Behavioral tests for `ls` source axis: --archived, --all/-a.

    # spec: ticket-query requirement=list-source-axis
    """

    @staticmethod
    def _seed(tmp_path: Path) -> Path:
        td = tmp_path / ".tickets"
        td.mkdir()
        (td / "archive").mkdir()
        write_ticket(Ticket(id="act-001", title="Active"), td)
        write_ticket(
            Ticket(id="arc-001", title="Archived closed",
                   status="closed", tags=["ui"]),
            td / "archive",
        )
        write_ticket(
            Ticket(id="arc-002", title="Archived canceled",
                   status="canceled", tags=["backend"]),
            td / "archive",
        )
        return td

    # spec: ticket-query requirement=list-tickets scenario=default-excludes-archived
    def test_default_excludes_archived(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", env=_make_env(td))
        assert "act-001" in r.stdout
        assert "arc-001" not in r.stdout
        assert "arc-002" not in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--archived-shows-only-archived-tickets
    def test_archived_shows_only_archived(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "--archived", env=_make_env(td))
        assert "act-001" not in r.stdout
        assert "arc-001" in r.stdout
        assert "arc-002" in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--all-shows-active-and-archived
    def test_all_shows_active_and_archived(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "--all", env=_make_env(td))
        assert "act-001" in r.stdout
        assert "arc-001" in r.stdout
        assert "arc-002" in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=-a-shows-active-and-archived
    def test_short_a_means_all(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "-a", env=_make_env(td))
        assert "act-001" in r.stdout
        assert "arc-001" in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--archived-combines-with--status-canceled
    def test_archived_combines_with_canceled(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "--archived", "--status", "canceled", env=_make_env(td))
        assert "arc-002" in r.stdout
        assert "arc-001" not in r.stdout
        assert "act-001" not in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--archived-combines-with--s-closed
    def test_archived_combines_with_closed(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "--archived", "-s", "closed", env=_make_env(td))
        assert "arc-001" in r.stdout
        assert "arc-002" not in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--all-combines-with---status-closed
    def test_all_combines_with_closed(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        (td / "archive").mkdir()
        write_ticket(Ticket(id="done-001", title="Active closed", status="closed"), td)
        write_ticket(Ticket(id="done-003", title="Active canceled", status="canceled"), td)
        write_ticket(
            Ticket(id="done-002", title="Archived closed", status="closed"),
            td / "archive",
        )
        r = run_tq_env("ls", "--all", "--status", "closed", env=_make_env(td))
        assert "done-001" in r.stdout
        assert "done-002" in r.stdout
        assert "done-003" not in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--archived-combines-with---tag
    def test_archived_combines_with_tag(self, tmp_path: Path) -> None:
        td = self._seed(tmp_path)
        r = run_tq_env("ls", "--archived", "--tag", "ui", env=_make_env(td))
        assert "arc-001" in r.stdout
        assert "arc-002" not in r.stdout

    # spec: ticket-query requirement=list-source-axis scenario=--archived-with-no-archived-tickets
    def test_archived_with_no_archived_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="act-001", title="Active"), td)
        r = run_tq_env("ls", "--archived", env=_make_env(td))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    # spec: ticket-query requirement=list-tickets scenario=list-with--s-closed
    def test_closed_active_only_by_default(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        (td / "archive").mkdir()
        write_ticket(Ticket(id="done-001", title="Active closed", status="closed"), td)
        write_ticket(Ticket(id="done-002", title="Active canceled", status="canceled"), td)
        write_ticket(
            Ticket(id="done-003", title="Archived closed", status="closed"),
            td / "archive",
        )
        r = run_tq_env("ls", "--status", "closed", env=_make_env(td))
        assert "done-001" in r.stdout
        assert "done-002" not in r.stdout
        assert "done-003" not in r.stdout

    # spec: ticket-query requirement=list-tickets scenario=list-with---status-canceled
    def test_canceled_active_only_by_default(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        (td / "archive").mkdir()
        write_ticket(Ticket(id="done-001", title="Active closed", status="closed"), td)
        write_ticket(Ticket(id="done-002", title="Active canceled", status="canceled"), td)
        write_ticket(
            Ticket(id="done-003", title="Archived canceled", status="canceled"),
            td / "archive",
        )
        r = run_tq_env("ls", "--status", "canceled", env=_make_env(td))
        assert "done-002" in r.stdout
        assert "done-001" not in r.stdout
        assert "done-003" not in r.stdout


class TestLsLineFormat:
    """Tests for ls line format: checkbox status, conditional tags."""

    # spec: ticket-query requirement=list-ticket-line-format scenario=default-priority-and-type-hidden
    def test_default_priority_and_type_hidden(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-001", title="Fix login", priority=2, type="task", status="open"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "fmt-001 - [ ] Fix login" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=non-default-priority-shown
    def test_non_default_priority_shown(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-002", title="Fix login", priority=1, type="task", status="open"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "fmt-002 [P1] - [ ] Fix login" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=non-default-type-shown
    def test_non_default_type_shown(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-003", title="Add export", priority=2, type="feature", status="open"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "fmt-003 [feature] - [ ] Add export" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=both-non-default-priority-and-type-shown
    def test_both_non_default_priority_and_type(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-004", title="Refactor", priority=3, type="epic", status="open"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "fmt-004 [P3][epic] - [ ] Refactor" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=in-progress-renders-half-checkbox
    def test_in_progress_checkbox(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-005", title="Working", priority=2, type="task", status="in_progress"), td)
        r = run_tq_env("ls", env=_make_env(td))
        assert "fmt-005 - [/] Working" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=closed-renders-checked-checkbox
    def test_closed_checkbox(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-006", title="Done", status="closed"), td)
        r = run_tq_env("ls", "--status", "closed", env=_make_env(td))
        assert "[x]" in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=canceled-renders-tilde-checkbox
    def test_canceled_checkbox(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-006c", title="Abandoned", status="canceled"), td)
        r = run_tq_env("ls", "--status", "canceled", env=_make_env(td))
        assert "[~]" in r.stdout
        assert "[x]" not in r.stdout

    # spec: ticket-query requirement=list-ticket-line-format scenario=single-dependency-appended-after-title
    def test_single_dep_appended(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-007", title="Has dep", deps=["fmt-008"]), td)
        write_ticket(Ticket(id="fmt-008", title="Blocker"), td)
        r = run_tq_env("ls", env=_make_env(td))
        line = [l for l in r.stdout.splitlines() if "fmt-007" in l][0]
        assert line.rstrip().endswith("<- [fmt-008]")

    # spec: ticket-query requirement=list-ticket-line-format scenario=multiple-dependencies-appended-after-title
    def test_multi_deps_appended(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="fmt-009", title="Has deps", deps=["fmt-010", "fmt-011"]), td)
        write_ticket(Ticket(id="fmt-010", title="Blocker 1"), td)
        write_ticket(Ticket(id="fmt-011", title="Blocker 2"), td)
        r = run_tq_env("ls", env=_make_env(td))
        line = [l for l in r.stdout.splitlines() if "fmt-009" in l][0]
        assert line.rstrip().endswith("<- [fmt-010, fmt-011]")


class TestDepsBehavior:
    """Behavioral tests for `tq deps`."""

    def test_deps_tree_shows_transitive_deps(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="dep-root", title="Root", deps=["dep-a"], priority=2), td)
        write_ticket(Ticket(id="dep-a", title="Dep A", deps=["dep-b"], priority=1), td)
        write_ticket(Ticket(id="dep-b", title="Dep B", status="closed", priority=0), td)
        r = run_tq_env("deps", "dep-root", env=_make_env(td))
        assert r.returncode == 0
        assert "dep-root" in r.stdout
        assert "dep-a" in r.stdout
        assert "dep-b" in r.stdout
        assert "├──" in r.stdout or "└──" in r.stdout

    def test_deps_tree_with_multiple_children(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="dm-root", title="Root", deps=["dm-a", "dm-b"]), td)
        write_ticket(Ticket(id="dm-a", title="A"), td)
        write_ticket(Ticket(id="dm-b", title="B"), td)
        r = run_tq_env("deps", "dm-root", env=_make_env(td))
        assert "├──" in r.stdout
        assert "└──" in r.stdout

    def test_deps_full_disables_dedup(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        # Diamond: root -> a, b; a -> c; b -> c
        write_ticket(Ticket(id="dd-root", title="Root", deps=["dd-a", "dd-b"]), td)
        write_ticket(Ticket(id="dd-a", title="A", deps=["dd-c"]), td)
        write_ticket(Ticket(id="dd-b", title="B", deps=["dd-c"]), td)
        write_ticket(Ticket(id="dd-c", title="C"), td)
        # Without --full, dd-c appears once (deduped)
        r1 = run_tq_env("deps", "dd-root", env=_make_env(td))
        count_without = r1.stdout.count("dd-c")
        # With --full, dd-c appears twice
        r2 = run_tq_env("deps", "dd-root", "--full", env=_make_env(td))
        count_with = r2.stdout.count("dd-c")
        assert count_with > count_without

    def test_deps_children_sorted_by_subtree_depth_then_id(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="ds-root", title="Root", deps=["ds-shallow", "ds-deep"]), td)
        write_ticket(Ticket(id="ds-shallow", title="Shallow"), td)
        write_ticket(Ticket(id="ds-deep", title="Deep", deps=["ds-deeper"]), td)
        write_ticket(Ticket(id="ds-deeper", title="Deeper"), td)
        r = run_tq_env("deps", "ds-root", env=_make_env(td))
        lines = r.stdout.strip().splitlines()
        # Deep subtree should come first (larger subtree depth)
        deep_idx = next(i for i, l in enumerate(lines) if "ds-deep" in l and "ds-deeper" not in l)
        shallow_idx = next(i for i, l in enumerate(lines) if "ds-shallow" in l)
        assert deep_idx < shallow_idx


class TestTagsBehavior:
    """Behavioral tests for `tq tags`."""

    def test_tags_sorted_by_count_descending(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="tg-1", title="T1", tags=["ui", "backend"]), td)
        write_ticket(Ticket(id="tg-2", title="T2", tags=["ui"]), td)
        write_ticket(Ticket(id="tg-3", title="T3", tags=["backend"]), td)
        write_ticket(Ticket(id="tg-4", title="T4", tags=["ui"]), td)
        r = run_tq_env("tags", env=_make_env(td))
        assert r.returncode == 0
        lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
        assert lines[0] == "ui (3)"
        assert lines[1] == "backend (2)"

    def test_tags_excludes_closed_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="tg-open", title="Open", tags=["active"]), td)
        write_ticket(Ticket(id="tg-closed", title="Closed", status="closed", tags=["dead"]), td)
        r = run_tq_env("tags", env=_make_env(td))
        assert "active" in r.stdout
        assert "dead" not in r.stdout


class TestLinksBehavior:
    """Behavioral tests for `tq links`."""

    def test_links_lists_all_pairs(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="lk-a", title="A", links=["lk-b"]), td)
        write_ticket(Ticket(id="lk-b", title="B", links=["lk-a"]), td)
        r = run_tq_env("links", env=_make_env(td))
        assert r.returncode == 0
        assert "lk-a <-> lk-b" in r.stdout


class TestArchiveBehavior:
    """Behavioral tests for `tq archive`."""

    def test_archive_moves_closed_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-1", title="Closed", status="closed"), td)
        write_ticket(Ticket(id="arc-2", title="Open", status="open"), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert r.returncode == 0
        assert not (td / "arc-1.md").exists()
        assert (td / "archive" / "arc-1.md").exists()
        assert (td / "arc-2.md").exists()

    def test_archive_no_closed_tickets(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-3", title="Open"), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert r.returncode == 0
        assert "No closed or canceled tickets to archive" in r.stdout

    def test_archive_creates_directory(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-4", title="Closed", status="closed"), td)
        assert not (td / "archive").exists()
        run_tq_env("archive", env=_make_env(td))
        assert (td / "archive").exists()

    def test_archive_is_idempotent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-5", title="Closed", status="closed"), td)
        run_tq_env("archive", env=_make_env(td))
        r = run_tq_env("archive", env=_make_env(td))
        assert "No closed or canceled tickets to archive" in r.stdout

    def test_archived_ticket_file_intact(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-6", title="Intact check", status="closed"), td)
        original = (td / "arc-6.md").read_text()
        run_tq_env("archive", env=_make_env(td))
        archived = (td / "archive" / "arc-6.md").read_text()
        assert original == archived

    def test_archive_skips_ticket_with_dependent(self, tmp_path: Path) -> None:
        """A closed ticket referenced in another ticket's deps is not archived."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-dep", title="Dep target", status="closed"), td)
        write_ticket(Ticket(id="arc-src", title="Depends on dep", deps=["arc-dep"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert (td / "arc-dep.md").exists(), "should not be archived"
        assert "Skipped arc-dep" in r.stderr

    def test_archive_skips_ticket_with_link(self, tmp_path: Path) -> None:
        """A closed ticket linked from an active ticket is not archived."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-la", title="Linked A", status="closed"), td)
        write_ticket(Ticket(id="arc-lb", title="Linked B", links=["arc-la"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert (td / "arc-la.md").exists()
        assert "Skipped arc-la" in r.stderr

    def test_archive_skips_parent_with_children(self, tmp_path: Path) -> None:
        """A closed ticket that is the parent of another ticket is not archived."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-par", title="Parent", status="closed"), td)
        write_ticket(Ticket(id="arc-kid", title="Child", parent="arc-par"), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert (td / "arc-par.md").exists()
        assert "Skipped arc-par" in r.stderr

    def test_archive_allows_mutually_closed_group(self, tmp_path: Path) -> None:
        """Two closed tickets referencing each other can both be archived."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-ma", title="A", status="closed", links=["arc-mb"]), td)
        write_ticket(Ticket(id="arc-mb", title="B", status="closed", links=["arc-ma"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert r.returncode == 0
        assert (td / "archive" / "arc-ma.md").exists()
        assert (td / "archive" / "arc-mb.md").exists()

    def test_archive_cascade_blocks(self, tmp_path: Path) -> None:
        """If A is blocked from archive, B (referenced only by A) is also blocked."""
        td = tmp_path / ".tickets"
        td.mkdir()
        # B is closed, A is closed and depends on B, open ticket C depends on A
        write_ticket(Ticket(id="arc-cb", title="B", status="closed"), td)
        write_ticket(Ticket(id="arc-ca", title="A", status="closed", deps=["arc-cb"]), td)
        write_ticket(Ticket(id="arc-cc", title="C", deps=["arc-ca"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert (td / "arc-ca.md").exists(), "A should not be archived (C depends on it)"
        assert (td / "arc-cb.md").exists(), "B should not be archived (A stays and depends on it)"
        assert "Skipped" in r.stderr

    def test_archive_cascade_blocks_via_link(self, tmp_path: Path) -> None:
        """Link-cascade: if A is blocked, B (linked only from A) is also blocked."""
        td = tmp_path / ".tickets"
        td.mkdir()
        # B closed; A closed and links B; open C links A.
        write_ticket(Ticket(id="arc-lcb", title="B", status="closed"), td)
        write_ticket(Ticket(id="arc-lca", title="A", status="closed", links=["arc-lcb"]), td)
        write_ticket(Ticket(id="arc-lcc", title="C", links=["arc-lca"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert (td / "arc-lca.md").exists(), "A should not be archived (C links it)"
        assert (td / "arc-lcb.md").exists(), "B should not be archived (A stays and links it)"
        assert "Skipped" in r.stderr

    def test_archive_no_eligible_prints_message(self, tmp_path: Path) -> None:
        """When all terminal tickets are referenced, print a clear message."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="arc-ne", title="Referenced", status="closed"), td)
        write_ticket(Ticket(id="arc-nf", title="Referrer", deps=["arc-ne"]), td)
        r = run_tq_env("archive", env=_make_env(td))
        assert "No closed or canceled tickets eligible for archiving" in r.stdout


class TestLsParent:
    """`tq ls --parent <id>` scopes to a subtree.
    # spec: ticket-query requirement=list-filtered-by-parent
    """

    def _seed_epic(self, td: Path) -> None:
        write_ticket(Ticket(id="epic-001", title="Epic", priority=1), td)
        write_ticket(Ticket(id="task-001", title="Task one", parent="epic-001"), td)
        write_ticket(Ticket(id="task-002", title="Task two", parent="task-001"), td)
        write_ticket(Ticket(id="other-001", title="Unrelated"), td)

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-shows-itself-and-descendants
    def test_parent_shows_itself_and_descendants(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        self._seed_epic(td)
        r = run_tq_env("ls", "--parent", "epic-001", env=_make_env(td))
        assert r.returncode == 0
        assert "epic-001" in r.stdout
        assert "task-001" in r.stdout
        assert "task-002" in r.stdout
        assert "other-001" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-renders-as-tree-with-root
    def test_parent_renders_root_unindented_children_indented(
        self, tmp_path: Path,
    ) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-001", title="Epic"), td)
        write_ticket(Ticket(id="task-001", title="Task one", parent="epic-001"), td)
        r = run_tq_env("ls", "--parent", "epic-001", env=_make_env(td))
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        # Root must appear at column 0
        assert lines[0].startswith("epic-001"), lines
        # Child must be indented by box-drawing chars
        child_lines = [l for l in lines if "task-001" in l]
        assert child_lines, lines
        assert any("──" in l for l in child_lines), child_lines

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-accepts-partial-id
    def test_parent_accepts_partial_id(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-xyz-001", title="Epic"), td)
        write_ticket(Ticket(id="task-aaa-001", title="Child", parent="epic-xyz-001"), td)
        r = run_tq_env("ls", "--parent", "xyz", env=_make_env(td))
        assert r.returncode == 0, r.stderr
        assert "epic-xyz-001" in r.stdout
        assert "task-aaa-001" in r.stdout

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-with-non-existent-id
    def test_parent_unknown_id_exits_nonzero(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="real-001", title="Real"), td)
        r = run_tq_env("ls", "--parent", "nonexistent", env=_make_env(td))
        assert r.returncode != 0
        assert "ticket 'nonexistent' not found" in r.stderr

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-with-leaf-ticket-no-descendants
    def test_parent_leaf_shows_only_root(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="leaf-001", title="Leaf"), td)
        write_ticket(Ticket(id="other-001", title="Other"), td)
        r = run_tq_env("ls", "--parent", "leaf-001", env=_make_env(td))
        assert r.returncode == 0
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert len(lines) == 1, lines
        assert "leaf-001" in lines[0]
        assert "──" not in lines[0]  # no tree connectors

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-stacks-with---ready
    def test_parent_stacks_with_ready(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-001", title="Epic"), td)
        write_ticket(Ticket(id="task-001", title="Ready task", parent="epic-001"), td)
        write_ticket(Ticket(id="task-002", title="Blocked task", parent="epic-001",
                            deps=["task-003"]), td)
        write_ticket(Ticket(id="task-003", title="Open dep"), td)
        r = run_tq_env("ls", "--parent", "epic-001", "--ready", env=_make_env(td))
        assert r.returncode == 0
        assert "task-001" in r.stdout
        assert "task-002" not in r.stdout
        # Out-of-scope dep must not appear
        assert "task-003" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-stacks-with---status
    def test_parent_stacks_with_status(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-001", title="Epic"), td)
        write_ticket(Ticket(id="task-001", title="Open", parent="epic-001", status="open"), td)
        write_ticket(Ticket(id="task-002", title="Done", parent="epic-001", status="closed"), td)
        r = run_tq_env("ls", "--parent", "epic-001", "--status", "closed",
                       env=_make_env(td))
        assert "task-002" in r.stdout
        assert "task-001" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-stacks-with---tag
    def test_parent_stacks_with_tag(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-001", title="Epic"), td)
        write_ticket(Ticket(id="task-001", title="UI", parent="epic-001", tags=["ui"]), td)
        write_ticket(Ticket(id="task-002", title="Backend", parent="epic-001",
                            tags=["backend"]), td)
        r = run_tq_env("ls", "--parent", "epic-001", "--tag", "ui", env=_make_env(td))
        assert "task-001" in r.stdout
        assert "task-002" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-parent scenario=parent-root-is-shown-as-context-when-filtered-out
    def test_parent_root_shown_as_context_when_filtered_out(
        self, tmp_path: Path,
    ) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="epic-001", title="Open epic", status="open"), td)
        write_ticket(Ticket(id="task-001", title="Done task",
                            parent="epic-001", status="closed"), td)
        r = run_tq_env("ls", "--parent", "epic-001", "--status", "closed",
                       env=_make_env(td))
        assert r.returncode == 0
        # Both root (as context) and child (as match) appear; root is unindented
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert any(l.startswith("epic-001") for l in lines), lines
        assert any("task-001" in l and "──" in l for l in lines), lines

    def test_parent_does_not_climb_above_scope(self, tmp_path: Path) -> None:
        """--parent task-001 must not show grand-epic-000 even though task-001's
        parent chain reaches it."""
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="grand-epic-000", title="Grand epic"), td)
        write_ticket(Ticket(id="epic-001", title="Mid", parent="grand-epic-000"), td)
        write_ticket(Ticket(id="task-001", title="Leaf", parent="epic-001"), td)
        r = run_tq_env("ls", "--parent", "epic-001", env=_make_env(td))
        assert "epic-001" in r.stdout
        assert "task-001" in r.stdout
        assert "grand-epic-000" not in r.stdout


class TestLsDep:
    """`tq ls --dep <id>` lists direct dependents only.
    # spec: ticket-query requirement=list-filtered-by-dependent
    """

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-shows-direct-dependents
    def test_dep_shows_direct_dependents(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="Target"), td)
        write_ticket(Ticket(id="task-002", title="Depends", deps=["task-001"]), td)
        write_ticket(Ticket(id="task-003", title="Also depends", deps=["task-001"]), td)
        write_ticket(Ticket(id="other-001", title="Unrelated"), td)
        r = run_tq_env("ls", "--dep", "task-001", env=_make_env(td))
        assert r.returncode == 0
        assert "task-002" in r.stdout
        assert "task-003" in r.stdout
        assert "other-001" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-excludes-transitive-dependents
    def test_dep_excludes_transitive(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="Root"), td)
        write_ticket(Ticket(id="task-002", title="Direct", deps=["task-001"]), td)
        write_ticket(Ticket(id="task-003", title="Transitive", deps=["task-002"]), td)
        r = run_tq_env("ls", "--dep", "task-001", env=_make_env(td))
        assert "task-002" in r.stdout
        assert "task-003" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-excludes-the-target-ticket-itself
    def test_dep_excludes_self(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="Self"), td)
        write_ticket(Ticket(id="task-002", title="Dependent", deps=["task-001"]), td)
        r = run_tq_env("ls", "--dep", "task-001", env=_make_env(td))
        # Only the dependent line should be present; the target itself is excluded
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert len(lines) == 1, lines
        assert "task-002" in lines[0]

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-with-no-dependents
    def test_dep_no_dependents_empty(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="leaf-001", title="No dependents"), td)
        write_ticket(Ticket(id="other-001", title="Unrelated"), td)
        r = run_tq_env("ls", "--dep", "leaf-001", env=_make_env(td))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-accepts-partial-id
    def test_dep_accepts_partial_id(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-xyz-001", title="Target"), td)
        write_ticket(Ticket(id="task-bbb-002", title="Dep", deps=["task-xyz-001"]), td)
        r = run_tq_env("ls", "--dep", "xyz", env=_make_env(td))
        assert r.returncode == 0
        assert "task-bbb-002" in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-with-non-existent-id
    def test_dep_unknown_id_exits_nonzero(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="real-001", title="Real"), td)
        r = run_tq_env("ls", "--dep", "nonexistent", env=_make_env(td))
        assert r.returncode != 0
        assert "ticket 'nonexistent' not found" in r.stderr

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-output-is-flat-no-tree
    def test_dep_output_is_flat(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="parent-001", title="Parent"), td)
        write_ticket(Ticket(id="task-001", title="Target"), td)
        write_ticket(Ticket(id="task-002", title="Dependent",
                            parent="parent-001", deps=["task-001"]), td)
        r = run_tq_env("ls", "--dep", "task-001", env=_make_env(td))
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        assert any(l.startswith("task-002") for l in lines), lines
        # Parent must not appear as a context heading
        assert "parent-001" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-stacks-with---status
    def test_dep_stacks_with_status(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="Target"), td)
        write_ticket(Ticket(id="task-002", title="Open dep",
                            deps=["task-001"], status="open"), td)
        write_ticket(Ticket(id="task-003", title="Done dep",
                            deps=["task-001"], status="closed"), td)
        r = run_tq_env("ls", "--dep", "task-001", "--status", "open", env=_make_env(td))
        assert "task-002" in r.stdout
        assert "task-003" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=dep-stacks-with---tag
    def test_dep_stacks_with_tag(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="Target"), td)
        write_ticket(Ticket(id="task-002", title="UI dep",
                            deps=["task-001"], tags=["ui"]), td)
        write_ticket(Ticket(id="task-003", title="Backend dep",
                            deps=["task-001"], tags=["backend"]), td)
        r = run_tq_env("ls", "--dep", "task-001", "--tag", "ui", env=_make_env(td))
        assert "task-002" in r.stdout
        assert "task-003" not in r.stdout

    # spec: ticket-query requirement=list-filtered-by-dependent scenario=--parent-and---dep-mutually-exclusive
    def test_parent_and_dep_mutually_exclusive(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        write_ticket(Ticket(id="task-001", title="A"), td)
        write_ticket(Ticket(id="task-002", title="B"), td)
        r = run_tq_env("ls", "--parent", "task-001", "--dep", "task-002",
                       env=_make_env(td))
        assert r.returncode != 0

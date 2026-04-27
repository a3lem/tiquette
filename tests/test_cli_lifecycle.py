"""Tests for lifecycle command argument parsing and behavior.
# spec: ticket-lifecycle
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


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


class TestCreateArgs:
    """Argument parsing for `tq create`."""

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-title
    def test_create_with_title(self) -> None:
        result = run_tq("create", "My ticket")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-default-title
    def test_create_no_title(self) -> None:
        result = run_tq("create")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-description
    def test_create_with_description(self) -> None:
        result = run_tq("create", "Test", "-d", "A description")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-type
    def test_create_with_type(self) -> None:
        result = run_tq("create", "Test", "-t", "bug")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-rejects-invalid-type
    def test_create_with_invalid_type(self) -> None:
        result = run_tq("create", "Test", "-t", "invalid")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-priority
    def test_create_with_priority(self) -> None:
        result = run_tq("create", "Test", "-p", "0")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-rejects-invalid-priority
    def test_create_with_invalid_priority(self) -> None:
        result = run_tq("create", "Test", "-p", "5")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-rejects-negative-priority
    def test_create_with_negative_priority(self) -> None:
        result = run_tq("create", "Test", "-p", "-1")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-assignee
    def test_create_with_assignee(self) -> None:
        result = run_tq("create", "Test", "-a", "Alice")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-external-reference
    def test_create_with_ref(self) -> None:
        result = run_tq("create", "Test", "--xref", "JIRA-123")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-parent
    def test_create_with_parent(self) -> None:
        result = run_tq("create", "Test", "--parent", "parent-001")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-tags
    def test_create_with_tags(self) -> None:
        result = run_tq("create", "Test", "--tag", "ui", "--tag", "backend")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-deps
    def test_create_with_deps(self) -> None:
        result = run_tq("create", "Test", "--dep", "dep-001", "--dep", "dep-002")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket
    def test_create_with_all_flags(self) -> None:
        result = run_tq(
            "create", "Full ticket",
            "-d", "desc", "-t", "bug", "-p", "1", "-a", "Alice",
            "--xref", "GH-42", "--parent", "p-001",
            "--tag", "ui", "--tag", "api", "--dep", "d-001",
        )
        assert result.returncode == 0


class TestStatusTransitionArgs:
    """Argument parsing for status transition commands."""

    # spec: ticket-lifecycle requirement=start-command scenario=start-sets-in_progress
    def test_start_requires_id(self) -> None:
        result = run_tq("start")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=start-command scenario=start-sets-in_progress
    def test_start_accepts_id(self) -> None:
        result = run_tq("start", "test-0001")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-completed
    def test_close_requires_id(self) -> None:
        result = run_tq("close")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-completed
    def test_close_accepts_id(self) -> None:
        result = run_tq("close", "test-0001")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=cancel-command scenario=cancel-sets-canceled
    def test_cancel_requires_id(self) -> None:
        result = run_tq("cancel")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=cancel-command scenario=cancel-sets-canceled
    def test_cancel_accepts_id(self) -> None:
        result = run_tq("cancel", "test-0001")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-sets-open-and-clears-resolution
    def test_reopen_requires_id(self) -> None:
        result = run_tq("reopen")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-sets-open-and-clears-resolution
    def test_reopen_accepts_id(self) -> None:
        result = run_tq("reopen", "test-0001")
        assert result.returncode == 0


def _read_ticket_file(tickets_dir: Path, ticket_id: str) -> str:
    """Read ticket file content by ID."""
    return (tickets_dir / f"{ticket_id}.md").read_text()


def _find_ticket_id(tickets_dir: Path) -> str:
    """Find the single ticket file in the directory and return its ID."""
    files = list(tickets_dir.glob("*.md"))
    assert len(files) == 1, f"Expected 1 ticket file, found {len(files)}"
    return files[0].stem


class TestCreateBehavior:
    """Full behavioral tests for `tq create` -- verifies file output."""

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-title
    def test_create_prints_id_and_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        result = run_tq("create", "My first ticket", env={"TICKETS_DIR": str(tmp_path / ".tickets")})
        assert result.returncode == 0
        ticket_id = result.stdout.strip()
        assert re.match(r".+-[a-f0-9]{4}$", ticket_id)

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-title
    def test_create_writes_file_with_title(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "My first ticket", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "# My first ticket" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-default-title
    def test_create_default_title(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "# Untitled" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-description
    def test_create_with_description(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Test", "-d", "A detailed description", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "## Description" in content
        assert "A detailed description" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-type
    def test_create_with_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Bug", "-t", "bug", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "type: bug" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-priority
    def test_create_with_priority(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Urgent", "-p", "0", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "priority: 0" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-assignee
    def test_create_with_assignee(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Task", "-a", "John Doe", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "assignee: John Doe" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-external-reference
    def test_create_with_xref(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Task", "--xref", "JIRA-123", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "xref: JIRA-123" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-parent
    def test_create_with_parent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Child", "--parent", "parent-001", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "parent: parent-001" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-tags
    def test_create_with_tags(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Tagged", "--tag", "ui", "--tag", "backend", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "tags: [ui, backend]" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-deps
    def test_create_with_deps(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Blocked", "--dep", "dep-001", "--dep", "dep-002", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "deps: [dep-001, dep-002]" in content

    # spec: ticket-lifecycle requirement=default-field-values
    def test_create_default_fields(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Defaults", env={"TICKETS_DIR": str(tickets_dir)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "status: open" in content
        assert "priority: 2" in content
        assert "type: task" in content
        assert "deps: []" in content
        assert "links: []" in content
        assert "tags: []" in content
        assert "assignee" not in content  # nullable fields omitted when null
        # created should be valid ISO 8601
        for line in content.splitlines():
            if line.startswith("created: "):
                ts = line.split("created: ", 1)[1]
                from datetime import datetime
                datetime.fromisoformat(ts)
                break
        else:
            pytest.fail("no 'created' field in frontmatter")

    # spec: ticket-lifecycle requirement=tickets-directory-auto-creation
    def test_create_auto_creates_tickets_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        assert not tickets_dir.exists()
        result = run_tq("create", "First", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert tickets_dir.exists()


def _make_ticket(
    ticket_id: str,
    title: str = "Test ticket",
    status: str = "open",
    resolution: str | None = None,
    parent: str | None = None,
) -> "Ticket":
    from tiquette.store import Ticket
    return Ticket(
        id=ticket_id, title=title, status=status,
        resolution=resolution, parent=parent,
    )


class TestStatusTransitionBehavior:
    """Behavioral tests for start/close/cancel/reopen commands."""

    # spec: ticket-lifecycle requirement=start-command scenario=start-sets-in_progress
    def test_start_sets_in_progress(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("start", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert read_ticket("test-0001", tickets_dir).status == "in_progress"

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-completed
    def test_close_sets_completed(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        t = read_ticket("test-0001", tickets_dir)
        assert t.status == "closed"
        assert t.resolution == "completed"

    # spec: ticket-lifecycle requirement=close-command scenario=close-rejects-parent-with-open-children
    def test_close_rejects_parent_with_open_children(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", title="Parent"), tickets_dir)
        write_ticket(_make_ticket("test-0002", title="Child", parent="test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert "has open descendants" in result.stderr
        assert "test-0002" in result.stderr
        assert read_ticket("test-0001", tickets_dir).status == "open"

    # spec: ticket-lifecycle requirement=close-command scenario=close-succeeds-when-all-children-closed
    def test_close_succeeds_when_all_children_closed(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="closed", resolution="completed", parent="test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-rejects-grandparent-with-open-grandchild
    def test_close_rejects_grandparent_with_open_grandchild(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="closed", resolution="completed", parent="test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0003", parent="test-0002"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert "has open descendants" in result.stderr
        assert "test-0003" in result.stderr

    # spec: ticket-lifecycle requirement=close-command scenario=close-ticket-with-no-children
    def test_close_ticket_with_no_children(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-notifies-last-open-child
    def test_close_notifies_last_open_child(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", title="Parent"), tickets_dir)
        write_ticket(_make_ticket("test-0002", title="Last child", parent="test-0001"), tickets_dir)
        result = run_tq("close", "test-0002", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "test-0001" in result.stdout
        assert "no remaining open children" in result.stdout

    # spec: ticket-lifecycle requirement=cancel-command scenario=cancel-sets-canceled
    def test_cancel_sets_canceled(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("cancel", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        t = read_ticket("test-0001", tickets_dir)
        assert t.status == "closed"
        assert t.resolution == "canceled"

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-sets-open-and-clears-resolution
    def test_reopen_sets_open_and_clears_resolution(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", status="closed", resolution="completed"), tickets_dir)
        result = run_tq("reopen", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        t = read_ticket("test-0001", tickets_dir)
        assert t.status == "open"
        assert t.resolution is None

    # spec: ticket-lifecycle requirement=invalid-operations scenario=nonexistent-ticket
    def test_nonexistent_ticket(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        result = run_tq("start", "nonexistent", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert "ticket" in result.stderr and "not found" in result.stderr


class TestTransitionOutput:
    """Transition commands print the ticket ID to stdout on success."""

    # spec: ticket-lifecycle requirement=transition-output scenario=start-prints-ticket-id
    def test_start_prints_ticket_id(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("start", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "test-0001" in result.stdout

    # spec: ticket-lifecycle requirement=transition-output scenario=close-prints-ticket-id
    def test_close_prints_ticket_id(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "test-0001" in result.stdout

    # spec: ticket-lifecycle requirement=transition-output scenario=cancel-prints-ticket-id
    def test_cancel_prints_ticket_id(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("cancel", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "test-0001" in result.stdout

    # spec: ticket-lifecycle requirement=transition-output scenario=reopen-prints-ticket-id
    def test_reopen_prints_ticket_id(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", status="closed", resolution="completed"), tickets_dir)
        result = run_tq("reopen", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "test-0001" in result.stdout

    # spec: ticket-lifecycle requirement=transition-output scenario=failed-transition-does-not-print-id
    def test_failed_transition_prints_nothing_to_stdout(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        result = run_tq("close", "nonexistent", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert result.stdout == ""

"""Tests for lifecycle command argument parsing and behavior.
# spec: ticket-lifecycle
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from tiquette.store import Ticket


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

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-without-title-is-rejected
    def test_create_no_title(self) -> None:
        result = run_tq("create")
        assert result.returncode != 0

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

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-assignee-short-flag
    def test_create_with_assignee(self) -> None:
        result = run_tq("create", "Test", "-A", "Alice")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-assignee-long-flag
    def test_create_with_assignee_long(self) -> None:
        result = run_tq("create", "Test", "--assignee", "Alice")
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=create-ticket scenario=-a-is-no-longer-accepted-for---assignee
    def test_create_lowercase_a_rejected(self) -> None:
        result = run_tq("create", "Test", "-a", "Alice")
        assert result.returncode != 0

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
            "-d", "desc", "-t", "bug", "-p", "1", "-A", "Alice",
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

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-closed
    def test_close_requires_id(self) -> None:
        result = run_tq("close")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-closed
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

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-from-closed
    def test_reopen_requires_id(self) -> None:
        result = run_tq("reopen")
        assert result.returncode != 0

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-from-closed
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

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-without-title-is-rejected
    def test_create_no_title_rejected(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert result.stderr  # argparse should emit usage error

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
        result = run_tq("create", "Task", "-A", "John Doe", env={"TICKETS_DIR": str(tickets_dir)})
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
        from tiquette.store import write_ticket
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        # v1.2: create --parent validates the parent exists
        write_ticket(Ticket(id="parent-001", title="Parent"), tickets_dir)
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
        from tiquette.store import write_ticket
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        # v1.2: create --dep validates each dep target exists
        write_ticket(Ticket(id="dep-001", title="Dep 1"), tickets_dir)
        write_ticket(Ticket(id="dep-002", title="Dep 2"), tickets_dir)
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
    parent: str | None = None,
) -> Ticket:
    return Ticket(
        id=ticket_id, title=title, status=status,
        parent=parent,
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

    # spec: ticket-lifecycle requirement=close-command scenario=close-sets-closed
    def test_close_sets_closed(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        t = read_ticket("test-0001", tickets_dir)
        assert t.status == "closed"
        content = (tickets_dir / "test-0001.md").read_text()
        assert "resolution" not in content
        assert "status: completed" not in content

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

    # spec: ticket-lifecycle requirement=close-command scenario=close-succeeds-when-all-children-are-terminal
    def test_close_succeeds_when_all_children_closed(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="closed", parent="test-0001"), tickets_dir)
        result = run_tq("close", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0

    # spec: ticket-lifecycle requirement=close-command scenario=close-rejects-grandparent-with-non-terminal-grandchild
    def test_close_rejects_grandparent_with_open_grandchild(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="canceled", parent="test-0001"), tickets_dir)
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
        assert t.status == "canceled"
        content = (tickets_dir / "test-0001.md").read_text()
        assert "resolution" not in content

    # spec: ticket-lifecycle requirement=cancel-command scenario=cancel-rejects-parent-with-open-children
    def test_cancel_rejects_parent_with_open_children(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", title="Parent"), tickets_dir)
        write_ticket(_make_ticket("test-0002", title="Child", parent="test-0001"), tickets_dir)
        result = run_tq("cancel", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert "has open descendants" in result.stderr
        assert "test-0002" in result.stderr
        assert read_ticket("test-0001", tickets_dir).status == "open"

    # spec: ticket-lifecycle requirement=cancel-command scenario=cancel-succeeds-when-all-descendants-are-terminal
    def test_cancel_succeeds_when_all_descendants_closed(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="closed", parent="test-0001"), tickets_dir)
        result = run_tq("cancel", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert read_ticket("test-0001", tickets_dir).status == "canceled"

    # spec: ticket-lifecycle requirement=cancel-command scenario=force-cancel-cascades-to-non-terminal-descendants
    def test_force_cancel_cascades(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", parent="test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0003", status="in_progress", parent="test-0002"), tickets_dir)
        result = run_tq("cancel", "-f", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        for tid in ("test-0001", "test-0002", "test-0003"):
            assert read_ticket(tid, tickets_dir).status == "canceled", tid

    # spec: ticket-lifecycle requirement=cancel-command scenario=force-cancel-leaves-already-terminal-descendants-untouched
    def test_force_cancel_skips_closed_descendants(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="closed", parent="test-0001"), tickets_dir)
        result = run_tq("cancel", "--force", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert read_ticket("test-0002", tickets_dir).status == "closed"
        assert read_ticket("test-0001", tickets_dir).status == "canceled"

    # spec: ticket-lifecycle requirement=close-command scenario=force-close-cascades-to-non-terminal-descendants
    def test_force_close_cascades(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", parent="test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0003", status="in_progress", parent="test-0002"), tickets_dir)
        result = run_tq("close", "-f", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        for tid in ("test-0001", "test-0002", "test-0003"):
            assert read_ticket(tid, tickets_dir).status == "closed", tid

    # spec: ticket-lifecycle requirement=close-command scenario=force-close-leaves-already-terminal-descendants-untouched
    def test_force_close_skips_closed_descendants(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001"), tickets_dir)
        write_ticket(_make_ticket("test-0002", status="canceled", parent="test-0001"), tickets_dir)
        result = run_tq("close", "--force", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert read_ticket("test-0002", tickets_dir).status == "canceled"
        assert read_ticket("test-0001", tickets_dir).status == "closed"

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-from-closed
    def test_reopen_sets_open_from_closed(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", status="closed"), tickets_dir)
        result = run_tq("reopen", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        t = read_ticket("test-0001", tickets_dir)
        assert t.status == "open"
        assert "resolution" not in (tickets_dir / "test-0001.md").read_text()

    # spec: ticket-lifecycle requirement=reopen-command scenario=reopen-from-canceled
    def test_reopen_sets_open_from_canceled(self, tmp_path: Path) -> None:
        from tiquette.store import read_ticket, write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("test-0001", status="canceled"), tickets_dir)
        result = run_tq("reopen", "test-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert read_ticket("test-0001", tickets_dir).status == "open"

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
        write_ticket(_make_ticket("test-0001", status="closed"), tickets_dir)
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

    # spec: ticket-lifecycle requirement=transition-output scenario=force-close-prints-all-affected-ids
    def test_force_close_prints_all_ids(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("par-0001"), tickets_dir)
        write_ticket(_make_ticket("par-0002", parent="par-0001"), tickets_dir)
        result = run_tq("close", "-f", "par-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "par-0001" in result.stdout
        assert "par-0002" in result.stdout

    # spec: ticket-lifecycle requirement=transition-output scenario=force-cancel-prints-all-affected-ids
    def test_force_cancel_prints_all_ids(self, tmp_path: Path) -> None:
        from tiquette.store import write_ticket
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(_make_ticket("par-0001"), tickets_dir)
        write_ticket(_make_ticket("par-0002", parent="par-0001"), tickets_dir)
        result = run_tq("cancel", "-f", "par-0001", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        assert "par-0001" in result.stdout
        assert "par-0002" in result.stdout


class TestCreateWithLink:
    """Create with --link flag writes symmetric links."""

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-links-is-symmetric
    def test_create_with_link_symmetric(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        from tiquette.store import Ticket, write_ticket, read_ticket
        write_ticket(Ticket(id="rel-001", title="Existing"), tickets_dir)

        result = run_tq("create", "Related ticket", "--link", "rel-001",
                        env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        new_id = result.stdout.strip()
        assert new_id  # non-empty ID printed

        # New ticket references rel-001
        new_content = _read_ticket_file(tickets_dir, new_id)
        assert "rel-001" in new_content

        # rel-001 back-references the new ticket
        rel_content = _read_ticket_file(tickets_dir, "rel-001")
        assert new_id in rel_content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-links-is-symmetric
    def test_create_with_link_arg_accepted(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        from tiquette.store import Ticket, write_ticket
        write_ticket(Ticket(id="lnk-001", title="Target"), tickets_dir)
        result = run_tq("create", "Linked ticket", "--link", "lnk-001",
                        env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0


class TestCascadeOrder:
    """Force-close/cancel writes descendants before the parent (parent-last invariant)."""

    def test_parent_still_open_if_write_raises_before_parent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from unittest.mock import patch
        from tiquette.store import Ticket, write_ticket, read_ticket
        import tiquette.commands.lifecycle as lc

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        monkeypatch.setenv("TICKETS_DIR", str(tickets_dir))
        write_ticket(Ticket(id="par-0001", title="Parent"), tickets_dir)
        write_ticket(Ticket(id="chd-0001", title="Child", parent="par-0001"), tickets_dir)

        original_write = write_ticket
        written: list[str] = []

        def failing_write(ticket: Ticket, td: Path) -> Path:
            if ticket.id == "par-0001" and "chd-0001" in written:
                raise OSError("simulated disk failure")
            result = original_write(ticket, td)
            written.append(ticket.id)
            return result

        with patch.object(lc, "write_ticket", side_effect=failing_write):
            import argparse
            ns = argparse.Namespace(id="par-0001", target_status=lc.Status.CLOSED, force=True)
            try:
                lc._handle_status(ns)
            except (OSError, SystemExit):
                pass

        # Child was written; parent was not (failure before parent write)
        assert "chd-0001" in written
        assert "par-0001" not in written
        # Parent on disk is still open
        assert read_ticket("par-0001", tickets_dir).status == "open"
        # Child on disk is closed (descendant write succeeded)
        assert read_ticket("chd-0001", tickets_dir).status == "closed"


class TestCreateWithNote:
    """Create with --note flag writes timestamped notes matching created timestamp."""

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-note
    def test_create_with_note_creates_notes_section(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Kickoff ticket", "--note", "initial context",
                        env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)
        assert "## Notes" in content
        assert "initial context" in content

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-note
    def test_create_with_note_timestamp_matches_created(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import re as _re
        from datetime import datetime
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Kickoff ticket", "--note", "initial context",
                        env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)

        # Extract created timestamp from frontmatter
        created_match = _re.search(r"^created: (.+)$", content, _re.MULTILINE)
        assert created_match, "no 'created' field found"
        created_ts = created_match.group(1).strip()

        # The note should carry the same ISO 8601 timestamp
        assert created_ts in content, (
            f"note timestamp {created_ts!r} not found in ticket content"
        )

    # spec: ticket-lifecycle requirement=create-ticket scenario=create-with-multiple-notes-shares-one-timestamp
    def test_create_with_multiple_notes_share_timestamp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import re as _re
        monkeypatch.chdir(tmp_path)
        tickets_dir = tmp_path / ".tickets"
        result = run_tq("create", "Multi-note", "--note", "first", "--note", "second",
                        env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(tickets_dir, ticket_id)

        assert "first" in content
        assert "second" in content

        # Extract all ISO 8601-looking timestamps from the Notes section
        notes_section_match = _re.search(r"## Notes\n(.+)", content, _re.DOTALL)
        assert notes_section_match, "no Notes section found"
        notes_text = notes_section_match.group(1)

        # Both notes must appear in order
        first_pos = notes_text.find("first")
        second_pos = notes_text.find("second")
        assert first_pos != -1 and second_pos != -1
        assert first_pos < second_pos, "notes not in insertion order"

        # Both should share the created timestamp (one timestamp per invocation)
        created_match = _re.search(r"^created: (.+)$", content, _re.MULTILINE)
        assert created_match
        created_ts = created_match.group(1).strip()
        # Both notes carry the shared timestamp — count occurrences
        assert content.count(created_ts) >= 2, (
            "expected both notes to carry the same timestamp"
        )

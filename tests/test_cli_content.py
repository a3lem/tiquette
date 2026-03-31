"""Tests for content command argument parsing and behavior.
# spec: ticket-content
"""
from __future__ import annotations

import os
import re
import subprocess
import typing as T
from pathlib import Path

import pytest


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


def run_tq_env(
    *args: str,
    env: dict[str, str] | None = None,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True, text=True, env=run_env, input=stdin_text,
    )


TICKET_TEMPLATE = """\
---
id: {ticket_id}
status: open
type: task
priority: 2
assignee: null
deps: []
links: []
parent: null
tags: []
xref: null
resolution: null
created: 2026-01-01T00:00:00+00:00
---
# {title}

## Description

{description}
"""

TICKET_WITH_NOTES_TEMPLATE = """\
---
id: {ticket_id}
status: open
type: task
priority: 2
assignee: null
deps: []
links: []
parent: null
tags: []
xref: null
resolution: null
created: 2026-01-01T00:00:00+00:00
---
# {title}

## Description

{description}

## Notes

{notes}
"""


def _create_ticket(
    tickets_dir: Path,
    ticket_id: str,
    title: str = "Test Ticket",
    description: str = "Some description.",
    notes: str | None = None,
) -> Path:
    tickets_dir.mkdir(parents=True, exist_ok=True)
    path = tickets_dir / f"{ticket_id}.md"
    if notes is not None:
        content = TICKET_WITH_NOTES_TEMPLATE.format(
            ticket_id=ticket_id, title=title,
            description=description, notes=notes,
        )
    else:
        content = TICKET_TEMPLATE.format(
            ticket_id=ticket_id, title=title, description=description,
        )
    path.write_text(content)
    return path


class TestDescribeArgs:
    """Argument parsing for `tq describe`."""

    def test_describe_requires_id_and_text(self) -> None:
        result = run_tq("describe", "t-001")
        assert result.returncode != 0

    def test_describe_accepts_id_and_text(self) -> None:
        result = run_tq("describe", "t-001", "New description")
        assert result.returncode == 0


class TestAddNoteArgs:
    """Argument parsing for `tq add-note`."""

    def test_add_note_accepts_id_and_text(self) -> None:
        result = run_tq("add-note", "t-001", "This is my note")
        assert result.returncode == 0

    # text is now optional (stdin support per spec)
    def test_add_note_accepts_id_only(self) -> None:
        result = run_tq("add-note", "t-001")
        assert result.returncode == 0


class TestContentBehavior:
    """Integration tests for describe and add-note behavior."""

    # spec: ticket-content requirement=describe scenario=set-description
    def test_describe_sets_description(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "desc-0001", description="Old desc.")
        result = run_tq_env("describe", "desc-0001", "New description", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        content = ticket_path.read_text()
        assert "New description" in content
        assert "Old desc." not in content

    # spec: ticket-content requirement=describe scenario=replace-existing-description
    def test_describe_replaces_existing(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "desc-0001", description="First version.")
        env = {"TICKETS_DIR": str(tickets_dir)}
        run_tq_env("describe", "desc-0001", "Second version", env=env)
        run_tq_env("describe", "desc-0001", "Third version", env=env)
        content = ticket_path.read_text()
        assert "Third version" in content
        assert "Second version" not in content

    # spec: ticket-content requirement=add-note scenario=add-a-note
    def test_add_note_exits_zero(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        _create_ticket(tickets_dir, "note-0001")
        result = run_tq_env("add-note", "note-0001", "This is my note", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0

    def test_add_note_appears_in_file(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "note-0001")
        run_tq_env("add-note", "note-0001", "This is my note", env={"TICKETS_DIR": str(tickets_dir)})
        content = ticket_path.read_text()
        assert "## Notes" in content
        assert "This is my note" in content

    # spec: ticket-content requirement=add-note scenario=note-has-timestamp
    def test_add_note_has_timestamp(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "note-0001")
        run_tq_env("add-note", "note-0001", "Timestamped", env={"TICKETS_DIR": str(tickets_dir)})
        content = ticket_path.read_text()
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", content)

    # spec: ticket-content requirement=add-note scenario=multiple-notes-are-appended
    def test_add_note_multiple_appended_in_order(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "note-0001")
        env = {"TICKETS_DIR": str(tickets_dir)}
        run_tq_env("add-note", "note-0001", "First note", env=env)
        run_tq_env("add-note", "note-0001", "Second note", env=env)
        content = ticket_path.read_text()
        assert content.index("First note") < content.index("Second note")

    # spec: ticket-content requirement=add-note scenario=add-note-to-ticket-with-existing-notes
    def test_add_note_to_existing_notes_section(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(
            tickets_dir, "note-0001",
            notes="- 2026-01-15T10:30:00+00:00: Existing note",
        )
        run_tq_env("add-note", "note-0001", "New note", env={"TICKETS_DIR": str(tickets_dir)})
        content = ticket_path.read_text()
        assert "Existing note" in content
        assert "New note" in content
        assert content.index("Existing note") < content.index("New note")

    # spec: ticket-content requirement=add-note scenario=empty-note-adds-timestamp-only
    def test_add_note_empty_text(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        ticket_path = _create_ticket(tickets_dir, "note-0001")
        result = run_tq_env("add-note", "note-0001", "", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0
        content = ticket_path.read_text()
        assert re.search(r"- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*:$", content, re.MULTILINE)

    # spec: ticket-content requirement=add-note scenario=non-existent-ticket
    def test_add_note_nonexistent_ticket(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir(parents=True)
        result = run_tq_env("add-note", "nonexistent", "A note", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode != 0
        assert "ticket 'nonexistent' not found" in result.stderr

    # spec: ticket-content requirement=add-note scenario=add-note-via-stdin
    def test_add_note_via_stdin(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        _create_ticket(tickets_dir, "note-0001")
        result = run_tq_env(
            "add-note", "note-0001",
            env={"TICKETS_DIR": str(tickets_dir)},
            stdin_text="Piped note content",
        )
        assert result.returncode == 0
        content = (tickets_dir / "note-0001.md").read_text()
        assert "Piped note content" in content

    # spec: ticket-content requirement=add-note scenario=partial-id
    def test_add_note_partial_id(self, tmp_path: Path) -> None:
        tickets_dir = tmp_path / ".tickets"
        _create_ticket(tickets_dir, "note-0001")
        result = run_tq_env("add-note", "0001", "A note", env={"TICKETS_DIR": str(tickets_dir)})
        assert result.returncode == 0

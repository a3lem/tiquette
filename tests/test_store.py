"""Tests for the ticket store layer.
# spec: ticket-store
"""
from __future__ import annotations

import os
import re
import typing as T
from datetime import datetime
from pathlib import Path

import pytest


class TestFindTicketsDir:
    """Directory walking to locate .tickets/."""

    # spec: ticket-store requirement=directory-walking scenario=find-in-current-dir
    def test_find_in_current_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tiquette.store import find_tickets_dir

        monkeypatch.delenv("TICKETS_DIR", raising=False)
        tickets = tmp_path / ".tickets"
        tickets.mkdir()
        monkeypatch.chdir(tmp_path)
        assert find_tickets_dir() == tickets

    # spec: ticket-store requirement=directory-walking scenario=find-in-parent-dir
    def test_find_in_parent_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tiquette.store import find_tickets_dir

        monkeypatch.delenv("TICKETS_DIR", raising=False)
        tickets = tmp_path / ".tickets"
        tickets.mkdir()
        child = tmp_path / "sub"
        child.mkdir()
        monkeypatch.chdir(child)
        assert find_tickets_dir() == tickets

    # spec: ticket-store requirement=directory-walking scenario=find-in-grandparent-dir
    def test_find_in_grandparent_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tiquette.store import find_tickets_dir

        monkeypatch.delenv("TICKETS_DIR", raising=False)
        tickets = tmp_path / ".tickets"
        tickets.mkdir()
        deep = tmp_path / "a" / "b"
        deep.mkdir(parents=True)
        monkeypatch.chdir(deep)
        assert find_tickets_dir() == tickets

    # spec: ticket-store requirement=directory-walking scenario=env-var-takes-priority
    def test_env_var_takes_priority(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tiquette.store import find_tickets_dir

        # Create .tickets in tmp_path but point env elsewhere
        (tmp_path / ".tickets").mkdir()
        override = tmp_path / "custom_tickets"
        override.mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("TICKETS_DIR", str(override))
        assert find_tickets_dir() == override

    # spec: ticket-store requirement=directory-walking scenario=error-when-not-found
    def test_error_when_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tiquette.store import TicketsNotFoundError, find_tickets_dir

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("TICKETS_DIR", raising=False)
        with pytest.raises(TicketsNotFoundError):
            find_tickets_dir()


class TestGenerateId:
    """ID generation using directory name prefix + hex suffix."""

    # spec: ticket-store requirement=id-generation scenario=single-word-directory
    def test_id_format_single_word(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "myproj"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"mypr-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=multi-word-directory-with-four-or-more-tokens
    def test_id_format_four_tokens(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "my-cool-awesome-project"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"mcap-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=multi-word-directory-with-fewer-than-four-tokens
    def test_id_format_short_tokens(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "ai-ml-research"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"amrh-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=vowel-ending-replaced-by-next-consonant-in-single-token-name
    def test_id_format_single_token_vowel_swap(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "tiquette"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"tiqt-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=vowel-ending-replaced-by-consonant-scanned-back-in-multi-token-fill
    def test_id_format_multi_token_vowel_swap(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "ai-ml-data"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"amdt-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=falls-back-to-3-char-prefix-when-no-consonant-available-and-char-3-is-consonant
    def test_id_format_three_char_fallback(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "strae"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"str-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=keeps-vowel-ending-when-char-3-is-also-a-vowel
    def test_id_format_keeps_vowel_when_char3_vowel(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "stoau"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        assert re.match(r"stoa-[a-f0-9]{4}$", ticket_id), ticket_id

    # spec: ticket-store requirement=id-generation scenario=uniqueness
    def test_ids_are_unique(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ids = {generate_id(tickets_dir) for _ in range(20)}
        # With 4 hex chars (65536 possibilities), 20 should all be unique
        assert len(ids) == 20

    # spec: ticket-store requirement=id-generation scenario=no-collision-with-existing
    def test_no_collision_with_existing(self, tmp_path: Path) -> None:
        from tiquette.store import generate_id

        project_dir = tmp_path / "proj"
        project_dir.mkdir()
        tickets_dir = project_dir / ".tickets"
        tickets_dir.mkdir()

        ticket_id = generate_id(tickets_dir)
        # File does not already exist
        assert not (tickets_dir / f"{ticket_id}.md").exists()


class TestTicketDataclass:
    """Ticket data model."""

    # spec: ticket-store requirement=ticket-file-format scenario=default-fields
    def test_defaults(self) -> None:
        from tiquette.store import Ticket

        t = Ticket(id="test-0001", title="Hello")
        assert t.status == "open"
        assert t.type == "task"
        assert t.priority == 2
        assert t.assignee is None
        assert t.deps == []
        assert t.links == []
        assert t.parent is None
        assert t.tags == []
        assert t.xref is None
        assert t.resolution is None
        assert t.created is not None
        # created should be valid ISO 8601
        datetime.fromisoformat(t.created)

    def test_custom_fields(self) -> None:
        from tiquette.store import Ticket

        t = Ticket(
            id="proj-abcd",
            title="Bug report",
            status="in_progress",
            type="bug",
            priority=0,
            assignee="Alice",
            deps=["dep-001"],
            links=["link-001"],
            parent="parent-001",
            tags=["ui", "backend"],
            xref="JIRA-123",
            resolution=None,
            created="2026-01-01T00:00:00",
            description="Some details",
        )
        assert t.id == "proj-abcd"
        assert t.type == "bug"
        assert t.priority == 0
        assert t.tags == ["ui", "backend"]


class TestWriteTicket:
    """Writing tickets to disk as YAML frontmatter + markdown."""

    # spec: ticket-store requirement=ticket-file-format scenario=file-structure
    def test_write_creates_file(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="My ticket")
        write_ticket(t, tickets_dir)
        assert (tickets_dir / "proj-0001.md").exists()

    def test_write_frontmatter_structure(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test ticket", description="Some body text")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        # Starts with frontmatter delimiter
        assert content.startswith("---\n")
        # Has closing delimiter
        parts = content.split("---\n")
        # parts[0] is empty (before first ---), parts[1] is frontmatter, rest is body
        assert len(parts) >= 3

        frontmatter = parts[1]
        assert "id: proj-0001" in frontmatter
        assert "status: open" in frontmatter
        assert "type: task" in frontmatter
        assert "priority: 2" in frontmatter

    def test_write_title_as_heading(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="My first ticket")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "# My first ticket" in content

    def test_write_description_section(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test", description="A detailed description")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "## Description" in content
        assert "A detailed description" in content

    def test_write_no_description_section_when_none(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "## Description" not in content

    def test_write_lists_as_flow_style(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(
            id="proj-0001",
            title="Test",
            tags=["ui", "backend"],
            deps=["dep-001", "dep-002"],
        )
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "tags: [ui, backend]" in content
        assert "deps: [dep-001, dep-002]" in content

    def test_write_empty_lists(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "deps: []" in content
        assert "links: []" in content
        assert "tags: []" in content

    # spec: ticket-store requirement=ticket-file-format scenario=file-structure
    def test_write_nullable_fields_absent_when_none(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test")
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        # Nullable fields must be absent when null, not written as "null"
        assert "assignee" not in content
        assert "resolution" not in content
        assert "parent" not in content
        assert "xref" not in content

    # spec: ticket-store requirement=ticket-file-format scenario=nullable-fields-present-when-non-null
    def test_write_nullable_fields_present_when_set(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(
            id="proj-0001", title="Test",
            assignee="Alice", parent="parent-001",
            xref="gh-42", resolution="completed",
        )
        write_ticket(t, tickets_dir)

        content = (tickets_dir / "proj-0001.md").read_text()
        assert "assignee: Alice" in content
        assert "parent: parent-001" in content
        assert "xref: gh-42" in content
        assert "resolution: completed" in content


class TestReadTicket:
    """Reading and parsing ticket files."""

    def test_roundtrip(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, read_ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        original = Ticket(
            id="proj-abcd",
            title="Roundtrip test",
            type="bug",
            priority=1,
            assignee="Bob",
            tags=["urgent", "api"],
            deps=["dep-001"],
            links=["link-001"],
            parent="parent-001",
            xref="GH-42",
            description="Body text here",
        )
        write_ticket(original, tickets_dir)
        loaded = read_ticket("proj-abcd", tickets_dir)

        assert loaded.id == original.id
        assert loaded.title == original.title
        assert loaded.status == original.status
        assert loaded.type == original.type
        assert loaded.priority == original.priority
        assert loaded.assignee == original.assignee
        assert loaded.tags == original.tags
        assert loaded.deps == original.deps
        assert loaded.links == original.links
        assert loaded.parent == original.parent
        assert loaded.xref == original.xref
        assert loaded.created == original.created
        assert loaded.description == original.description

    def test_read_nonexistent_ticket(self, tmp_path: Path) -> None:
        from tiquette.store import TicketNotFoundError, read_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        with pytest.raises(TicketNotFoundError):
            read_ticket("nonexistent-0001", tickets_dir)

    def test_read_ticket_without_description(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, read_ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        original = Ticket(id="proj-0001", title="No desc")
        write_ticket(original, tickets_dir)
        loaded = read_ticket("proj-0001", tickets_dir)
        assert loaded.description is None
        assert loaded.title == "No desc"


class TestResolveId:
    """Partial ID resolution.
    # spec: id-resolution requirement=partial-id-matching
    """

    def test_exact_match(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="test"), tickets_dir)
        assert resolve_id("abc-1234", tickets_dir) == "abc-1234"

    def test_partial_suffix(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="test"), tickets_dir)
        assert resolve_id("1234", tickets_dir) == "abc-1234"

    def test_partial_prefix(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="test"), tickets_dir)
        assert resolve_id("abc", tickets_dir) == "abc-1234"

    def test_partial_substring(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="test"), tickets_dir)
        assert resolve_id("c-12", tickets_dir) == "abc-1234"

    def test_ambiguous_id_error(self, tmp_path: Path) -> None:
        from tiquette.store import AmbiguousIDError, Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="first"), tickets_dir)
        write_ticket(Ticket(id="abc-5678", title="second"), tickets_dir)
        with pytest.raises(AmbiguousIDError, match="ambiguous ID 'abc'"):
            resolve_id("abc", tickets_dir)


class TestNullableFieldsRoundtrip:
    """Nullable fields are omitted from the file when None and round-trip correctly."""

    # spec: ticket-store requirement=ticket-file-format scenario=nullable-fields-absent-after-being-cleared
    def test_null_nullable_fields_roundtrip_to_none(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, read_ticket, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        t = Ticket(id="proj-0001", title="Test")
        write_ticket(t, tickets_dir)
        loaded = read_ticket("proj-0001", tickets_dir)

        assert loaded.assignee is None
        assert loaded.parent is None
        assert loaded.xref is None
        assert loaded.resolution is None

    def test_nonexistent_id_error(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, TicketNotFoundError, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc-1234", title="test"), tickets_dir)
        with pytest.raises(TicketNotFoundError, match="ticket 'nonexistent' not found"):
            resolve_id("nonexistent", tickets_dir)

    def test_exact_takes_precedence_over_substring(self, tmp_path: Path) -> None:
        from tiquette.store import Ticket, resolve_id, write_ticket

        tickets_dir = tmp_path / ".tickets"
        tickets_dir.mkdir()
        write_ticket(Ticket(id="abc", title="exact"), tickets_dir)
        write_ticket(Ticket(id="abc-1234", title="longer"), tickets_dir)
        assert resolve_id("abc", tickets_dir) == "abc"

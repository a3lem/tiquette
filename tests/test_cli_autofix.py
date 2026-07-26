"""Tests for `tq autofix`.
# spec: ticket-store
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tiquette.store import Ticket, read_ticket, write_ticket


def _run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
        env=run_env,
    )


def _make_project(tmp_path: Path, name: str) -> Path:
    project = tmp_path / name
    project.mkdir()
    td = project / ".tickets"
    td.mkdir()
    return td


class TestAutofix:
    def test_no_fixes_when_prefixes_already_match(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "myproj")
        write_ticket(Ticket(id="mypr-aaaa", title="A"), td)
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "No fixes needed" in r.stdout
        assert (td / "mypr-aaaa.md").exists()

    def test_renames_stale_prefix_and_propagates_refs(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        # Stale prefix: pre-rule full name
        write_ticket(Ticket(id="tiquette-aaaa", title="Parent"), td)
        write_ticket(
            Ticket(
                id="tiquette-bbbb",
                title="Child",
                parent="tiquette-aaaa",
                deps=["tiquette-aaaa"],
                links=["tiquette-aaaa"],
            ),
            td,
        )

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "- Renamed 2 tickets to current ID prefix" in r.stdout

        # Old files gone, new files exist
        assert not (td / "tiquette-aaaa.md").exists()
        assert not (td / "tiquette-bbbb.md").exists()
        assert (td / "tiqt-aaaa.md").exists()
        assert (td / "tiqt-bbbb.md").exists()

        # References propagated; no orphaned IDs remain
        child = read_ticket("tiqt-bbbb", td)
        assert child.parent == "tiqt-aaaa"
        assert child.deps == ["tiqt-aaaa"]
        assert child.links == ["tiqt-aaaa"]
        assert child.id == "tiqt-bbbb"

    def test_singular_summary_for_one_ticket(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        write_ticket(Ticket(id="tiquette-cafe", title="Solo"), td)
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "- Renamed 1 ticket to current ID prefix" in r.stdout
        assert (td / "tiqt-cafe.md").exists()

    def test_collision_regenerates_suffix(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        # An existing ticket already occupies the target name
        write_ticket(Ticket(id="tiqt-dead", title="Existing"), td)
        write_ticket(Ticket(id="tiquette-dead", title="Stale colliding"), td)

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr

        # Both tickets must still exist; existing one untouched, stale one renamed
        # to a new id with the right prefix but a different suffix.
        assert (td / "tiqt-dead.md").exists()
        assert not (td / "tiquette-dead.md").exists()
        new_files = sorted(p.name for p in td.glob("tiqt-*.md"))
        assert len(new_files) == 2
        assert "tiqt-dead.md" in new_files

    def test_mixed_stale_prefixes_all_renamed(self, tmp_path: Path) -> None:
        # Several tickets with a variety of stale prefixes, plus a non-hex
        # suffix imported from the old `tk` tool. All should be renamed.
        td = _make_project(tmp_path, "tiquette")
        archive = td / "archive"
        archive.mkdir()
        write_ticket(Ticket(id="tiquette-aaaa", title="Stale long prefix"), td)
        write_ticket(
            Ticket(id="tk-bbbb", title="Old tk import", deps=["tiquette-aaaa"]), td
        )
        write_ticket(
            Ticket(id="foo-zzzz", title="Non-hex suffix", parent="tk-bbbb"), td
        )
        write_ticket(Ticket(id="tiquette-cccc", title="Archived stale"), archive)

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr

        for stale in ("tiquette-aaaa.md", "tk-bbbb.md", "foo-zzzz.md"):
            assert not (td / stale).exists(), stale
        assert not (archive / "tiquette-cccc.md").exists()

        new_active = sorted(p.stem for p in td.glob("*.md"))
        assert new_active == ["tiqt-aaaa", "tiqt-bbbb", "tiqt-zzzz"], new_active
        assert (archive / "tiqt-cccc.md").exists()

        # Cross-references rewritten to new IDs
        b = read_ticket("tiqt-bbbb", td)
        assert b.deps == ["tiqt-aaaa"]
        z = read_ticket("tiqt-zzzz", td)
        assert z.parent == "tiqt-bbbb"

        assert "- Renamed 4 tickets to current ID prefix" in r.stdout

    # -----------------------------------------------------------------------
    # REMOVED in v1.2: migrate-legacy-closed-status (closed → completed/canceled)
    # v1.2 reverses the rename: closed is now the terminal status for shipped
    # work, so these migrations would incorrectly rewrite v1.2 closed tickets.
    # See specs/changes/cli-redesign-v1.2/deltas/ticket-autofix/spec.md
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # NEW in v1.2: migrate-completed-status-to-closed
    # See specs/changes/cli-redesign-v1.2/deltas/ticket-autofix/spec.md
    # -----------------------------------------------------------------------

    # spec: ticket-autofix requirement=migrate-completed-status-to-closed scenario=active-completed-ticket-migrated
    def test_migrate_completed_to_closed_active(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-aaaa.md"
        path.write_text("---\nid: proj-aaaa\nstatus: completed\ntitle: Done\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        content = path.read_text()
        assert "status: closed" in content
        assert "status: completed" not in content
        assert "Migrated 1 ticket from completed status" in r.stdout

    # spec: ticket-autofix requirement=migrate-completed-status-to-closed scenario=archived-completed-ticket-migrated
    def test_migrate_completed_to_closed_archived(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        archive = td / "archive"
        archive.mkdir()
        path = archive / "proj-arc1.md"
        path.write_text(
            "---\nid: proj-arc1\nstatus: completed\ntitle: Archived done\n---\n"
        )
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        content = path.read_text()
        assert "status: closed" in content
        assert "status: completed" not in content

    # spec: ticket-autofix requirement=migrate-completed-status-to-closed scenario=multiple-tickets-migrated
    def test_migrate_multiple_completed_tickets(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        for tid in ("proj-1111", "proj-2222", "proj-3333"):
            (td / f"{tid}.md").write_text(
                f"---\nid: {tid}\nstatus: completed\ntitle: Done\n---\n"
            )
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Migrated 3 tickets from completed status" in r.stdout
        for tid in ("proj-1111", "proj-2222", "proj-3333"):
            content = (td / f"{tid}.md").read_text()
            assert "status: closed" in content
            assert "status: completed" not in content

    # spec: ticket-autofix requirement=migrate-completed-status-to-closed scenario=no-completed-tickets-is-a-no-op
    def test_no_completed_tickets_no_migration_line(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        (td / "proj-open.md").write_text(
            "---\nid: proj-open\nstatus: open\ntitle: Open\n---\n"
        )
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "from completed status" not in r.stdout

    # spec: ticket-autofix requirement=migrate-completed-status-to-closed scenario=idempotent
    def test_migration_is_idempotent(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-aaaa.md"
        path.write_text("---\nid: proj-aaaa\nstatus: completed\ntitle: Done\n---\n")
        # First run migrates
        r1 = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r1.returncode == 0, r1.stderr
        assert "Migrated 1 ticket from completed status" in r1.stdout
        # Second run: already closed, no migration
        r2 = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r2.returncode == 0, r2.stderr
        assert "from completed status" not in r2.stdout
        assert "status: closed" in path.read_text()

    def test_archived_tickets_renamed_too(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        archive = td / "archive"
        archive.mkdir()
        write_ticket(Ticket(id="tiquette-a1c1", title="Archived"), archive)
        write_ticket(
            Ticket(
                id="tiquette-bbbb",
                title="Active linking archived",
                links=["tiquette-a1c1"],
            ),
            td,
        )

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr

        assert (archive / "tiqt-a1c1.md").exists()
        active = read_ticket("tiqt-bbbb", td)
        assert active.links == ["tiqt-a1c1"]


# spec: ticket-autofix requirement=normalize-legacy-timestamps
class TestAutofixTimestampNormalization:
    LEGACY = "2026-04-29T12:48:50.906383+00:00"
    NEW = "2026-04-29T12:48Z"

    def _write_raw_ticket(
        self,
        tickets_dir: Path,
        ticket_id: str,
        created: str,
        body_extra: str = "",
    ) -> Path:
        path = tickets_dir / f"{ticket_id}.md"
        # Match the file format used by write_ticket: trailing newlines and `id` first.
        path.write_text(
            f"---\nid: {ticket_id}\nstatus: open\ntype: task\npriority: 2\n"
            f"deps: []\nlinks: []\ntags: []\ncreated: {created}\n"
            f"---\n# Title\n{body_extra}"
        )
        return path

    def test_active_legacy_created_normalized(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        self._write_raw_ticket(td, "tiqt-aaaa", self.LEGACY)
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "- Normalized 1 ticket to current timestamp format" in r.stdout
        content = (td / "tiqt-aaaa.md").read_text()
        assert f"created: {self.NEW}" in content

    def test_archived_legacy_created_normalized(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        archive = td / "archive"
        archive.mkdir()
        self._write_raw_ticket(archive, "tiqt-arc1", self.LEGACY)
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        content = (archive / "tiqt-arc1.md").read_text()
        assert f"created: {self.NEW}" in content

    def test_note_timestamp_normalized(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        self._write_raw_ticket(
            td,
            "tiqt-bbbb",
            self.NEW,  # frontmatter already new; only the note is legacy
            body_extra=f"\n## Notes\n\n- {self.LEGACY}: hello\n",
        )
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        content = (td / "tiqt-bbbb.md").read_text()
        assert f"- {self.NEW}: hello" in content
        assert self.LEGACY not in content

    def test_already_new_format_is_no_op(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        path = self._write_raw_ticket(td, "tiqt-cccc", self.NEW)
        before = path.read_text()
        before_mtime = path.stat().st_mtime
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Normalized" not in r.stdout or "timestamp" not in r.stdout
        assert path.read_text() == before
        assert path.stat().st_mtime == before_mtime

    def test_multiple_tickets_normalized(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        self._write_raw_ticket(td, "tiqt-aaaa", self.LEGACY)
        self._write_raw_ticket(td, "tiqt-bbbb", self.LEGACY)
        self._write_raw_ticket(
            td,
            "tiqt-cccc",
            self.NEW,
            body_extra=f"\n## Notes\n\n- {self.LEGACY}: hi\n",
        )
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "- Normalized 3 tickets to current timestamp format" in r.stdout

    def test_idempotent(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        self._write_raw_ticket(td, "tiqt-aaaa", self.LEGACY)
        r1 = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert "Normalized 1" in r1.stdout
        r2 = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r2.returncode == 0, r2.stderr
        assert "Normalized" not in r2.stdout or "timestamp" not in r2.stdout


# spec: ticket-autofix requirement=stale-id-prefix-renames -- regression for tiqt-0896
class TestAutofixRenamePreservesBody:
    def test_rename_preserves_notes_section(self, tmp_path: Path) -> None:
        """Prefix-rename must preserve a `## Notes` section even when no `## Description` heading is present."""
        td = _make_project(tmp_path, "tiquette")
        # Stale-prefix ticket with only a Notes section (no Description heading).
        (td / "tiquette-aaaa.md").write_text(
            "---\nid: tiquette-aaaa\nstatus: open\ntype: task\npriority: 2\n"
            "deps: []\nlinks: []\ntags: []\ncreated: 2026-04-29T12:48Z\n"
            "---\n# Legacy ticket\n\n## Notes\n\n- 2026-04-29T12:48Z: kickoff\n"
        )

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert (td / "tiqt-aaaa.md").exists()
        renamed = (td / "tiqt-aaaa.md").read_text()
        assert "## Notes" in renamed
        assert "- 2026-04-29T12:48Z: kickoff" in renamed

    def test_rename_preserves_description_and_notes(self, tmp_path: Path) -> None:
        """Round-trip through rename keeps both `## Description` and `## Notes`."""
        td = _make_project(tmp_path, "tiquette")
        (td / "tiquette-bbbb.md").write_text(
            "---\nid: tiquette-bbbb\nstatus: open\ntype: task\npriority: 2\n"
            "deps: []\nlinks: []\ntags: []\ncreated: 2026-04-29T12:48Z\n"
            "---\n# With both\n\n## Description\n\nProse content here.\n\n"
            "## Notes\n\n- 2026-04-29T12:48Z: kickoff\n"
        )

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        renamed = (td / "tiqt-bbbb.md").read_text()
        assert "Prose content here." in renamed
        assert "## Notes" in renamed
        assert "- 2026-04-29T12:48Z: kickoff" in renamed

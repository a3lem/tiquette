"""Tests for `tq autofix`.
# spec: ticket-store
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tiquette.store import Ticket, read_ticket, write_ticket


def _run(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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
        write_ticket(Ticket(id="tk-bbbb", title="Old tk import",
                            deps=["tiquette-aaaa"]), td)
        write_ticket(Ticket(id="foo-zzzz", title="Non-hex suffix",
                            parent="tk-bbbb"), td)
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

    # spec: ticket-autofix requirement=migrate-legacy-closed-status
    def test_migrate_closed_with_no_resolution_becomes_completed(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-aaaa.md"
        path.write_text("---\nid: proj-aaaa\nstatus: closed\ntitle: Legacy\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Migrated 1 ticket from closed status" in r.stdout
        content = path.read_text()
        assert "status: completed" in content
        assert "status: closed" not in content

    def test_migrate_closed_resolution_canceled_becomes_canceled(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-bbbb.md"
        path.write_text("---\nid: proj-bbbb\nstatus: closed\nresolution: canceled\ntitle: Rejected\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Migrated 1 ticket from closed status" in r.stdout
        content = path.read_text()
        assert "status: canceled" in content
        assert "status: closed" not in content
        assert "resolution:" not in content

    def test_migrate_closed_resolution_completed_becomes_completed(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-cccc.md"
        path.write_text("---\nid: proj-cccc\nstatus: closed\nresolution: completed\ntitle: Done\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        content = path.read_text()
        assert "status: completed" in content
        assert "resolution:" not in content

    def test_strip_stray_resolution_from_open_ticket(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        path = td / "proj-dddd.md"
        path.write_text("---\nid: proj-dddd\nstatus: open\nresolution: completed\ntitle: Stray\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Stripped resolution from 1 ticket" in r.stdout
        content = path.read_text()
        assert "status: open" in content
        assert "resolution:" not in content

    def test_migrate_multiple_closed_tickets(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "proj")
        (td / "proj-1111.md").write_text("---\nid: proj-1111\nstatus: closed\ntitle: A\n---\n")
        (td / "proj-2222.md").write_text("---\nid: proj-2222\nstatus: closed\nresolution: canceled\ntitle: B\n---\n")
        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr
        assert "Migrated 2 tickets from closed status" in r.stdout

    def test_archived_tickets_renamed_too(self, tmp_path: Path) -> None:
        td = _make_project(tmp_path, "tiquette")
        archive = td / "archive"
        archive.mkdir()
        write_ticket(Ticket(id="tiquette-a1c1", title="Archived"), archive)
        write_ticket(
            Ticket(id="tiquette-bbbb", title="Active linking archived",
                   links=["tiquette-a1c1"]),
            td,
        )

        r = _run("autofix", env={"TICKETS_DIR": str(td)})
        assert r.returncode == 0, r.stderr

        assert (archive / "tiqt-a1c1.md").exists()
        active = read_ticket("tiqt-bbbb", td)
        assert active.links == ["tiqt-a1c1"]

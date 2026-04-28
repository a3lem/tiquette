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

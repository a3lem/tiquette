"""Tests for relationship behaviour surviving the v1.2 redesign.
# spec: ticket-relationships

Removed verbs (dep, undep, nest, unnest, link, unlink) are gone.
Only cycle detection survives, now triggered via `tq edit --dep`,
`tq edit --parent`, and `tq create --dep`.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tiquette.store import Ticket, write_ticket


def run_tq(
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


def _make_ticket(
    tickets_dir: Path,
    ticket_id: str,
    deps: list[str] | None = None,
    parent: str | None = None,
) -> Ticket:
    tickets_dir.mkdir(parents=True, exist_ok=True)
    t = Ticket(
        id=ticket_id,
        title=f"Test {ticket_id}",
        deps=deps or [],
        parent=parent,
    )
    write_ticket(t, tickets_dir)
    return t


class TestCycleDetection:
    """Cycle detection survives v1.2; trigger moves to `edit --dep` / `edit --parent`."""

    # spec: ticket-relationships requirement=cycle-detection scenario=direct-dependency-cycle-rejected
    def test_edit_dep_direct_cycle_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001", deps=["task-0002"])
        _make_ticket(td, "task-0002")
        result = run_tq(
            "edit", "task-0002", "--dep", "task-0001", env={"TICKETS_DIR": str(td)}
        )
        assert result.returncode != 0
        assert "cycle" in result.stderr.lower()

    # spec: ticket-relationships requirement=cycle-detection scenario=transitive-dependency-cycle-rejected
    def test_edit_dep_transitive_cycle_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "task-0001", deps=["task-0002"])
        _make_ticket(td, "task-0002", deps=["task-0003"])
        _make_ticket(td, "task-0003")
        result = run_tq(
            "edit", "task-0003", "--dep", "task-0001", env={"TICKETS_DIR": str(td)}
        )
        assert result.returncode != 0
        assert "cycle" in result.stderr.lower()

    # spec: ticket-relationships requirement=cycle-detection scenario=parent-cycle-rejected
    def test_edit_parent_cycle_rejected(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        _make_ticket(td, "par-0002", parent="par-0001")
        _make_ticket(td, "par-0001")
        result = run_tq(
            "edit", "par-0001", "--parent", "par-0002", env={"TICKETS_DIR": str(td)}
        )
        assert result.returncode != 0
        assert "cycle" in result.stderr.lower()

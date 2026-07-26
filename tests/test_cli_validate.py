"""Tests for the validate command.
# spec: ticket-validate
"""

from __future__ import annotations

import os
import subprocess
import typing as T
from pathlib import Path

from tiquette.store import Ticket, write_ticket


def run_tq_env(
    *args: str,
    env: dict[str, str] | None = None,
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


def _make_ticket(tickets_dir: Path, ticket_id: str, **kwargs: T.Any) -> None:
    t = Ticket(id=ticket_id, title=f"Test {ticket_id}", **kwargs)
    write_ticket(t, tickets_dir)


def _setup_clean(tmp_path: Path) -> Path:
    td = tmp_path / ".tickets"
    td.mkdir()
    _make_ticket(td, "proj-a001")
    _make_ticket(td, "proj-b002", deps=["proj-a001"])
    _make_ticket(td, "proj-c003", parent="proj-a001", links=["proj-b002"])
    return td


# ── Requirement: Validate command ──────────────────────────


# spec: ticket-validate requirement=validate-command scenario=clean-ticket-store
class TestCleanStore:
    def test_exits_zero_no_output(self, tmp_path: Path) -> None:
        td = _setup_clean(tmp_path)
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "error:" not in result.stderr
        assert "warning:" not in result.stderr


# spec: ticket-validate requirement=validate-command scenario=violations-found
class TestViolationsFound:
    def test_exits_nonzero_on_error(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-gone"])
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.returncode != 0
        assert "error:" in result.stderr


# spec: ticket-validate requirement=validate-command scenario=only-warnings-found
class TestOnlyWarnings:
    def test_exits_zero_with_warnings(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-old1"])
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "warning:" in result.stderr
        assert "error:" not in result.stderr


# ── Requirement: Output format ─────────────────────────────


# spec: ticket-validate requirement=output-format scenario=violation-output
class TestOutputFormatViolation:
    def test_structured_error_line(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-gone"])
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: error: depends on non-existent ticket "proj-gone"'
            in result.stderr
        )


# spec: ticket-validate requirement=output-format scenario=warning-output
class TestOutputFormatWarning:
    def test_structured_warning_line(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-old1"])
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: warning: depends on archived ticket "proj-old1"'
            in result.stderr
        )


# ── Requirement: Summary line ──────────────────────────────


# spec: ticket-validate requirement=summary-line scenario=summary-with-violations
class TestSummaryWithViolations:
    def test_error_and_warning_counts(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-gone", "proj-also-gone"])
        _make_ticket(td, "proj-b002", deps=["proj-old1"])
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.stderr.strip().endswith("2 errors, 1 warning")


# spec: ticket-validate requirement=summary-line scenario=summary-all-clean
class TestSummaryAllClean:
    def test_all_valid_message(self, tmp_path: Path) -> None:
        td = _setup_clean(tmp_path)
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.stderr.strip().endswith("all tickets valid")


# spec: ticket-validate requirement=summary-line scenario=summary-warnings-only
class TestSummaryWarningsOnly:
    def test_zero_errors_with_warnings(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-old1"])
        _make_ticket(td, "proj-b002", links=["proj-old2"])
        _make_ticket(archive, "proj-old1")
        _make_ticket(archive, "proj-old2")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.stderr.strip().endswith("0 errors, 2 warnings")


# ── Requirement: Dependency existence ──────────────────────


# spec: ticket-validate requirement=dependency-existence scenario=valid-dependency
class TestValidDep:
    def test_no_problem_for_valid_dep(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-b002"])
        _make_ticket(td, "proj-b002")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert "proj-a001" not in result.stderr.split("all tickets valid")[0]


# spec: ticket-validate requirement=dependency-existence scenario=missing-dependency
class TestMissingDep:
    def test_error_for_missing_dep(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-gone"])
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: error: depends on non-existent ticket "proj-gone"'
            in result.stderr
        )


# spec: ticket-validate requirement=dependency-existence scenario=multiple-missing-dependencies
class TestMultipleMissingDeps:
    def test_reports_each_missing_dep(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-gone", "proj-also-gone"])
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert '"proj-gone"' in result.stderr
        assert '"proj-also-gone"' in result.stderr


# spec: ticket-validate requirement=dependency-existence scenario=dependency-on-archived-ticket
class TestDepOnArchived:
    def test_warning_for_archived_dep(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", deps=["proj-old1"])
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: warning: depends on archived ticket "proj-old1"'
            in result.stderr
        )


# ── Requirement: Parent existence ──────────────────────────


# spec: ticket-validate requirement=parent-existence scenario=valid-parent
class TestValidParent:
    def test_no_problem_for_valid_parent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-c003", parent="proj-p001")
        _make_ticket(td, "proj-p001")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert "proj-c003" not in result.stderr.split("all tickets valid")[0]


# spec: ticket-validate requirement=parent-existence scenario=missing-parent
class TestMissingParent:
    def test_error_for_missing_parent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-c003", parent="proj-p001")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert 'proj-c003: error: has non-existent parent "proj-p001"' in result.stderr


# spec: ticket-validate requirement=parent-existence scenario=parent-is-archived-ticket
class TestParentArchived:
    def test_warning_for_archived_parent(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-c003", parent="proj-old1")
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert 'proj-c003: warning: has archived parent "proj-old1"' in result.stderr


# ── Requirement: Link existence ────────────────────────────


# spec: ticket-validate requirement=link-existence scenario=valid-link
class TestValidLink:
    def test_no_problem_for_valid_link(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", links=["proj-b002"])
        _make_ticket(td, "proj-b002")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert "proj-a001" not in result.stderr.split("all tickets valid")[0]


# spec: ticket-validate requirement=link-existence scenario=missing-link-target
class TestMissingLink:
    def test_error_for_missing_link(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        _make_ticket(td, "proj-a001", links=["proj-gone"])
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: error: links to non-existent ticket "proj-gone"'
            in result.stderr
        )


# spec: ticket-validate requirement=link-existence scenario=link-to-archived-ticket
class TestLinkToArchived:
    def test_warning_for_archived_link(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(td, "proj-a001", links=["proj-old1"])
        _make_ticket(archive, "proj-old1")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert (
            'proj-a001: warning: links to archived ticket "proj-old1"' in result.stderr
        )


# ── Requirement: Scope ─────────────────────────────────────


# spec: ticket-validate requirement=scope scenario=archived-ticket-excluded-from-checks
class TestArchivedExcluded:
    def test_archived_ticket_not_checked(self, tmp_path: Path) -> None:
        td = tmp_path / ".tickets"
        td.mkdir()
        archive = td / "archive"
        archive.mkdir()
        _make_ticket(archive, "proj-old1", deps=["proj-gone"])
        _make_ticket(td, "proj-a001")
        result = run_tq_env("validate", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0
        assert "proj-old1" not in result.stderr

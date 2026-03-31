"""Tests for lifecycle command argument parsing.
# spec: ticket-lifecycle
"""
from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
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

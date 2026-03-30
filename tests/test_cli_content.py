"""Tests for content command argument parsing.
# spec: ticket-content
"""
from __future__ import annotations

import subprocess

import pytest


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


class TestDescribeArgs:
    """Argument parsing for `tq describe`."""

    # spec: ticket-content requirement=describe scenario=set-description
    def test_describe_requires_id_and_text(self) -> None:
        result = run_tq("describe", "t-001")
        assert result.returncode != 0

    def test_describe_accepts_id_and_text(self) -> None:
        result = run_tq("describe", "t-001", "New description")
        assert result.returncode == 0


class TestAddNoteArgs:
    """Argument parsing for `tq add-note`."""

    # spec: ticket-content requirement=add-note scenario=add-a-note
    def test_add_note_requires_id_and_text(self) -> None:
        result = run_tq("add-note", "t-001")
        assert result.returncode != 0

    def test_add_note_accepts_id_and_text(self) -> None:
        result = run_tq("add-note", "t-001", "This is my note")
        assert result.returncode == 0

    # spec: ticket-content requirement=add-note scenario=add-note-via-stdin
    @pytest.mark.skip(reason="stdin fallback not yet implemented")
    def test_add_note_via_stdin(self) -> None:
        result = subprocess.run(
            ["uv", "run", "tq", "add-note", "t-001"],
            capture_output=True,
            text=True,
            input="Piped note content",
        )
        assert result.returncode == 0

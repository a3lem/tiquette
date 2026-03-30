"""Tests for query command argument parsing.
# spec: ticket-query
"""
from __future__ import annotations

import subprocess


def run_tq(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "tq", *args],
        capture_output=True,
        text=True,
    )


class TestShowArgs:
    """Argument parsing for `tq show`."""

    # spec: ticket-query requirement=show-ticket scenario=show-displays-ticket-content
    def test_show_requires_id(self) -> None:
        result = run_tq("show")
        assert result.returncode != 0

    def test_show_accepts_id(self) -> None:
        result = run_tq("show", "show-001")
        assert result.returncode == 0

    # spec: ticket-query requirement=show-ticket scenario=show-as-json
    def test_show_accepts_json_flag(self) -> None:
        result = run_tq("show", "show-001", "--json")
        assert result.returncode == 0


class TestInfoArgs:
    """Argument parsing for `tq info`."""

    # spec: ticket-query requirement=info-command scenario=info-displays-frontmatter-and-relationships
    def test_info_requires_id(self) -> None:
        result = run_tq("info")
        assert result.returncode != 0

    def test_info_accepts_id(self) -> None:
        result = run_tq("info", "info-001")
        assert result.returncode == 0

    # spec: ticket-query requirement=info-command scenario=info-as-json
    def test_info_accepts_json_flag(self) -> None:
        result = run_tq("info", "info-001", "--json")
        assert result.returncode == 0


class TestPathArgs:
    """Argument parsing for `tq path`."""

    # spec: ticket-query requirement=path-command scenario=path-prints-file-location
    def test_path_requires_id(self) -> None:
        result = run_tq("path")
        assert result.returncode != 0

    def test_path_accepts_id(self) -> None:
        result = run_tq("path", "test-001")
        assert result.returncode == 0


class TestShowDepsArgs:
    """Argument parsing for `tq show-deps`."""

    # spec: ticket-query requirement=show-dependency-tree scenario=dependency-tree-shows-transitive-deps
    def test_show_deps_requires_id(self) -> None:
        result = run_tq("show-deps")
        assert result.returncode != 0

    def test_show_deps_accepts_id(self) -> None:
        result = run_tq("show-deps", "task-0001")
        assert result.returncode == 0

    # spec: ticket-query requirement=show-dependency-tree scenario=full-tree-disables-deduplication
    def test_show_deps_accepts_full_flag(self) -> None:
        result = run_tq("show-deps", "task-0001", "--full")
        assert result.returncode == 0


class TestLsArgs:
    """Argument parsing for `tq ls`."""

    # spec: ticket-query requirement=list-tickets scenario=list-all-open-tickets
    def test_ls_no_args(self) -> None:
        result = run_tq("ls")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=list-with-status-filter
    def test_ls_status_filter(self) -> None:
        for status in ["open", "in_progress", "closed"]:
            result = run_tq("ls", "--status", status)
            assert result.returncode == 0, f"Status '{status}' should be valid"

    # spec: ticket-query requirement=list-tickets scenario=invalid-status-rejected
    def test_ls_invalid_status(self) -> None:
        result = run_tq("ls", "--status", "invalid")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=ready-filter
    def test_ls_ready_flag(self) -> None:
        result = run_tq("ls", "--ready")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=blocked-filter
    def test_ls_blocked_flag(self) -> None:
        result = run_tq("ls", "--blocked")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=ready-and-blocked-are-mutually-exclusive
    def test_ls_ready_and_blocked_are_mutually_exclusive(self) -> None:
        result = run_tq("ls", "--ready", "--blocked")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=completed-filter
    def test_ls_completed_flag(self) -> None:
        result = run_tq("ls", "--completed")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=canceled-filter
    def test_ls_canceled_flag(self) -> None:
        result = run_tq("ls", "--canceled")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-assignee
    def test_ls_assignee_filter(self) -> None:
        result = run_tq("ls", "--assignee", "Alice")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-tag
    def test_ls_tag_filter(self) -> None:
        result = run_tq("ls", "--tag", "ui")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=filter-by-type
    def test_ls_type_filter(self) -> None:
        result = run_tq("ls", "--type", "bug")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=sort-by-mtime
    def test_ls_sort(self) -> None:
        for sort in ["priority", "mtime"]:
            result = run_tq("ls", "--sort", sort)
            assert result.returncode == 0, f"Sort '{sort}' should be valid"

    # spec: ticket-query requirement=list-tickets scenario=invalid-sort-rejected
    def test_ls_invalid_sort(self) -> None:
        result = run_tq("ls", "--sort", "invalid")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=limit
    def test_ls_limit(self) -> None:
        result = run_tq("ls", "--limit", "10")
        assert result.returncode == 0

    # spec: ticket-query requirement=list-tickets scenario=limit-must-be-positive
    def test_ls_limit_must_be_positive(self) -> None:
        result = run_tq("ls", "--limit", "0")
        assert result.returncode != 0

    # spec: ticket-query requirement=list-tickets scenario=jsonl-output
    def test_ls_jsonl_flag(self) -> None:
        result = run_tq("ls", "--jsonl")
        assert result.returncode == 0


class TestTagsArgs:
    """Argument parsing for `tq tags`."""

    # spec: ticket-query requirement=tags-listing scenario=tags-sorted-by-count-descending
    def test_tags_no_args(self) -> None:
        result = run_tq("tags")
        assert result.returncode == 0


class TestArchiveArgs:
    """Argument parsing for `tq archive`."""

    # spec: ticket-query requirement=archive scenario=archive-moves-closed-tickets
    def test_archive_no_args(self) -> None:
        result = run_tq("archive")
        assert result.returncode == 0

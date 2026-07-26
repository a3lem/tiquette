"""Tests for the timestamp format change.

# spec: ticket-store requirement=timestamp-format
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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


NEW_FMT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$")
LEGACY_TS = "2026-04-29T12:48:50.906383+00:00"


class TestTimestampsHelper:
    """Unit tests for tiquette.timestamps."""

    def test_now_iso_shape(self) -> None:
        from tiquette.timestamps import now_iso

        s = now_iso()
        assert NEW_FMT_RE.match(s), s

    def test_now_iso_is_utc_minute_precision(self) -> None:
        from tiquette.timestamps import now_iso, parse_iso

        before = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        s = now_iso()
        parsed = parse_iso(s)
        # parsed minute should be the same as `before` minute (or one minute later
        # if the test crossed a minute boundary mid-call).
        assert parsed.tzinfo is not None
        delta = (parsed - before).total_seconds()
        assert 0 <= delta < 120, (before, parsed)

    def test_parse_iso_accepts_new_format(self) -> None:
        from tiquette.timestamps import parse_iso

        dt = parse_iso("2026-05-26T10:00Z")
        assert dt.year == 2026 and dt.minute == 0
        assert dt.tzinfo is not None
        assert dt.utcoffset() == timezone.utc.utcoffset(dt)

    def test_parse_iso_accepts_legacy_format(self) -> None:
        from tiquette.timestamps import parse_iso

        dt = parse_iso(LEGACY_TS)
        assert dt.year == 2026 and dt.microsecond == 906383
        assert dt.tzinfo is not None

    def test_new_and_legacy_parse_equal_when_truncated(self) -> None:
        from tiquette.timestamps import parse_iso

        a = parse_iso("2026-04-29T12:48Z")
        b = parse_iso("2026-04-29T12:48:00+00:00")
        assert a == b


def _read_ticket_file(tickets_dir: Path, ticket_id: str) -> str:
    return (tickets_dir / f"{ticket_id}.md").read_text()


def _make_dir(tmp_path: Path) -> Path:
    td = tmp_path / ".tickets"
    td.mkdir()
    return td


class TestTimestampFormatEndToEnd:
    """Spec scenarios from deltas/ticket-store/spec.md."""

    # spec: ticket-store requirement=timestamp-format scenario=new-ticket-writes-new-format
    def test_new_ticket_writes_new_format(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        result = run_tq("create", "Hello", env={"TICKETS_DIR": str(td)})
        ticket_id = result.stdout.strip()
        content = _read_ticket_file(td, ticket_id)
        created_line = next(
            l for l in content.splitlines() if l.startswith("created: ")
        )
        ts = created_line.split("created: ", 1)[1]
        assert NEW_FMT_RE.match(ts), ts

    # spec: ticket-store requirement=timestamp-format scenario=new-note-writes-new-format
    def test_new_note_writes_new_format(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        result = run_tq("create", "Host", env={"TICKETS_DIR": str(td)})
        ticket_id = result.stdout.strip()
        result = run_tq(
            "edit", ticket_id, "--note", "hello", env={"TICKETS_DIR": str(td)}
        )
        assert result.returncode == 0, result.stderr
        content = _read_ticket_file(td, ticket_id)
        # Note line: "- 2026-05-26T10:00Z: hello"
        match = re.search(r"^- (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z): hello$", content, re.M)
        assert match, content

    def _write_legacy_ticket(self, td: Path, ticket_id: str) -> Path:
        path = td / f"{ticket_id}.md"
        path.write_text(
            f"---\nid: {ticket_id}\nstatus: open\ntype: task\npriority: 2\n"
            f"deps: []\nlinks: []\ntags: []\ncreated: {LEGACY_TS}\n"
            f"---\n# Legacy ticket\n"
        )
        return path

    # spec: ticket-store requirement=timestamp-format scenario=legacy-timestamps-read-ok
    def test_legacy_timestamp_is_read_without_error(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        self._write_legacy_ticket(td, "leg-0001")
        result = run_tq("show", "leg-0001", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        assert LEGACY_TS in result.stdout

    # spec: ticket-store requirement=timestamp-format scenario=legacy-not-rewritten-on-read
    def test_legacy_not_rewritten_on_read(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        path = self._write_legacy_ticket(td, "leg-0002")
        original = path.read_text()
        original_mtime = path.stat().st_mtime
        run_tq("show", "leg-0002", env={"TICKETS_DIR": str(td)})
        assert path.read_text() == original
        assert path.stat().st_mtime == original_mtime

    # spec: ticket-store requirement=timestamp-format scenario=editing-legacy-preserves-created
    def test_editing_legacy_ticket_preserves_created(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        self._write_legacy_ticket(td, "leg-0003")
        result = run_tq("edit", "leg-0003", "-p", "1", env={"TICKETS_DIR": str(td)})
        assert result.returncode == 0, result.stderr
        content = (td / "leg-0003.md").read_text()
        assert f"created: {LEGACY_TS}" in content
        assert "priority: 1" in content

    # spec: ticket-store requirement=timestamp-format scenario=editing-legacy-preserves-created
    def test_editing_legacy_writes_new_format_notes(self, tmp_path: Path) -> None:
        td = _make_dir(tmp_path)
        self._write_legacy_ticket(td, "leg-0004")
        result = run_tq(
            "edit", "leg-0004", "--note", "hi", env={"TICKETS_DIR": str(td)}
        )
        assert result.returncode == 0, result.stderr
        content = (td / "leg-0004.md").read_text()
        assert f"created: {LEGACY_TS}" in content
        assert re.search(r"^- \d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z: hi$", content, re.M)

from __future__ import annotations

import argparse
import dataclasses
import re
import secrets
from pathlib import Path

from tiquette.store import (
    Ticket,
    abbreviate,
    find_tickets_dir,
    iter_tickets,
    write_ticket,
)
from tiquette.timestamps import parse_iso, to_iso


# [AI]
# Context: user request -- maintenance command to reconcile tickets with current behavior
# Intent: rename ticket IDs whose prefix no longer matches the expected abbreviation,
#   and propagate renames into deps/links/parent of every other ticket so nothing is orphaned.


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = subparsers.add_parser(
        "autofix",
        help="Update tickets to be consistent with current behavior",
    )
    p.set_defaults(func=_handle_autofix)


def _all_ticket_dirs(tickets_dir: Path) -> list[Path]:
    dirs = [tickets_dir]
    archive = tickets_dir / "archive"
    if archive.is_dir():
        dirs.append(archive)
    return dirs


def _existing_ids(dirs: list[Path]) -> set[str]:
    ids: set[str] = set()
    for d in dirs:
        for p in d.glob("*.md"):
            ids.add(p.stem)
    return ids


# [AI]
# Context: prefix abbreviation rule changed
# Intent: build old->new ID map for tickets whose prefix is stale.
#   Preserve the original 4-hex suffix when possible; regenerate on collision.
def _plan_prefix_renames(
    tickets_dir: Path,
    all_ids: set[str],
) -> dict[str, str]:
    expected_prefix = abbreviate(tickets_dir.parent.name)
    renames: dict[str, str] = {}
    reserved = set(all_ids)

    for tid in sorted(all_ids):
        if "-" not in tid:
            continue
        current_prefix, _, suffix = tid.rpartition("-")
        if current_prefix == expected_prefix:
            continue
        candidate = f"{expected_prefix}-{suffix}"
        while candidate in reserved:
            candidate = f"{expected_prefix}-{secrets.token_hex(2)}"
        reserved.add(candidate)
        renames[tid] = candidate

    return renames


def _apply_renames(
    tickets_dir: Path,
    renames: dict[str, str],
) -> None:
    if not renames:
        return

    dirs = _all_ticket_dirs(tickets_dir)

    # Load every ticket once, apply rename + reference updates in memory,
    # then write all new files before deleting old ones.
    loaded: list[
        tuple[Path, Ticket, Ticket]
    ] = []  # (containing_dir, original_ticket, updated_ticket)
    for d in dirs:
        for ticket in iter_tickets(d):
            tid = ticket.id
            new_id = renames.get(tid, tid)
            new_deps = [renames.get(x, x) for x in ticket.deps]
            new_links = [renames.get(x, x) for x in ticket.links]
            new_parent = (
                renames.get(ticket.parent, ticket.parent) if ticket.parent else None
            )
            updated = dataclasses.replace(
                ticket,
                id=new_id,
                deps=new_deps,
                links=new_links,
                parent=new_parent,
            )
            loaded.append((d, ticket, updated))

    # Write new files first (skip if nothing changed)
    for d, original, updated in loaded:
        if (
            original.id == updated.id
            and original.deps == updated.deps
            and original.links == updated.links
            and original.parent == updated.parent
        ):
            continue
        write_ticket(updated, d)

    # Delete old files whose id changed
    for d, original, updated in loaded:
        if original.id != updated.id:
            old_path = d / f"{original.id}.md"
            if old_path.exists():
                old_path.unlink()


# [AI]
# Context: cli-redesign-v1.2 -- ticket-autofix requirement=migrate-completed-status-to-closed
# Intent: rewrite legacy `status: completed` to `status: closed`. v1.2 renames
#   the terminal status so the stored value matches the verb (`close`).
#   Unconditional: no flag, no opt-in. Idempotent (a second run finds zero
#   completed tickets and does nothing).
def _migrate_completed_to_closed(dirs: list[Path]) -> int:
    """Return the count of tickets whose status was rewritten."""
    migrated = 0
    for d in dirs:
        for path in sorted(d.glob("*.md")):
            content = path.read_text()
            parts = content.split("---\n")
            if len(parts) < 3:
                continue
            fm_raw = parts[1]
            fm_lines = fm_raw.splitlines(keepends=True)
            changed = False
            new_lines: list[str] = []
            for line in fm_lines:
                if ":" in line:
                    key, _, value = line.partition(":")
                    if key.strip() == "status" and value.strip() == "completed":
                        new_lines.append("status: closed\n")
                        changed = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            if changed:
                parts[1] = "".join(new_lines)
                path.write_text("---\n".join(parts))
                migrated += 1
    return migrated


# [AI] Matches a Notes-section line: `- <timestamp>[ <tag>]: <text>`. The
# timestamp is the first non-space token; an optional bracketed tag like
# `[closed]` may follow before the `: ` separator. We then attempt to parse
# the captured timestamp via parse_iso and skip the line if it isn't a
# real timestamp.
_NOTE_LINE_RE = re.compile(r"^(- )(\S+)((?:\s+\[[^\]]+\])?:\s.*)$")

_NEW_FMT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$")


def _normalize_ts_string(s: str) -> str | None:
    # [AI] Returns the normalised form, or None if `s` is already in the new
    # format. Raises ValueError if `s` is not a parseable timestamp -- callers
    # use that as a signal to leave the line alone.
    if _NEW_FMT_RE.match(s):
        return None
    return to_iso(parse_iso(s))


def _normalize_timestamps(dirs: list[Path]) -> int:
    """Return the count of ticket files whose content was rewritten."""
    normalized = 0
    for d in dirs:
        for path in sorted(d.glob("*.md")):
            content = path.read_text()
            parts = content.split("---\n")
            if len(parts) < 3:
                continue

            changed = False

            # Frontmatter: only the `created:` line carries a timestamp.
            fm_lines = parts[1].splitlines(keepends=True)
            new_fm: list[str] = []
            for line in fm_lines:
                if line.startswith("created:"):
                    value = line.split(":", 1)[1].strip()
                    try:
                        new_value = _normalize_ts_string(value)
                    except ValueError:
                        new_fm.append(line)
                        continue
                    if new_value is None:
                        new_fm.append(line)
                    else:
                        new_fm.append(f"created: {new_value}\n")
                        changed = True
                else:
                    new_fm.append(line)
            parts[1] = "".join(new_fm)

            # Body: Notes-section lines of the form `- <ts>...`.
            body = "---\n".join(parts[2:])
            new_body_lines: list[str] = []
            for line in body.splitlines(keepends=True):
                m = _NOTE_LINE_RE.match(line.rstrip("\n"))
                if m is None:
                    new_body_lines.append(line)
                    continue
                dash, ts, rest = m.group(1), m.group(2), m.group(3)
                try:
                    new_ts = _normalize_ts_string(ts)
                except ValueError:
                    new_body_lines.append(line)
                    continue
                if new_ts is None:
                    new_body_lines.append(line)
                    continue
                trailing_nl = "\n" if line.endswith("\n") else ""
                new_body_lines.append(f"{dash}{new_ts}{rest}{trailing_nl}")
                changed = True
            new_body = "".join(new_body_lines)

            if changed:
                path.write_text(parts[0] + "---\n" + parts[1] + "---\n" + new_body)
                normalized += 1
    return normalized


def _handle_autofix(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    dirs = _all_ticket_dirs(tickets_dir)
    all_ids = _existing_ids(dirs)

    fixes: list[str] = []

    renames = _plan_prefix_renames(tickets_dir, all_ids)
    if renames:
        _apply_renames(tickets_dir, renames)
        n = len(renames)
        noun = "ticket" if n == 1 else "tickets"
        fixes.append(f"Renamed {n} {noun} to current ID prefix")

    migrated = _migrate_completed_to_closed(dirs)
    if migrated:
        noun = "ticket" if migrated == 1 else "tickets"
        fixes.append(f"Migrated {migrated} {noun} from completed status")

    normalized = _normalize_timestamps(dirs)
    if normalized:
        noun = "ticket" if normalized == 1 else "tickets"
        fixes.append(f"Normalized {normalized} {noun} to current timestamp format")

    if not fixes:
        print("No fixes needed")
        return

    for fix in fixes:
        print(f"- {fix}")

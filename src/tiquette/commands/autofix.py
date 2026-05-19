from __future__ import annotations

import argparse
import dataclasses
import secrets
from pathlib import Path

from tiquette.store import (
    Ticket,
    abbreviate,
    find_tickets_dir,
    iter_tickets,
    write_ticket,
)


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
        tuple[Path, Ticket, str]
    ] = []  # (containing_dir, updated_ticket, original_id)
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
            loaded.append((d, updated, tid))

    # Write new files first
    for d, updated, _ in loaded:
        write_ticket(updated, d)

    # Delete old files whose id changed
    for d, updated, original_id in loaded:
        if original_id != updated.id:
            old_path = d / f"{original_id}.md"
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
                if line.strip() == "status: completed":
                    new_lines.append("status: closed\n")
                    changed = True
                else:
                    new_lines.append(line)
            if changed:
                parts[1] = "".join(new_lines)
                path.write_text("---\n".join(parts))
                migrated += 1
    return migrated


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

    if not fixes:
        print("No fixes needed")
        return

    for fix in fixes:
        print(f"- {fix}")

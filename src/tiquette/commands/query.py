from __future__ import annotations

import argparse
import json
import shutil
import sys
import typing as T
from collections import Counter
from pathlib import Path

from tiquette.store import (
    Ticket,
    TicketNotFoundError,
    find_tickets_dir,
    list_ticket_ids,
    read_ticket,
    resolve_id,
)


# [AI] Query commands: show, info, path, deps, ls, tags, archive.
# ls has complex filtering with validation and mutual exclusion.

VALID_STATUSES = ("open", "in_progress", "closed")
VALID_SORTS = ("priority", "mtime")


def _positive_int(value: str) -> int:
    # [AI] Custom argparse type: must be int > 0
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: '{value}'")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"limit must be a positive integer, got {n}")
    return n


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # show <id> [--json]
    p_show = subparsers.add_parser("show", help="Display ticket")
    p_show.add_argument("id", help="Ticket ID")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=_handle_show)

    # info <id> [--json]
    p_info = subparsers.add_parser("info", help="Frontmatter + relationships")
    p_info.add_argument("id", help="Ticket ID")
    p_info.add_argument("--json", action="store_true", help="Output as JSON")
    p_info.set_defaults(func=_handle_info)

    # path <id>
    p_path = subparsers.add_parser("path", help="Print file path")
    p_path.add_argument("id", help="Ticket ID")
    p_path.set_defaults(func=_handle_path)

    # deps <id> [--full]
    p_deps = subparsers.add_parser("deps", help="Show dependency tree")
    p_deps.add_argument("id", help="Ticket ID")
    p_deps.add_argument("--full", action="store_true", help="Disable dedup")
    p_deps.set_defaults(func=_handle_deps)

    # [AI] ls: many optional filters, mutual exclusion for --ready/--blocked
    p_ls = subparsers.add_parser("ls", help="List tickets")
    p_ls.add_argument(
        "--status", choices=VALID_STATUSES,
        help="Filter by status (open|in_progress|closed)",
    )

    ready_group = p_ls.add_mutually_exclusive_group()
    ready_group.add_argument("--ready", action="store_true", help="Actionable tickets")
    ready_group.add_argument("--blocked", action="store_true", help="Blocked tickets")

    p_ls.add_argument("--completed", action="store_true", help="Resolution = completed")
    p_ls.add_argument("--canceled", action="store_true", help="Resolution = canceled")
    # [AI]
    # Context: fix-cli-output-gaps -- ticket-query requirement=list-tickets
    # Intent: short aliases match create (-a for assignee); -T avoids conflict with future -t/--type
    p_ls.add_argument("-a", "--assignee", help="Filter by assignee")
    p_ls.add_argument("-T", "--tag", help="Filter by tag")
    p_ls.add_argument("--type", help="Filter by type")
    p_ls.add_argument(
        "--sort", choices=VALID_SORTS, default="priority",
        help="Sort by field (priority|mtime)",
    )
    p_ls.add_argument("--limit", type=_positive_int, help="Limit results")
    p_ls.add_argument("--jsonl", action="store_true", help="Output as JSON Lines")
    p_ls.set_defaults(func=_handle_ls)

    # tags (no args)
    p_tags = subparsers.add_parser("tags", help="List all tags with counts")
    p_tags.set_defaults(func=_handle_tags)

    # links (no args)
    p_links = subparsers.add_parser("links", help="List all linked pairs")
    p_links.set_defaults(func=_handle_links)

    # archive (no args)
    p_archive = subparsers.add_parser("archive", help="Move closed tickets to archive")
    p_archive.set_defaults(func=_handle_archive)


# ── Helpers ──────────────────────────────────────────────────


def _load_all_tickets(tickets_dir: Path) -> dict[str, Ticket]:
    """Load all tickets into a dict keyed by ID."""
    result: dict[str, Ticket] = {}
    for tid in list_ticket_ids(tickets_dir):
        result[tid] = read_ticket(tid, tickets_dir)
    return result


# [AI]
# Context: spexl change ls-display-format, requirement=list-ticket-line-format
# Intent: match tk ls output -- checkbox for status, hide default priority/type
_STATUS_CHECKBOX: dict[str, str] = {
    "open": "[ ]",
    "in_progress": "[/]",
    "closed": "[x]",
}


def _format_ticket_line(t: Ticket) -> str:
    parts: list[str] = []
    if t.priority != 2:
        parts.append(f"[P{t.priority}]")
    if t.type != "task":
        parts.append(f"[{t.type}]")
    tags = f" {''.join(parts)}" if parts else ""
    checkbox = _STATUS_CHECKBOX.get(t.status, "[?]")
    return f"{t.id}{tags} - {checkbox} {t.title}"


def _format_ticket_line_with_deps(t: Ticket) -> str:
    """Format ticket line, appending deps if present."""
    line = _format_ticket_line(t)
    if t.deps:
        dep_str = ", ".join(t.deps)
        line += f" <- [{dep_str}]"
    return line


# [AI] Determine if a ticket is "blocked": has open deps or open children.
def _is_blocked(
    ticket: Ticket,
    all_tickets: dict[str, Ticket],
) -> bool:
    # Check open dependencies
    for dep_id in ticket.deps:
        dep = all_tickets.get(dep_id)
        if dep and dep.status != "closed":
            return True
    # Check open children
    for t in all_tickets.values():
        if t.parent == ticket.id and t.status != "closed":
            return True
    return False


# [AI] Build parent->children map for tree rendering.
def _build_children_map(tickets: dict[str, Ticket]) -> dict[str | None, list[str]]:
    children: dict[str | None, list[str]] = {}
    for tid, t in tickets.items():
        children.setdefault(t.parent, []).append(tid)
    return children


# ── show ─────────────────────────────────────────────────────


# [AI] Show full ticket content: frontmatter, body, and relationship sections
# (blockers, blocking, children, linked). JSON mode outputs structured data.
def _handle_show(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    ticket = read_ticket(ticket_id, tickets_dir)

    if args.json:
        # Read raw file body for the "body" field
        file_path = tickets_dir / f"{ticket_id}.md"
        raw = file_path.read_text()
        parts = raw.split("---\n")
        body = "---\n".join(parts[2:]).strip() if len(parts) >= 3 else ""
        data = {
            "id": ticket.id,
            "title": ticket.title,
            "status": ticket.status,
            "type": ticket.type,
            "priority": ticket.priority,
            "assignee": ticket.assignee,
            "deps": ticket.deps,
            "links": ticket.links,
            "parent": ticket.parent,
            "tags": ticket.tags,
            "xref": ticket.xref,
            "resolution": ticket.resolution,
            "created": ticket.created,
            "body": body,
        }
        print(json.dumps(data, indent=2))
        return

    # Read and print raw file content (frontmatter + body)
    file_path = tickets_dir / f"{ticket_id}.md"
    print(file_path.read_text())

    # Load all tickets for relationship sections
    all_tickets = _load_all_tickets(tickets_dir)

    # Blockers: deps that are still open
    open_deps = [
        dep_id for dep_id in ticket.deps
        if dep_id in all_tickets and all_tickets[dep_id].status != "closed"
    ]
    if open_deps:
        print("## Blockers\n")
        for dep_id in open_deps:
            dep = all_tickets[dep_id]
            print(f"- {dep_id} [{dep.status}] - {dep.title}")
        print()

    # Blocking: tickets that depend on this one
    blocking = [
        t for t in all_tickets.values()
        if ticket_id in t.deps
    ]
    if blocking:
        print("## Blocking\n")
        for t in sorted(blocking, key=lambda x: x.id):
            print(f"- {t.id} [{t.status}] - {t.title}")
        print()

    # Children
    children = [t for t in all_tickets.values() if t.parent == ticket_id]
    if children:
        print("## Children\n")
        for c in sorted(children, key=lambda x: x.id):
            print(f"- {c.id} [{c.status}] - {c.title}")
        print()

    # Linked
    if ticket.links:
        print("## Linked\n")
        for link_id in ticket.links:
            if link_id in all_tickets:
                lt = all_tickets[link_id]
                print(f"- {link_id} [{lt.status}] - {lt.title}")
            else:
                print(f"- {link_id} [missing]")
        print()


# ── info ─────────────────────────────────────────────────────


# [AI] Info shows frontmatter and relationships but no body/description.
def _handle_info(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    ticket = read_ticket(ticket_id, tickets_dir)

    if args.json:
        data = {
            "id": ticket.id,
            "title": ticket.title,
            "status": ticket.status,
            "type": ticket.type,
            "priority": ticket.priority,
            "assignee": ticket.assignee,
            "deps": ticket.deps,
            "links": ticket.links,
            "parent": ticket.parent,
            "tags": ticket.tags,
            "xref": ticket.xref,
            "resolution": ticket.resolution,
            "created": ticket.created,
        }
        print(json.dumps(data, indent=2))
        return

    # Print frontmatter fields only
    print(f"id: {ticket.id}")
    print(f"title: {ticket.title}")
    print(f"status: {ticket.status}")
    print(f"type: {ticket.type}")
    print(f"priority: {ticket.priority}")
    print(f"assignee: {ticket.assignee}")
    print(f"deps: {ticket.deps}")
    print(f"links: {ticket.links}")
    print(f"parent: {ticket.parent}")
    print(f"tags: {ticket.tags}")
    print(f"xref: {ticket.xref}")
    print(f"resolution: {ticket.resolution}")
    print(f"created: {ticket.created}")


# ── path ─────────────────────────────────────────────────────


def _handle_path(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    file_path = tickets_dir / f"{ticket_id}.md"
    print(file_path)


# ── deps ─────────────────────────────────────────────────────


# [AI] Render a dependency tree with box-drawing characters.
# Without --full, deduplicates nodes (shows each dep once).
# Children sorted by subtree depth (deepest first), then by ID.
def _handle_deps(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    all_tickets = _load_all_tickets(tickets_dir)
    assert ticket_id in all_tickets, f"resolved ID {ticket_id} not in tickets"

    seen: set[str] = set()

    def _subtree_depth(tid: str, visited: set[str] | None = None) -> int:
        """Compute max depth of the dependency subtree."""
        if visited is None:
            visited = set()
        if tid in visited or tid not in all_tickets:
            return 0
        visited.add(tid)
        t = all_tickets[tid]
        if not t.deps:
            return 0
        return 1 + max(_subtree_depth(d, visited) for d in t.deps)

    def _print_tree(tid: str, prefix: str, is_last: bool, is_root: bool) -> None:
        # Dedup check: skip entirely if already seen (unless --full or root)
        if not args.full and not is_root and tid in seen:
            return

        t = all_tickets.get(tid)
        if t is None:
            label = f"{tid} [missing]"
        else:
            label = _format_ticket_line(t)

        if is_root:
            print(label)
        else:
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{label}")

        if t is None:
            return

        seen.add(tid)

        child_prefix = prefix + ("    " if is_last else "│   ") if not is_root else ""

        # Sort children by subtree depth desc, then by ID
        deps_sorted = sorted(
            t.deps,
            key=lambda d: (-_subtree_depth(d), d),
        )

        for i, dep_id in enumerate(deps_sorted):
            is_last_child = i == len(deps_sorted) - 1
            _print_tree(dep_id, child_prefix, is_last_child, False)

    _print_tree(ticket_id, "", True, True)


# ── ls ───────────────────────────────────────────────────────


# [AI] List tickets with filtering, sorting, tree rendering.
# Default shows open + in_progress. --ready/--blocked use dependency analysis.
# Tree rendering groups children under parents with box-drawing chars.
def _handle_ls(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    if not all_tickets:
        return

    # -- Filtering --
    filtered: list[Ticket] = []

    if args.completed:
        filtered = [t for t in all_tickets.values()
                     if t.status == "closed" and t.resolution == "completed"]
    elif args.canceled:
        filtered = [t for t in all_tickets.values()
                     if t.status == "closed" and t.resolution == "canceled"]
    elif args.ready:
        for t in all_tickets.values():
            if t.status == "closed":
                continue
            if _is_blocked(t, all_tickets):
                continue
            filtered.append(t)
    elif args.blocked:
        for t in all_tickets.values():
            if t.status == "closed":
                continue
            if _is_blocked(t, all_tickets):
                filtered.append(t)
    elif args.status:
        filtered = [t for t in all_tickets.values() if t.status == args.status]
    else:
        # Default: open + in_progress
        filtered = [t for t in all_tickets.values()
                     if t.status in ("open", "in_progress")]

    # Additional filters (stackable)
    if args.assignee:
        filtered = [t for t in filtered if t.assignee == args.assignee]
    if args.tag:
        filtered = [t for t in filtered if args.tag in t.tags]
    if args.type:
        filtered = [t for t in filtered if t.type == args.type]

    # -- Sorting --
    if args.sort == "mtime":
        filtered.sort(
            key=lambda t: -(tickets_dir / f"{t.id}.md").stat().st_mtime
        )
    else:
        # Default: priority asc, then id asc
        filtered.sort(key=lambda t: (t.priority, t.id))

    # -- JSONL output --
    if args.jsonl:
        for t in filtered[:args.limit] if args.limit else filtered:
            data = {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "type": t.type,
                "priority": t.priority,
                "assignee": t.assignee,
                "deps": t.deps,
                "links": t.links,
                "parent": t.parent,
                "tags": t.tags,
            }
            print(json.dumps(data))
        return

    # -- Tree rendering --
    filtered_ids = {t.id for t in filtered}

    # Build parent->children map for filtered tickets
    children_map: dict[str | None, list[str]] = {}
    for t in filtered:
        children_map.setdefault(t.parent, []).append(t.id)

    # Determine which parents need to be shown as context
    # (parent not in filtered set but has children in filtered set).
    # Skip context parents for --ready/--blocked since those filters
    # explicitly exclude certain tickets.
    context_parents: set[str] = set()
    if not args.ready and not args.blocked:
        for t in filtered:
            if t.parent and t.parent not in filtered_ids:
                pid: str | None = t.parent
                while pid and pid not in filtered_ids:
                    context_parents.add(pid)
                    parent_ticket = all_tickets.get(pid)
                    if parent_ticket:
                        pid = parent_ticket.parent
                    else:
                        break

    # Root tickets: no parent, or parent not in filtered + context
    visible_ids = filtered_ids | context_parents

    def _get_visible_children(parent_id: str | None) -> list[str]:
        """Get children of parent_id that are in the visible set."""
        result: list[str] = []
        for tid in sorted(visible_ids):
            t = all_tickets.get(tid)
            if t and t.parent == parent_id:
                result.append(tid)
        return result

    # Check if a parent has any filtered descendants
    def _has_filtered_descendants(tid: str) -> bool:
        if tid in filtered_ids:
            return True
        for child_id in _get_visible_children(tid):
            if _has_filtered_descendants(child_id):
                return True
        return False

    printed_count = 0

    def _print_ls_tree(
        tid: str,
        prefix: str,
        is_last: bool,
        is_root: bool,
    ) -> None:
        nonlocal printed_count
        if args.limit and printed_count >= args.limit:
            return

        t = all_tickets.get(tid)
        if t is None:
            return

        is_context = tid in context_parents and tid not in filtered_ids

        if is_root:
            if is_context:
                print(_format_ticket_line(t))
            else:
                print(_format_ticket_line_with_deps(t))
                printed_count += 1
        else:
            connector = "└── " if is_last else "├── "
            if is_context:
                print(f"{prefix}{connector}{_format_ticket_line(t)}")
            else:
                print(f"{prefix}{connector}{_format_ticket_line_with_deps(t)}")
                printed_count += 1

        children = _get_visible_children(tid)
        # Sort children same as main sort
        if args.sort == "mtime":
            children.sort(
                key=lambda c: -(tickets_dir / f"{c}.md").stat().st_mtime
            )
        else:
            children.sort(key=lambda c: (all_tickets[c].priority, c))

        child_prefix = prefix + ("    " if is_last else "│   ") if not is_root else ""

        for i, child_id in enumerate(children):
            if args.limit and printed_count >= args.limit:
                return
            _print_ls_tree(child_id, child_prefix, i == len(children) - 1, False)

    # Get root-level tickets (no parent or parent not visible)
    roots: list[str] = []
    for tid in visible_ids:
        t = all_tickets.get(tid)
        if t and (t.parent is None or t.parent not in visible_ids):
            # Only include if has filtered descendants or is filtered itself
            if _has_filtered_descendants(tid):
                roots.append(tid)

    # Sort roots
    if args.sort == "mtime":
        roots.sort(key=lambda r: -(tickets_dir / f"{r}.md").stat().st_mtime)
    else:
        roots.sort(key=lambda r: (all_tickets[r].priority, r))

    for root_id in roots:
        if args.limit and printed_count >= args.limit:
            break
        _print_ls_tree(root_id, "", True, True)


# ── tags ─────────────────────────────────────────────────────


# [AI] List all tags with counts, sorted descending. Excludes closed tickets.
def _handle_tags(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    tag_counts: Counter[str] = Counter()
    for t in all_tickets.values():
        if t.status == "closed":
            continue
        for tag in t.tags:
            tag_counts[tag] += 1

    for tag, count in tag_counts.most_common():
        print(f"{tag} ({count})")


# ── links ────────────────────────────────────────────────────


# [AI] List all unique link pairs as "id-a <-> id-b" (sorted, deduped).
def _handle_links(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    seen_pairs: set[tuple[str, str]] = set()
    for t in all_tickets.values():
        for link_id in t.links:
            pair = tuple(sorted([t.id, link_id]))
            assert len(pair) == 2
            seen_pairs.add(pair)  # type: ignore[arg-type]

    for a, b in sorted(seen_pairs):
        print(f"{a} <-> {b}")


# ── archive ──────────────────────────────────────────────────


# [AI]
# Context: archive must not orphan references from active tickets
# Intent: find all tickets that reference a given ticket via deps, links, or parent
def _find_referrers(
    ticket_id: str, tickets: dict[str, Ticket],
) -> list[str]:
    referrers: list[str] = []
    for t in tickets.values():
        if t.id == ticket_id:
            continue
        if ticket_id in t.deps or ticket_id in t.links or t.parent == ticket_id:
            referrers.append(t.id)
    return sorted(referrers)


# [AI]
# Context: archive command with reference-safety check
# Intent: refuse to archive closed tickets still referenced by non-archived tickets
# Logic: iteratively shrink the archivable set -- removing a candidate makes it a
#   "remaining" ticket whose references block other candidates
def _handle_archive(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    closed_ids = {t.id for t in all_tickets.values() if t.status == "closed"}

    if not closed_ids:
        print("No closed tickets to archive")
        return

    archivable = set(closed_ids)
    changed = True
    while changed:
        changed = False
        remaining = {k: v for k, v in all_tickets.items() if k not in archivable}
        for tid in sorted(archivable):
            if _find_referrers(tid, remaining):
                archivable.discard(tid)
                changed = True

    skipped = closed_ids - archivable
    for tid in sorted(skipped):
        remaining = {k: v for k, v in all_tickets.items() if k not in archivable}
        refs = _find_referrers(tid, remaining)
        sys.stderr.write(f"Skipped {tid}: referenced by {', '.join(refs)}\n")

    if not archivable:
        print("No closed tickets eligible for archiving")
        return

    archive_dir = tickets_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    for tid in sorted(archivable):
        t = all_tickets[tid]
        src = tickets_dir / f"{t.id}.md"
        dst = archive_dir / f"{t.id}.md"
        shutil.move(str(src), str(dst))
        print(f"Archived {t.id}")

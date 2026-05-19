from __future__ import annotations

import argparse
import dataclasses
import json
import shutil
import sys
import typing as T
from collections import Counter
from pathlib import Path

from tiquette.store import (
    Status,
    Ticket,
    TicketNotFoundError,
    TicketSource,
    find_tickets_dir,
    is_terminal,
    load_all_tickets,
    read_ticket,
    resolve_id,
    resolve_id_in_dir,
)


# [AI] Query commands: show, info, path, deps, ls, tags, archive.
# ls has complex filtering with validation and mutual exclusion.

VALID_STATUSES = tuple(s.value for s in Status)


# [AI]
# Context: cli-redesign-v1.2 -- ticket-query requirement=list-tickets
# Intent: reject the legacy `completed` spelling with a message that points
#   the user at the new spelling AND at autofix (which migrates on-disk data).
def _validate_status(value: str) -> str:
    if value == "completed":
        raise argparse.ArgumentTypeError(
            "'completed' is no longer a valid status; use 'closed' instead (run `tq autofix` to migrate existing tickets)"
        )
    if value not in VALID_STATUSES:
        raise argparse.ArgumentTypeError(
            f"invalid choice: {value!r} (choose from {', '.join(repr(s) for s in VALID_STATUSES)})"
        )
    return value


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


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
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
        "-s",
        "--status",
        type=_validate_status,
        help="Filter by status (open|in_progress|closed|canceled)",
    )

    ready_group = p_ls.add_mutually_exclusive_group()
    ready_group.add_argument("--ready", action="store_true", help="Actionable tickets")
    ready_group.add_argument("--blocked", action="store_true", help="Blocked tickets")

    # [AI]
    # Context: ls-archived-flags -- ticket-query requirement=list-source-axis
    # Intent: source axis (active|archived|all); -a mirrors `ls -a`
    source_group = p_ls.add_mutually_exclusive_group()
    source_group.add_argument(
        "-a",
        "--all",
        action="store_true",
        dest="all_sources",
        help="Include archived tickets",
    )
    source_group.add_argument(
        "--archived",
        action="store_true",
        help="Show only archived tickets",
    )

    # [AI]
    # Context: ls-archived-flags -- ticket-query requirement=list-tickets
    # Intent: -A is short for --assignee (was -a, now freed for --all); -T avoids -t conflict
    p_ls.add_argument("-A", "--assignee", help="Filter by assignee")
    # [AI]
    # Context: cli-redesign-v1.2 -- ticket-query requirement=list-tickets
    # Intent: drop the `-T` short for `--tag`. `--tag` is short enough.
    p_ls.add_argument("--tag", help="Filter by tag")
    p_ls.add_argument("--type", help="Filter by type")

    # [AI]
    # Context: ls-parent-and-dep-filters -- ticket-query requirements list-filtered-by-parent + list-filtered-by-dependent
    # Intent: scope `ls` to a subtree (--parent) or to direct dependents of a ticket (--dep)
    scope_group = p_ls.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--parent",
        metavar="ID",
        help="Show <ID> and its descendants as a tree",
    )
    scope_group.add_argument(
        "--dep",
        metavar="ID",
        help="Show tickets that directly depend on <ID> (flat list)",
    )
    p_ls.add_argument(
        "--sort",
        choices=VALID_SORTS,
        default="priority",
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
    p_archive = subparsers.add_parser(
        "archive", help="Move closed and canceled tickets to archive"
    )
    p_archive.set_defaults(func=_handle_archive)


# ── Helpers ──────────────────────────────────────────────────


def _load_all_tickets(
    tickets_dir: Path,
    source: TicketSource = "active",
) -> dict[str, Ticket]:
    return load_all_tickets(tickets_dir, source)


_JsonValue = str | int | list[str] | None


def _ticket_to_dict(
    t: Ticket,
    *,
    include_body: bool = False,
    body: str | None = None,
) -> dict[str, _JsonValue]:
    """Serialize a Ticket to a JSON-compatible dict.

    If `include_body` is True, the caller should pass `body` (the raw markdown
    body extracted from the file); it is included under the "body" key.
    """
    data: dict[str, _JsonValue] = {
        "id": t.id,
        "title": t.title,
        "status": str(t.status),
        "type": t.type,
        "priority": t.priority,
        "assignee": t.assignee,
        "deps": t.deps,
        "links": t.links,
        "parent": t.parent,
        "tags": t.tags,
        "xref": t.xref,
        "created": t.created,
    }
    if include_body:
        data["body"] = body
    return data


def _resolve_or_exit(partial: str, tickets_dir: Path) -> str:
    """Resolve a partial ticket ID or exit with an error message."""
    try:
        return resolve_id_in_dir(partial, tickets_dir)
    except (TicketNotFoundError, ValueError) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


# [AI]
# Context: cli-redesign-v1.2 -- ticket-query requirement=list-ticket-line-format
# Intent: glyph keyed on status alone; closed=[x], canceled=[~]. v1.2 renamed
#   `completed` → `closed`.
def _checkbox(t: Ticket) -> str:
    match t.status:
        case Status.OPEN:
            return "[ ]"
        case Status.IN_PROGRESS:
            return "[/]"
        case Status.CLOSED:
            return "[x]"
        case Status.CANCELED:
            return "[~]"
        case _ as unreachable:
            T.assert_never(unreachable)


def _format_ticket_line(t: Ticket) -> str:
    parts: list[str] = []
    if t.priority != 2:
        parts.append(f"[P{t.priority}]")
    if t.type != "task":
        parts.append(f"[{t.type}]")
    tags = f" {''.join(parts)}" if parts else ""
    return f"{t.id}{tags} - {_checkbox(t)} {t.title}"


def _format_ticket_line_with_deps(t: Ticket) -> str:
    """Format ticket line, appending deps if present."""
    line = _format_ticket_line(t)
    if t.deps:
        dep_str = ", ".join(t.deps)
        line += f" <- [{dep_str}]"
    return line


# [AI] Determine if a ticket is "blocked": has non-terminal deps or non-terminal children.
def _is_blocked(
    ticket: Ticket,
    all_tickets: dict[str, Ticket],
) -> bool:
    for dep_id in ticket.deps:
        dep = all_tickets.get(dep_id)
        if dep is None:
            # Dangling dep: unknown ticket is treated as blocking.
            return True
        if not is_terminal(dep.status):
            return True
    for t in all_tickets.values():
        if t.parent == ticket.id and not is_terminal(t.status):
            return True
    return False


# [AI]
# Context: ls-parent-and-dep-filters -- ticket-query requirement=list-filtered-by-parent
# Intent: collect transitive descendants of `root_id` via parent pointers
def _descendants_of(root_id: str, all_tickets: dict[str, Ticket]) -> set[str]:
    children_by_parent: dict[str, list[str]] = {}
    for tid, t in all_tickets.items():
        if t.parent is not None:
            children_by_parent.setdefault(t.parent, []).append(tid)
    found: set[str] = set()
    queue = [root_id]
    while queue:
        cur = queue.pop()
        for child in children_by_parent.get(cur, ()):
            if child in found:
                continue
            found.add(child)
            queue.append(child)
    return found


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
    ticket_id = _resolve_or_exit(args.id, tickets_dir)

    ticket = read_ticket(ticket_id, tickets_dir)

    if args.json:
        # Read raw file body for the "body" field
        file_path = tickets_dir / f"{ticket_id}.md"
        raw = file_path.read_text()
        parts = raw.split("---\n")
        body = "---\n".join(parts[2:]).strip() if len(parts) >= 3 else ""
        print(
            json.dumps(_ticket_to_dict(ticket, include_body=True, body=body), indent=2)
        )
        return

    # Read and print raw file content (frontmatter + body)
    file_path = tickets_dir / f"{ticket_id}.md"
    print(file_path.read_text())

    # Load all tickets for relationship sections
    all_tickets = _load_all_tickets(tickets_dir)

    # Blockers: deps that are not yet in a terminal state
    open_deps = [
        dep_id
        for dep_id in ticket.deps
        if dep_id in all_tickets and not is_terminal(all_tickets[dep_id].status)
    ]
    if open_deps:
        print("## Blockers\n")
        for dep_id in open_deps:
            dep = all_tickets[dep_id]
            print(f"- {dep_id} [{dep.status}] - {dep.title}")
        print()

    # Blocking: tickets that depend on this one
    blocking = [t for t in all_tickets.values() if ticket_id in t.deps]
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
    ticket_id = _resolve_or_exit(args.id, tickets_dir)

    ticket = read_ticket(ticket_id, tickets_dir)

    if args.json:
        print(json.dumps(_ticket_to_dict(ticket), indent=2))
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
    print(f"created: {ticket.created}")


# ── path ─────────────────────────────────────────────────────


def _handle_path(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    ticket_id = _resolve_or_exit(args.id, tickets_dir)
    file_path = tickets_dir / f"{ticket_id}.md"
    print(file_path)


# ── deps ─────────────────────────────────────────────────────


def _subtree_depth(
    tid: str,
    all_tickets: dict[str, Ticket],
    memo: dict[str, int],
    visited: set[str] | None = None,
) -> int:
    """Compute max depth of the dependency subtree, memoized."""
    if tid in memo:
        return memo[tid]
    if visited is None:
        visited = set()
    if tid in visited or tid not in all_tickets:
        return 0
    visited.add(tid)
    t = all_tickets[tid]
    if not t.deps:
        result = 0
    else:
        result = 1 + max(_subtree_depth(d, all_tickets, memo, visited) for d in t.deps)
    memo[tid] = result
    return result


@dataclasses.dataclass
class _DepTreePrinter:
    """Holds shared state for the recursive dep-tree printer."""

    all_tickets: dict[str, Ticket]
    full: bool
    seen: set[str] = dataclasses.field(default_factory=set)
    depth_memo: dict[str, int] = dataclasses.field(default_factory=dict)

    def print_tree(self, tid: str, prefix: str, is_last: bool, is_root: bool) -> None:
        # Dedup: skip entirely if already seen (unless --full or root).
        if not self.full and not is_root and tid in self.seen:
            return

        t = self.all_tickets.get(tid)
        label = _format_ticket_line(t) if t is not None else f"{tid} [missing]"

        if is_root:
            print(label)
        else:
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{label}")

        if t is None:
            return

        self.seen.add(tid)
        child_prefix = prefix + ("    " if is_last else "│   ") if not is_root else ""
        deps_sorted = sorted(
            t.deps,
            key=lambda d: (-_subtree_depth(d, self.all_tickets, self.depth_memo), d),
        )
        for i, dep_id in enumerate(deps_sorted):
            self.print_tree(dep_id, child_prefix, i == len(deps_sorted) - 1, False)


# [AI] Render a dependency tree with box-drawing characters.
# Without --full, deduplicates nodes (shows each dep once).
# Children sorted by subtree depth (deepest first), then by ID.
def _handle_deps(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    ticket_id = _resolve_or_exit(args.id, tickets_dir)
    all_tickets = _load_all_tickets(tickets_dir)
    assert ticket_id in all_tickets, f"resolved ID {ticket_id} not in tickets"

    printer = _DepTreePrinter(all_tickets=all_tickets, full=args.full)
    printer.print_tree(ticket_id, "", True, True)


@dataclasses.dataclass
class _TreePrinter:
    """Holds shared state for the recursive ls tree printer."""

    all_tickets: dict[str, Ticket]
    filtered_ids: set[str]
    context_parents: set[str]
    visible_ids: set[str]
    tickets_dir: Path
    sort_key: str  # "priority" or "mtime"
    limit: int | None
    printed_count: int = dataclasses.field(default=0, init=False)

    def _get_visible_children(self, parent_id: str | None) -> list[str]:
        result: list[str] = []
        for tid in sorted(self.visible_ids):
            t = self.all_tickets.get(tid)
            if t and t.parent == parent_id:
                result.append(tid)
        return result

    def has_filtered_descendants(self, tid: str) -> bool:
        if tid in self.filtered_ids:
            return True
        for child_id in self._get_visible_children(tid):
            if self.has_filtered_descendants(child_id):
                return True
        return False

    def _sort_children(self, children: list[str]) -> None:
        if self.sort_key == "mtime":
            children.sort(key=lambda c: -(self.tickets_dir / f"{c}.md").stat().st_mtime)
        else:
            children.sort(key=lambda c: (self.all_tickets[c].priority, c))

    def print_tree(self, tid: str, prefix: str, is_last: bool, is_root: bool) -> None:
        if self.limit is not None and self.printed_count >= self.limit:
            return

        t = self.all_tickets.get(tid)
        if t is None:
            return

        is_context = tid in self.context_parents and tid not in self.filtered_ids

        if is_root:
            if is_context:
                print(_format_ticket_line(t))
            else:
                print(_format_ticket_line_with_deps(t))
                self.printed_count += 1
        else:
            connector = "└── " if is_last else "├── "
            if is_context:
                print(f"{prefix}{connector}{_format_ticket_line(t)}")
            else:
                print(f"{prefix}{connector}{_format_ticket_line_with_deps(t)}")
                self.printed_count += 1

        children = self._get_visible_children(tid)
        self._sort_children(children)

        child_prefix = prefix + ("    " if is_last else "│   ") if not is_root else ""

        for i, child_id in enumerate(children):
            if self.limit is not None and self.printed_count >= self.limit:
                return
            self.print_tree(child_id, child_prefix, i == len(children) - 1, False)


# ── ls ───────────────────────────────────────────────────────


# [AI] ls pipeline stage 1: resolve which ticket store to load based on source axis flags.
def _select_source(args: argparse.Namespace, tickets_dir: Path) -> dict[str, Ticket]:
    source: TicketSource
    if args.archived:
        source = "archived"
    elif args.all_sources:
        source = "all"
    else:
        source = "active"
    return _load_all_tickets(tickets_dir, source=source)


class _LsScopeError(Exception):
    """Raised by _apply_scope when a --parent/--dep target can't be resolved."""


# [AI]
# Context: ls-parent-and-dep-filters -- requirements list-filtered-by-parent + list-filtered-by-dependent
# Intent: resolve scope ID and narrow candidates; returns (candidate_ids, scope_root).
# candidate_ids=None means "all tickets". scope_root is the --parent anchor for tree context.
def _apply_scope(
    args: argparse.Namespace,
    all_tickets: dict[str, Ticket],
) -> tuple[set[str] | None, str | None]:
    raw_scope = args.parent or args.dep
    if raw_scope is None:
        return None, None

    if not all_tickets:
        raise _LsScopeError(f"ticket '{raw_scope}' not found")

    try:
        scope_id = resolve_id(raw_scope, all_tickets.keys())
    except (TicketNotFoundError, ValueError) as e:
        raise _LsScopeError(str(e)) from e

    if args.parent:
        return {scope_id} | _descendants_of(scope_id, all_tickets), scope_id
    # --dep: tickets whose deps directly contain scope_id (excludes self)
    return {tid for tid, t in all_tickets.items() if scope_id in t.deps}, None


# [AI]
# Context: ls decomposition -- ticket-query requirement=list-tickets
# Intent: apply primary filter (ready/blocked/status/all) then stackable
#   attribute filters (assignee/tag/type), then sort. Single responsibility.
def _apply_filter(
    args: argparse.Namespace,
    candidates: T.Iterable[Ticket],
    all_tickets: dict[str, Ticket],
    tickets_dir: Path,
) -> list[Ticket]:
    filtered: list[Ticket] = []

    if args.ready:
        for t in candidates:
            if is_terminal(t.status):
                continue
            if not _is_blocked(t, all_tickets):
                filtered.append(t)
    elif args.blocked:
        for t in candidates:
            if is_terminal(t.status):
                continue
            if _is_blocked(t, all_tickets):
                filtered.append(t)
    elif args.status:
        filtered = [t for t in candidates if t.status == args.status]
    else:
        filtered = list(candidates)

    if args.assignee:
        filtered = [t for t in filtered if t.assignee == args.assignee]
    if args.tag:
        filtered = [t for t in filtered if args.tag in t.tags]
    if args.type:
        filtered = [t for t in filtered if t.type == args.type]

    if args.sort == "mtime":
        filtered.sort(key=lambda t: -(tickets_dir / f"{t.id}.md").stat().st_mtime)
    else:
        filtered.sort(key=lambda t: (t.priority, t.id))

    return filtered


# [AI]
# Context: ls-parent-and-dep-filters -- requirement=list-filtered-by-dependent
# Intent: flat output for --dep mode; tree rendering is suppressed because
#   parent/child structure is orthogonal to dependency relationships.
def _render_flat(filtered: list[Ticket], args: argparse.Namespace) -> None:
    for t in filtered[: args.limit] if args.limit else filtered:
        print(_format_ticket_line_with_deps(t))


def _render_jsonl(filtered: list[Ticket], args: argparse.Namespace) -> None:
    for t in filtered[: args.limit] if args.limit else filtered:
        print(json.dumps(_ticket_to_dict(t)))


# [AI]
# Context: ls decomposition -- ticket-query requirement=list-tickets
# Intent: tree output for standard ls. Climbs to context parents so
#   children always appear under their ancestors. Delegates recursive
#   rendering to _TreePrinter.
def _render_tree(
    filtered: list[Ticket],
    args: argparse.Namespace,
    all_tickets: dict[str, Ticket],
    candidate_ids: set[str] | None,
    scope_root: str | None,
    tickets_dir: Path,
) -> None:
    filtered_ids = {t.id for t in filtered}

    # [AI]
    # Context: ls-parent-and-dep-filters -- requirement=list-filtered-by-parent
    # Intent: cap the climb at scope_root so the tree never shows ancestors
    #   above the named --parent ticket; ensure scope_root itself is added as
    #   context even when --ready/--blocked otherwise suppresses climbing.
    context_parents: set[str] = set()
    climb_full = not args.ready and not args.blocked
    if climb_full:
        for t in filtered:
            if t.parent and t.parent not in filtered_ids:
                pid: str | None = t.parent
                while pid and pid not in filtered_ids:
                    if candidate_ids is not None and pid not in candidate_ids:
                        break
                    context_parents.add(pid)
                    if pid == scope_root:
                        break
                    parent_ticket = all_tickets.get(pid)
                    if parent_ticket:
                        pid = parent_ticket.parent
                    else:
                        break
    elif scope_root is not None and scope_root not in filtered_ids:
        context_parents.add(scope_root)

    visible_ids = filtered_ids | context_parents

    printer = _TreePrinter(
        all_tickets=all_tickets,
        filtered_ids=filtered_ids,
        context_parents=context_parents,
        visible_ids=visible_ids,
        tickets_dir=tickets_dir,
        sort_key=args.sort,
        limit=args.limit,
    )

    roots: list[str] = []
    for tid in visible_ids:
        t = all_tickets.get(tid)
        if t and (t.parent is None or t.parent not in visible_ids):
            if printer.has_filtered_descendants(tid):
                roots.append(tid)

    if args.sort == "mtime":
        roots.sort(key=lambda r: -(tickets_dir / f"{r}.md").stat().st_mtime)
    else:
        roots.sort(key=lambda r: (all_tickets[r].priority, r))

    for root_id in roots:
        if args.limit is not None and printer.printed_count >= args.limit:
            break
        printer.print_tree(root_id, "", True, True)


# [AI]
# Context: ls decomposition -- ticket-query requirement=list-tickets
# Intent: thin driver; delegates to pipeline stages so each concern is isolated.
def _handle_ls(args: argparse.Namespace) -> None:
    # Reject empty-string scope flags before any further processing.
    if args.dep == "":
        print("error: --dep requires a non-empty ticket ID", file=sys.stderr)
        sys.exit(1)
    if args.parent == "":
        print("error: --parent requires a non-empty ticket ID", file=sys.stderr)
        sys.exit(1)

    tickets_dir = find_tickets_dir()
    all_tickets = _select_source(args, tickets_dir)
    try:
        candidate_ids, scope_root = _apply_scope(args, all_tickets)
    except _LsScopeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    if not all_tickets:
        return

    candidates: T.Iterable[Ticket]
    if candidate_ids is not None:
        candidates = [all_tickets[tid] for tid in candidate_ids]
    else:
        candidates = all_tickets.values()

    filtered = _apply_filter(args, candidates, all_tickets, tickets_dir)

    if args.dep and not args.jsonl:
        _render_flat(filtered, args)
        return

    if args.jsonl:
        _render_jsonl(filtered, args)
        return

    _render_tree(filtered, args, all_tickets, candidate_ids, scope_root, tickets_dir)


# ── tags ─────────────────────────────────────────────────────


# [AI] List all tags with counts, sorted descending. Excludes terminal tickets.
def _handle_tags(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    tag_counts: Counter[str] = Counter()
    for t in all_tickets.values():
        if is_terminal(t.status):
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
            pair = (t.id, link_id) if t.id < link_id else (link_id, t.id)
            seen_pairs.add(pair)

    for a, b in sorted(seen_pairs):
        print(f"{a} <-> {b}")


# ── archive ──────────────────────────────────────────────────


def _build_referrer_index(all_tickets: dict[str, Ticket]) -> dict[str, set[str]]:
    referrers_of: dict[str, set[str]] = {tid: set() for tid in all_tickets}
    for t in all_tickets.values():
        for dep_id in t.deps:
            if dep_id in referrers_of:
                referrers_of[dep_id].add(t.id)
        for link_id in t.links:
            if link_id in referrers_of:
                referrers_of[link_id].add(t.id)
        if t.parent is not None and t.parent in referrers_of:
            referrers_of[t.parent].add(t.id)
    return referrers_of


# [AI]
# Context: tiqt-6e82 -- propagation must follow every outgoing reference kind
#   (deps, links, parent). Previously links were tracked in the referrer index
#   but omitted from propagation, so a link-only chain leaked through.
def _compute_archivable(
    all_tickets: dict[str, Ticket],
    terminal_ids: set[str],
    referrers_of: dict[str, set[str]],
) -> tuple[set[str], set[str]]:
    archivable = set(terminal_ids)
    not_archivable: set[str] = set()
    work_queue = [tid for tid in terminal_ids if referrers_of[tid] - terminal_ids]
    visited: set[str] = set()
    while work_queue:
        tid = work_queue.pop()
        if tid in visited:
            continue
        visited.add(tid)
        if tid not in archivable:
            continue
        archivable.discard(tid)
        not_archivable.add(tid)
        t = all_tickets[tid]
        outgoing = (*t.deps, *t.links, *((t.parent,) if t.parent is not None else ()))
        for ref_id in outgoing:
            if ref_id in archivable:
                work_queue.append(ref_id)
    return archivable, not_archivable


def _move_to_archive(
    tickets_dir: Path, all_tickets: dict[str, Ticket], archivable: set[str]
) -> None:
    archive_dir = tickets_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    for tid in sorted(archivable):
        t = all_tickets[tid]
        src = tickets_dir / f"{t.id}.md"
        dst = archive_dir / f"{t.id}.md"
        shutil.move(str(src), str(dst))
        print(f"Archived {t.id}")


# [AI]
# Context: split-closed-status -- archive command with reference-safety check
# Intent: refuse to archive terminal (closed/canceled) tickets still referenced
#   by non-terminal tickets. Reverse-reference index propagates unarchivable
#   IDs along every outgoing reference (deps, links, parent).
def _handle_archive(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    all_tickets = _load_all_tickets(tickets_dir)

    terminal_ids = {t.id for t in all_tickets.values() if is_terminal(t.status)}
    if not terminal_ids:
        print("No closed or canceled tickets to archive")
        return

    referrers_of = _build_referrer_index(all_tickets)
    archivable, not_archivable = _compute_archivable(
        all_tickets, terminal_ids, referrers_of
    )

    for tid in sorted(not_archivable):
        active_refs = sorted(referrers_of[tid] - archivable - not_archivable)
        if not active_refs:
            active_refs = sorted(referrers_of[tid])
        sys.stderr.write(f"Skipped {tid}: referenced by {', '.join(active_refs)}\n")

    if not archivable:
        print("No closed or canceled tickets eligible for archiving")
        return

    _move_to_archive(tickets_dir, all_tickets, archivable)

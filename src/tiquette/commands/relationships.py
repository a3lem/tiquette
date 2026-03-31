from __future__ import annotations

import argparse
import sys
import typing as T

from tiquette.store import (
    Ticket,
    TicketNotFoundError,
    TicketsNotFoundError,
    find_tickets_dir,
    list_ticket_ids,
    read_ticket,
    write_ticket,
)


# [AI] Relationship commands: dep, undep, nest, unnest, link, unlink.


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # dep <id> <dep_id> [dep_id...]
    p_dep = subparsers.add_parser("dep", help="Add dependency")
    p_dep.add_argument("id", help="Ticket ID")
    p_dep.add_argument("dep_ids", nargs="+", help="Dependency IDs", metavar="dep-id")
    p_dep.set_defaults(func=_handle_dep)

    # undep <id> <dep_id> [dep_id...]
    p_undep = subparsers.add_parser("undep", help="Remove dependency")
    p_undep.add_argument("id", help="Ticket ID")
    p_undep.add_argument("dep_ids", nargs="+", help="Dependency IDs", metavar="dep-id")
    p_undep.set_defaults(func=_handle_undep)

    # nest <child> [child...] <parent> -- last arg is parent
    p_nest = subparsers.add_parser(
        "nest", help="Set parent (last arg is parent)",
        usage="tq nest child [child ...] parent",
    )
    p_nest.add_argument("ids", nargs="+", help="Child ID(s) followed by parent ID")
    p_nest.set_defaults(func=_handle_nest)

    # unnest <id> [id...]
    p_unnest = subparsers.add_parser("unnest", help="Remove from parent")
    p_unnest.add_argument("ids", nargs="+", help="Ticket ID(s)")
    p_unnest.set_defaults(func=_handle_unnest)

    # link <id> <id> [id...] -- needs >=2
    p_link = subparsers.add_parser("link", help="Associate tickets")
    p_link.add_argument("ids", nargs="+", help="Ticket IDs (at least 2)")
    p_link.set_defaults(func=_handle_link)

    # unlink <id> <id> [id...] -- needs >=2
    p_unlink = subparsers.add_parser("unlink", help="Remove association(s)")
    p_unlink.add_argument("ids", nargs="+", help="Ticket IDs (at least 2)")
    p_unlink.set_defaults(func=_handle_unlink)


def _error_exit(msg: str) -> T.NoReturn:
    print(msg, file=sys.stderr)
    sys.exit(1)


# [AI]
# Context: ticket-relationships requirement=cycle-detection
# Intent: build dep graph for cycle detection before writing
def _build_dep_graph(tickets_dir: T.Any) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for tid in list_ticket_ids(tickets_dir):
        t = read_ticket(tid, tickets_dir)
        graph[tid] = list(t.deps)
    return graph


# [AI]
# Context: ticket-relationships requirement=cycle-detection
# Intent: DFS from new dep targets back through graph to detect cycle
def _has_cycle(
    graph: dict[str, list[str]],
    source: str,
    new_deps: list[str],
) -> bool:
    original = graph.get(source, [])
    graph[source] = list(set(original + new_deps))

    visited: set[str] = set()
    stack: list[str] = list(new_deps)
    while stack:
        node = stack.pop()
        if node == source:
            graph[source] = original
            return True
        if node in visited:
            continue
        visited.add(node)
        stack.extend(graph.get(node, []))

    graph[source] = original
    return False


# [AI]
# Context: ticket-relationships requirement=add-dependency
# Intent: add deps with validation, dedup, and cycle detection
def _handle_dep(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    try:
        source = read_ticket(args.id, tickets_dir)
    except TicketNotFoundError:
        _error_exit(f"ticket '{args.id}' not found")

    for dep_id in args.dep_ids:
        try:
            read_ticket(dep_id, tickets_dir)
        except TicketNotFoundError:
            _error_exit(f"ticket '{dep_id}' not found")

    new_deps = [d for d in args.dep_ids if d not in source.deps]

    if new_deps:
        graph = _build_dep_graph(tickets_dir)
        if _has_cycle(graph, args.id, new_deps):
            _error_exit("error: adding dependency would create a cycle")

        source.deps.extend(new_deps)
        write_ticket(source, tickets_dir)


def _handle_undep(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    try:
        source = read_ticket(args.id, tickets_dir)
    except TicketNotFoundError:
        _error_exit(f"ticket '{args.id}' not found")

    for dep_id in args.dep_ids:
        if dep_id not in source.deps:
            _error_exit(f"error: '{dep_id}' is not a dependency of '{args.id}'")

    for dep_id in args.dep_ids:
        source.deps.remove(dep_id)

    write_ticket(source, tickets_dir)


def _handle_nest(args: argparse.Namespace) -> None:
    if len(args.ids) < 2:
        print("error: nest requires at least a child and a parent", file=sys.stderr)
        sys.exit(2)

    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    parent_id = args.ids[-1]
    child_ids = args.ids[:-1]

    try:
        read_ticket(parent_id, tickets_dir)
    except TicketNotFoundError:
        _error_exit(f"ticket '{parent_id}' not found")

    children: list[Ticket] = []
    for cid in child_ids:
        try:
            children.append(read_ticket(cid, tickets_dir))
        except TicketNotFoundError:
            _error_exit(f"ticket '{cid}' not found")

    for child in children:
        child.parent = parent_id
        write_ticket(child, tickets_dir)


def _handle_unnest(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    for tid in args.ids:
        try:
            ticket = read_ticket(tid, tickets_dir)
        except TicketNotFoundError:
            _error_exit(f"ticket '{tid}' not found")
        ticket.parent = None
        write_ticket(ticket, tickets_dir)


# [AI]
# Context: ticket-relationships requirement=link-tickets
# Intent: symmetric linking -- every pair gets both directions
def _handle_link(args: argparse.Namespace) -> None:
    if len(args.ids) < 2:
        print("error: link requires at least 2 IDs", file=sys.stderr)
        sys.exit(2)

    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    tickets: dict[str, Ticket] = {}
    for tid in args.ids:
        try:
            tickets[tid] = read_ticket(tid, tickets_dir)
        except TicketNotFoundError:
            _error_exit(f"ticket '{tid}' not found")

    ids = args.ids
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if b not in tickets[a].links:
                tickets[a].links.append(b)
            if a not in tickets[b].links:
                tickets[b].links.append(a)

    for ticket in tickets.values():
        write_ticket(ticket, tickets_dir)


def _handle_unlink(args: argparse.Namespace) -> None:
    if len(args.ids) < 2:
        print("error: unlink requires at least 2 IDs", file=sys.stderr)
        sys.exit(2)

    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        _error_exit("no .tickets directory found")

    tickets: dict[str, Ticket] = {}
    for tid in args.ids:
        try:
            tickets[tid] = read_ticket(tid, tickets_dir)
        except TicketNotFoundError:
            _error_exit(f"ticket '{tid}' not found")

    ids = args.ids
    removed_any = False
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if b in tickets[a].links:
                tickets[a].links.remove(b)
                removed_any = True
            if a in tickets[b].links:
                tickets[b].links.remove(a)
                removed_any = True

    if not removed_any:
        _error_exit("error: no links found between specified tickets")

    for ticket in tickets.values():
        write_ticket(ticket, tickets_dir)

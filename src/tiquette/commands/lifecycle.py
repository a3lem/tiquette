from __future__ import annotations

import argparse
import sys
import typing as T
from pathlib import Path

from tiquette.store import (
    Ticket,
    TicketNotFoundError,
    TicketsNotFoundError,
    find_tickets_dir,
    generate_id,
    read_ticket,
    write_ticket,
)


# [AI] Lifecycle commands: create, start, close, cancel, reopen.
# Each handler is a stub that validates args and exits 0.

VALID_TYPES = ("bug", "feature", "task", "epic", "chore")
VALID_PRIORITIES = ("0", "1", "2", "3", "4")


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # [AI] create: optional title positional, many optional flags
    p_create = subparsers.add_parser("create", help="Create ticket, prints ID")
    p_create.add_argument("title", nargs="?", default=None, help="Ticket title")
    p_create.add_argument("-d", "--description", default=None, help="Body content")
    p_create.add_argument(
        "-t", "--type", default="task", choices=VALID_TYPES,
        help="Type (bug|feature|task|epic|chore)",
    )
    p_create.add_argument(
        "-p", "--priority", default="2", choices=VALID_PRIORITIES,
        help="Priority 0-4, 0=highest",
    )
    p_create.add_argument("-a", "--assignee", default=None, help="Assignee")
    p_create.add_argument("--xref", default=None, help="External reference")
    p_create.add_argument("--parent", default=None, help="Parent ticket ID")
    p_create.add_argument("--tag", action="append", default=None, help="Tag (repeat for multiple)")
    p_create.add_argument("--dep", action="append", default=None, help="Blocker ID (repeat for multiple)")
    p_create.set_defaults(func=_handle_create)

    # [AI] Simple status-transition commands: one required positional id
    for name, helptext in [
        ("start", "Set status to in_progress"),
        ("close", "Set status to closed (completed)"),
        ("cancel", "Set status to closed (canceled)"),
        ("reopen", "Set status to open"),
    ]:
        p = subparsers.add_parser(name, help=helptext)
        p.add_argument("id", help="Ticket ID")
        p.set_defaults(func=_handle_status)


# [AI]
# Context: ticket-lifecycle requirement=create-ticket, requirement=tickets-directory-auto-creation
# Intent: create ticket file, auto-create .tickets/ on demand, print ID to stdout
def _handle_create(args: argparse.Namespace) -> None:
    from pathlib import Path

    from tiquette.store import TicketsNotFoundError

    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        tickets_dir = Path.cwd() / ".tickets"

    # Auto-create .tickets/ on demand for create command
    tickets_dir.mkdir(parents=True, exist_ok=True)

    ticket_id = generate_id(tickets_dir)
    title = args.title if args.title is not None else "Untitled"

    ticket = Ticket(
        id=ticket_id,
        title=title,
        type=args.type,
        priority=int(args.priority),
        assignee=args.assignee,
        xref=args.xref,
        parent=args.parent,
        tags=args.tag or [],
        deps=args.dep or [],
        description=args.description,
    )

    write_ticket(ticket, tickets_dir)
    sys.stdout.write(ticket_id + "\n")


# [AI]
# Context: ticket-lifecycle requirements for start/close/cancel/reopen
# Intent: collect all open descendants by walking parent→child tree recursively
def _find_open_descendants(ticket_id: str, tickets_dir: Path) -> list[str]:
    all_tickets: list[Ticket] = []
    for f in tickets_dir.iterdir():
        if f.suffix == ".md":
            all_tickets.append(read_ticket(f.stem, tickets_dir))

    children_of: dict[str, list[Ticket]] = {}
    for t in all_tickets:
        if t.parent:
            children_of.setdefault(t.parent, []).append(t)

    open_descendants: list[str] = []

    def _walk(parent_id: str) -> None:
        for child in children_of.get(parent_id, []):
            if child.status != "closed":
                open_descendants.append(child.id)
            _walk(child.id)

    _walk(ticket_id)
    return open_descendants


# [AI]
# Context: ticket-lifecycle requirement=close-command scenario=close-notifies-last-open-child
# Intent: notify when closing a child leaves its parent with no open children
def _check_last_open_child(ticket: Ticket, tickets_dir: Path) -> None:
    if not ticket.parent:
        return

    for f in tickets_dir.iterdir():
        if f.suffix != ".md":
            continue
        sibling = read_ticket(f.stem, tickets_dir)
        if sibling.id == ticket.id:
            continue
        if sibling.parent == ticket.parent and sibling.status != "closed":
            return

    sys.stdout.write(f"note: {ticket.parent} has no remaining open children\n")


def _handle_status(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        return

    try:
        ticket = read_ticket(args.id, tickets_dir)
    except TicketNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    command: str = args.command
    assert command in ("start", "close", "cancel", "reopen"), f"unexpected: {command}"

    if command == "start":
        ticket.status = "in_progress"
    elif command == "close":
        open_desc = _find_open_descendants(ticket.id, tickets_dir)
        if open_desc:
            desc_list = ", ".join(open_desc)
            sys.stderr.write(f"error: {ticket.id} has open descendants: {desc_list}\n")
            sys.exit(1)
        ticket.status = "closed"
        ticket.resolution = "completed"
        _check_last_open_child(ticket, tickets_dir)
    elif command == "cancel":
        ticket.status = "closed"
        ticket.resolution = "canceled"
    elif command == "reopen":
        ticket.status = "open"
        ticket.resolution = None

    write_ticket(ticket, tickets_dir)
    # [AI]
    # Context: fix-cli-output-gaps -- ticket-lifecycle requirement=transition-output
    # Intent: confirm which ticket was affected; placed after write so it only
    #   fires on success (failures sys.exit before reaching this line)
    sys.stdout.write(ticket.id + "\n")

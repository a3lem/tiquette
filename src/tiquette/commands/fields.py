from __future__ import annotations

import argparse
import sys
import typing as T

from tiquette.store import (
    TicketNotFoundError,
    TicketsNotFoundError,
    find_tickets_dir,
    read_ticket,
    write_ticket,
)

VALID_PRIORITIES = ("0", "1", "2", "3", "4")
VALID_TYPES = ("bug", "feature", "task", "epic", "chore")


# [AI]
# Context: CLI skeleton, fields group
# Intent: assign and xref use optional positional to set/clear in one command


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # assign <id> [assignee]
    p_assign = subparsers.add_parser("assign", help="Set or clear assignee")
    p_assign.add_argument("id", help="Ticket ID")
    p_assign.add_argument("assignee", nargs="?", default=None, help="Assignee name (omit to clear)")
    p_assign.set_defaults(func=_handle_assign)

    # change-prio <id> <priority>
    p_prio = subparsers.add_parser("change-prio", help="Update priority")
    p_prio.add_argument("id", help="Ticket ID")
    p_prio.add_argument("priority", choices=VALID_PRIORITIES, help="Priority 0-4")
    p_prio.set_defaults(func=_handle_change_prio)

    # change-type <id> <type>
    p_type = subparsers.add_parser("change-type", help="Change ticket type")
    p_type.add_argument("id", help="Ticket ID")
    p_type.add_argument("type", choices=VALID_TYPES, help="Ticket type")
    p_type.set_defaults(func=_handle_change_type)

    # tag <id> <tag> [tag...]
    p_tag = subparsers.add_parser("tag", help="Append tag(s)")
    p_tag.add_argument("id", help="Ticket ID")
    p_tag.add_argument("tags", nargs="+", help="Tag(s) to add")
    p_tag.set_defaults(func=_handle_tag)

    # untag <id> <tag> [tag...]
    p_untag = subparsers.add_parser("untag", help="Remove tag(s)")
    p_untag.add_argument("id", help="Ticket ID")
    p_untag.add_argument("tags", nargs="+", help="Tag(s) to remove")
    p_untag.set_defaults(func=_handle_untag)

    # xref <id> [xref]
    p_xref = subparsers.add_parser("xref", help="Set or clear external reference")
    p_xref.add_argument("id", help="Ticket ID")
    p_xref.add_argument("xref", nargs="?", default=None, help="External reference (omit to clear)")
    p_xref.set_defaults(func=_handle_xref)


# [AI]
# Context: ticket-fields -- shared by all field mutation handlers
# Intent: load ticket with error handling, return (ticket, tickets_dir)
def _load_ticket(ticket_id: str) -> tuple[T.Any, T.Any] | None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        return None
    try:
        ticket = read_ticket(ticket_id, tickets_dir)
    except TicketNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    return ticket, tickets_dir


# [AI]
# Context: ticket-fields requirement=assign
# Intent: set, reassign, or clear (when omitted) the assignee field
def _handle_assign(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    ticket.assignee = args.assignee
    write_ticket(ticket, tickets_dir)


def _handle_change_prio(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    ticket.priority = int(args.priority)
    write_ticket(ticket, tickets_dir)


def _handle_change_type(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    ticket.type = args.type
    write_ticket(ticket, tickets_dir)


# [AI]
# Context: ticket-fields requirement=tag-management
# Intent: extend tags, deduplicate while preserving order
def _handle_tag(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    existing = set(ticket.tags)
    for tag in args.tags:
        if tag not in existing:
            ticket.tags.append(tag)
            existing.add(tag)
    write_ticket(ticket, tickets_dir)


def _handle_untag(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    to_remove = set(args.tags)
    ticket.tags = [t for t in ticket.tags if t not in to_remove]
    write_ticket(ticket, tickets_dir)


def _handle_xref(args: argparse.Namespace) -> None:
    result = _load_ticket(args.id)
    if result is None:
        return
    ticket, tickets_dir = result
    ticket.xref = args.xref
    write_ticket(ticket, tickets_dir)

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from tiquette.commands._fields import add_create_flags, namespace_to_field_changes
from tiquette.store import (
    FieldChangeError,
    Status,
    Ticket,
    TicketNotFoundError,
    TicketsNotFoundError,
    apply_field_changes,
    find_tickets_dir,
    generate_id,
    is_terminal,
    read_ticket,
    resolve_id,
    write_ticket,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    # [AI]
    # Context: cli-redesign-v1.2 -- ticket-lifecycle requirement=create-ticket
    # Intent: title is required positional. Field-flags come from the shared
    #   _fields schema so `create` and `edit` stay in lockstep.
    p_create = subparsers.add_parser("create", help="Create ticket, prints ID")
    p_create.add_argument("title", help="Ticket title")
    add_create_flags(p_create)
    p_create.set_defaults(func=_handle_create)

    # [AI]
    # Context: cascade-close-cancel -- ticket-lifecycle requirements=close-command,cancel-command
    # Intent: close/cancel gain -f/--force to cascade through open descendants;
    #   start/reopen stay flagless.
    for name, helptext in [
        ("start", "Set status to in_progress"),
        ("close", "Set status to closed"),
        ("cancel", "Set status to canceled"),
        ("reopen", "Set status to open"),
    ]:
        p = subparsers.add_parser(name, help=helptext)
        p.add_argument("id", help="Ticket ID")
        if name in ("close", "cancel"):
            p.add_argument(
                "-f",
                "--force",
                action="store_true",
                help="Force closure; cascade to open descendants",
            )
        p.set_defaults(func=_handle_status)


# [AI]
# Context: cli-redesign-v1.2 -- ticket-lifecycle requirement=create-ticket
# Intent: create a fresh ticket then route through the shared
#   apply_field_changes pipeline. The note timestamp is the same UTC
#   instant as the ticket's `created` field (one clock read per call).
def _handle_create(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        tickets_dir = Path.cwd() / ".tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()
    ticket_id = generate_id(tickets_dir)
    ticket = Ticket(id=ticket_id, title=args.title, created=now)

    changes = namespace_to_field_changes(args, edit_mode=False)
    # Defaults: only apply when the user didn't pass the flag.
    if changes.type is None:
        changes.type = "task"
    if changes.priority is None:
        changes.priority = 2

    try:
        extra = apply_field_changes(ticket, changes, tickets_dir, note_timestamp=now)
    except FieldChangeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    for other in extra:
        write_ticket(other, tickets_dir)
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
            if not is_terminal(child):
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
        if sibling.parent == ticket.parent and not is_terminal(sibling):
            return

    sys.stdout.write(f"note: {ticket.parent} has no remaining open children\n")


def _handle_status(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        return

    try:
        ticket_id = resolve_id(args.id, tickets_dir)
        ticket = read_ticket(ticket_id, tickets_dir)
    except TicketNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    command: str = args.command
    assert command in ("start", "close", "cancel", "reopen"), f"unexpected: {command}"

    if command == "start":
        ticket.status = Status.IN_PROGRESS
    elif command in ("close", "cancel"):
        # [AI]
        # Context: cli-redesign-v1.2 -- ticket-lifecycle requirements=close-command,cancel-command
        # Intent: shared descendant rejection + optional force-cascade. The terminal
        #   status (`closed` for close, `canceled` for cancel) is set directly on
        #   each ticket; no resolution field is written. v1.2 renamed `completed`
        #   → `closed` so the stored value matches the verb.
        terminal_status = Status.CLOSED if command == "close" else Status.CANCELED
        open_desc = _find_open_descendants(ticket.id, tickets_dir)
        if open_desc and not args.force:
            desc_list = ", ".join(open_desc)
            sys.stderr.write(f"error: {ticket.id} has open descendants: {desc_list}\n")
            sys.exit(1)
        # Cascade descendants first so a partial failure leaves the parent open
        # (and therefore re-runnable) rather than closed-with-orphans. Each
        # cascaded ID is printed after its successful write so the user sees
        # exactly what landed on disk if a later write fails.
        for desc_id in open_desc:
            desc = read_ticket(desc_id, tickets_dir)
            desc.status = terminal_status
            write_ticket(desc, tickets_dir)
            sys.stdout.write(desc.id + "\n")
        ticket.status = terminal_status
        write_ticket(ticket, tickets_dir)
        sys.stdout.write(ticket.id + "\n")
        if command == "close":
            _check_last_open_child(ticket, tickets_dir)
        return

    if command == "reopen":
        ticket.status = Status.OPEN

    write_ticket(ticket, tickets_dir)
    # [AI]
    # Context: fix-cli-output-gaps -- ticket-lifecycle requirement=transition-output
    # Intent: confirm which ticket was affected; placed after write so it only
    #   fires on success (failures sys.exit before reaching this line)
    sys.stdout.write(ticket.id + "\n")

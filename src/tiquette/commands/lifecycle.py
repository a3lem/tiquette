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
    load_all_tickets,
    read_ticket,
    resolve_id_in_dir,
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
    #   start/reopen stay flagless. Each subparser carries its target Status
    #   in set_defaults so _handle_status dispatches on the Status enum, not
    #   on the subcommand name.
    for name, helptext, target in [
        ("start", "Set status to in_progress", Status.IN_PROGRESS),
        ("close", "Set status to closed", Status.CLOSED),
        ("cancel", "Set status to canceled", Status.CANCELED),
        ("reopen", "Set status to open", Status.OPEN),
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
        p.set_defaults(func=_handle_status, target_status=target)


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
# Intent: collect all open descendants by walking parent→child tree recursively;
#   returns a dict so callers can reuse the loaded Ticket objects for mutation.
def _find_open_descendants(
    ticket_id: str,
    all_tickets: dict[str, Ticket],
) -> dict[str, Ticket]:
    children_of: dict[str, list[Ticket]] = {}
    for t in all_tickets.values():
        if t.parent:
            children_of.setdefault(t.parent, []).append(t)

    open_descendants: dict[str, Ticket] = {}

    def _walk(parent_id: str) -> None:
        for child in children_of.get(parent_id, []):
            if not is_terminal(child.status):
                open_descendants[child.id] = child
            _walk(child.id)

    _walk(ticket_id)
    return open_descendants


# [AI]
# Context: ticket-lifecycle requirement=close-command scenario=close-notifies-last-open-child
# Intent: notify when closing a child leaves its parent with no open children
def _check_last_open_child(
    ticket: Ticket,
    all_tickets: dict[str, Ticket],
) -> None:
    if not ticket.parent:
        return

    for sibling in all_tickets.values():
        if sibling.id == ticket.id:
            continue
        if sibling.parent == ticket.parent and not is_terminal(sibling.status):
            return

    sys.stdout.write(f"note: {ticket.parent} has no remaining open children\n")


def _handle_status(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()

    try:
        ticket_id = resolve_id_in_dir(args.id, tickets_dir)
        ticket = read_ticket(ticket_id, tickets_dir)
    except TicketNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    target: Status = args.target_status

    if is_terminal(target):
        # [AI]
        # Context: cli-redesign-v1.2 -- ticket-lifecycle requirements=close-command,cancel-command
        # Intent: shared descendant rejection + optional force-cascade. The terminal
        #   status (`closed` or `canceled`) is set directly on each ticket;
        #   no resolution field is written.
        all_tickets = load_all_tickets(tickets_dir)
        open_desc = _find_open_descendants(ticket.id, all_tickets)
        if open_desc and not args.force:
            desc_list = ", ".join(sorted(open_desc))
            sys.stderr.write(f"error: {ticket.id} has open descendants: {desc_list}\n")
            sys.exit(1)
        # Cascade descendants first so a partial failure leaves the parent open
        # (and therefore re-runnable) rather than closed-with-orphans.
        for desc in open_desc.values():
            desc.status = target
            write_ticket(desc, tickets_dir)
            sys.stdout.write(desc.id + "\n")
        ticket.status = target
        write_ticket(ticket, tickets_dir)
        sys.stdout.write(ticket.id + "\n")
        if target is Status.CLOSED:
            all_tickets[ticket.id] = ticket
            _check_last_open_child(ticket, all_tickets)
        return

    ticket.status = target
    write_ticket(ticket, tickets_dir)
    # [AI]
    # Context: fix-cli-output-gaps -- ticket-lifecycle requirement=transition-output
    # Intent: confirm which ticket was affected; placed after write so it only
    #   fires on success (failures sys.exit before reaching this line)
    sys.stdout.write(ticket.id + "\n")

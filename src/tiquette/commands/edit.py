"""The `edit` subcommand: single post-creation mutation surface.

# spec: ticket-edit
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from tiquette.commands._fields import add_edit_flags, namespace_to_field_changes
from tiquette.store import (
    FieldChangeError,
    TicketNotFoundError,
    TicketsNotFoundError,
    apply_field_changes,
    find_tickets_dir,
    read_ticket,
    resolve_id_in_dir,
    write_ticket,
)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = subparsers.add_parser("edit", help="Modify ticket fields")
    p.add_argument("id", help="Ticket ID")
    add_edit_flags(p)
    p.set_defaults(func=_handle_edit)


def _handle_edit(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        sys.stderr.write("error: no .tickets directory found\n")
        sys.exit(1)

    try:
        ticket_id = resolve_id_in_dir(args.id, tickets_dir)
        ticket = read_ticket(ticket_id, tickets_dir)
    except TicketNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    changes = namespace_to_field_changes(args, edit_mode=True)

    if changes.is_empty():
        sys.stderr.write(
            "error: `tq edit` requires at least one field-option (see `tq edit --help`)\n"
        )
        sys.exit(2)

    note_ts = datetime.now(timezone.utc).isoformat() if changes.notes else None

    try:
        extra = apply_field_changes(
            ticket, changes, tickets_dir, note_timestamp=note_ts
        )
    except FieldChangeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    # Atomic-ish: write self last so a partial failure on a link-target write
    # leaves the source unchanged.
    for other in extra:
        write_ticket(other, tickets_dir)
    write_ticket(ticket, tickets_dir)
    sys.stdout.write(ticket.id + "\n")

from __future__ import annotations

import argparse
import sys
import typing as T
from datetime import datetime, timezone

from tiquette.store import (
    AmbiguousIDError,
    TicketNotFoundError,
    TicketsNotFoundError,
    find_tickets_dir,
    read_ticket,
    resolve_id,
    write_ticket,
)


# [AI]
# Context: ticket-content commands: describe, add-note
# Intent: describe uses Ticket model; add-note manipulates raw file for ## Notes


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # describe <id> <text>
    p_describe = subparsers.add_parser("describe", help="Set/replace description")
    p_describe.add_argument("id", help="Ticket ID")
    p_describe.add_argument("text", help="Description text")
    p_describe.set_defaults(func=_handle_describe)

    # add-note <id> [text] -- text optional for stdin support
    p_addnote = subparsers.add_parser("add-note", help="Append timestamped note")
    p_addnote.add_argument("id", help="Ticket ID")
    p_addnote.add_argument("text", nargs="?", default=None, help="Note text (reads stdin if omitted)")
    p_addnote.set_defaults(func=_handle_add_note)


# [AI]
# Context: ticket-content requirement=describe
# Intent: read ticket, set description, write back
def _handle_describe(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        return

    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, AmbiguousIDError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    ticket = read_ticket(ticket_id, tickets_dir)
    ticket.description = args.text
    write_ticket(ticket, tickets_dir)


# [AI]
# Context: ticket-content requirement=add-note
# Intent: append timestamped note to raw file; cannot use Ticket model
#   because notes are not part of the dataclass
def _handle_add_note(args: argparse.Namespace) -> None:
    try:
        tickets_dir = find_tickets_dir()
    except TicketsNotFoundError:
        return

    try:
        ticket_id = resolve_id(args.id, tickets_dir)
    except (TicketNotFoundError, AmbiguousIDError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    ticket_path = tickets_dir / f"{ticket_id}.md"

    text: str | None = args.text
    if text is None:
        text = sys.stdin.read().strip()

    timestamp = datetime.now(timezone.utc).isoformat()
    note_line = f"- {timestamp}: {text}" if text else f"- {timestamp}:"

    content = ticket_path.read_text()

    if "## Notes" in content:
        # Append to existing notes section
        idx = content.index("## Notes")
        rest = content[idx + len("## Notes"):]
        next_section = rest.find("\n## ")
        if next_section == -1:
            if not content.endswith("\n"):
                content += "\n"
            content += note_line + "\n"
        else:
            insert_pos = idx + len("## Notes") + next_section
            content = content[:insert_pos] + note_line + "\n" + content[insert_pos:]
    else:
        if not content.endswith("\n"):
            content += "\n"
        content += "\n## Notes\n\n" + note_line + "\n"

    ticket_path.write_text(content)

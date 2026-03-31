from __future__ import annotations

import argparse
import typing as T


# [AI] Content commands: describe, add-note.
# Both take id + text as required positionals.


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # describe <id> <text>
    p_describe = subparsers.add_parser("describe", help="Set/replace description")
    p_describe.add_argument("id", help="Ticket ID")
    p_describe.add_argument("text", help="Description text")
    p_describe.set_defaults(func=_handle_describe)

    # add-note <id> <text>
    p_addnote = subparsers.add_parser("add-note", help="Append timestamped note")
    p_addnote.add_argument("id", help="Ticket ID")
    p_addnote.add_argument("text", help="Note text")
    p_addnote.set_defaults(func=_handle_add_note)


def _handle_describe(args: argparse.Namespace) -> None:
    pass


def _handle_add_note(args: argparse.Namespace) -> None:
    pass

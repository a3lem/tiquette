from __future__ import annotations

import argparse
import typing as T


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


def _handle_create(args: argparse.Namespace) -> None:
    pass


def _handle_status(args: argparse.Namespace) -> None:
    pass

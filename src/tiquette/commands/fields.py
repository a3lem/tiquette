from __future__ import annotations

import argparse
import sys
import typing as T

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


def _handle_assign(args: argparse.Namespace) -> None:
    pass


def _handle_change_prio(args: argparse.Namespace) -> None:
    pass


def _handle_change_type(args: argparse.Namespace) -> None:
    pass


def _handle_tag(args: argparse.Namespace) -> None:
    pass


def _handle_untag(args: argparse.Namespace) -> None:
    pass


def _handle_xref(args: argparse.Namespace) -> None:
    pass

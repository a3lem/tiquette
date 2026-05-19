"""Shared field-flag argparse schema for `create` and `edit`.

# spec: ticket-edit
# spec: ticket-lifecycle requirement=create-ticket
"""

from __future__ import annotations

import argparse

from tiquette.store import FieldChanges

VALID_TYPES = ("bug", "feature", "task", "epic", "chore")
UNSET_TARGETS = ("parent", "xref", "assignee")


# [AI]
# Context: cli-redesign-v1.2 -- ticket-edit, ticket-lifecycle
# Intent: the shared subset accepted on both `create` and `edit`. Adding a
#   field happens here, once.
def _add_shared_field_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-d", "--description", default=None, help="Description (markdown body)"
    )
    parser.add_argument(
        "-t",
        "--type",
        default=None,
        choices=VALID_TYPES,
        help="Type (bug|feature|task|epic|chore)",
    )
    parser.add_argument(
        "-p",
        "--priority",
        default=None,
        type=int,
        choices=range(5),
        help="Priority 0-4, 0=highest",
    )
    parser.add_argument("-A", "--assignee", default=None, help="Assignee")
    parser.add_argument("--xref", default=None, help="External reference")
    parser.add_argument("--parent", default=None, help="Parent ticket ID")
    parser.add_argument(
        "--tag", action="append", default=None, help="Tag (repeat for multiple)"
    )
    parser.add_argument(
        "--dep", action="append", default=None, help="Blocker ID (repeat for multiple)"
    )
    parser.add_argument(
        "--link",
        action="append",
        default=None,
        help="Associated ticket ID (symmetric, repeatable)",
    )
    parser.add_argument(
        "--note", action="append", default=None, help="Timestamped note (repeatable)"
    )


def add_create_flags(parser: argparse.ArgumentParser) -> None:
    """Register field-flags on a `create` subparser."""
    _add_shared_field_flags(parser)


def add_edit_flags(parser: argparse.ArgumentParser) -> None:
    """Register field-flags + edit-only removers on an `edit` subparser."""
    parser.add_argument("--title", default=None, help="Rename ticket")
    _add_shared_field_flags(parser)
    parser.add_argument(
        "--untag", action="append", default=None, help="Remove tag (repeatable)"
    )
    parser.add_argument(
        "--undep", action="append", default=None, help="Remove blocker (repeatable)"
    )
    parser.add_argument(
        "--unlink",
        action="append",
        default=None,
        help="Remove association (repeatable)",
    )
    parser.add_argument(
        "--unset",
        action="append",
        default=None,
        choices=UNSET_TARGETS,
        help="Clear a single-value field (parent|xref|assignee), repeatable",
    )


# [AI]
# Context: cli-redesign-v1.2 -- ticket-edit
# Intent: convert the argparse Namespace into a FieldChanges. Both `create`
#   and `edit` go through this so validation/dispatch share one shape.
def namespace_to_field_changes(
    args: argparse.Namespace, *, edit_mode: bool
) -> FieldChanges:
    return FieldChanges(
        title=getattr(args, "title", None) if edit_mode else None,
        description=args.description,
        type=args.type,
        priority=args.priority,
        assignee=args.assignee,
        xref=args.xref,
        parent=args.parent,
        add_tags=list(args.tag or []),
        remove_tags=list(getattr(args, "untag", None) or []) if edit_mode else [],
        add_deps=list(args.dep or []),
        remove_deps=list(getattr(args, "undep", None) or []) if edit_mode else [],
        add_links=list(args.link or []),
        remove_links=list(getattr(args, "unlink", None) or []) if edit_mode else [],
        notes=list(args.note or []),
        unset_fields=set(getattr(args, "unset", None) or []) if edit_mode else set(),
    )

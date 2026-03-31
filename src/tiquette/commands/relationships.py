from __future__ import annotations

import argparse
import sys
import typing as T


# [AI] Relationship commands: dep, undep, nest, unnest, link, unlink.
# Validation: nest needs >=2 args, link/unlink need >=2 args,
# dep/undep need id + at least one dep_id.


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # [AI] dep <id> <dep_id> [dep_id...]
    p_dep = subparsers.add_parser("dep", help="Add dependency")
    p_dep.add_argument("id", help="Ticket ID")
    p_dep.add_argument("dep_ids", nargs="+", help="Dependency IDs", metavar="dep-id")
    p_dep.set_defaults(func=_handle_dep)

    # [AI] undep <id> <dep_id> [dep_id...]
    p_undep = subparsers.add_parser("undep", help="Remove dependency")
    p_undep.add_argument("id", help="Ticket ID")
    p_undep.add_argument("dep_ids", nargs="+", help="Dependency IDs", metavar="dep-id")
    p_undep.set_defaults(func=_handle_undep)

    # [AI] nest <child> [child...] <parent> -- last arg is parent
    p_nest = subparsers.add_parser(
        "nest", help="Set parent (last arg is parent)",
        usage="tq nest child [child ...] parent",
    )
    p_nest.add_argument("ids", nargs="+", help="Child ID(s) followed by parent ID")
    p_nest.set_defaults(func=_handle_nest)

    # [AI] unnest <id> [id...]
    p_unnest = subparsers.add_parser("unnest", help="Remove from parent")
    p_unnest.add_argument("ids", nargs="+", help="Ticket ID(s)")
    p_unnest.set_defaults(func=_handle_unnest)

    # [AI] link <id> <id> [id...] -- needs >=2
    p_link = subparsers.add_parser("link", help="Associate tickets")
    p_link.add_argument("ids", nargs="+", help="Ticket IDs (at least 2)")
    p_link.set_defaults(func=_handle_link)

    # [AI] unlink <id> <id> [id...] -- needs >=2
    p_unlink = subparsers.add_parser("unlink", help="Remove association(s)")
    p_unlink.add_argument("ids", nargs="+", help="Ticket IDs (at least 2)")
    p_unlink.set_defaults(func=_handle_unlink)


def _handle_dep(args: argparse.Namespace) -> None:
    pass


def _handle_undep(args: argparse.Namespace) -> None:
    pass


def _handle_nest(args: argparse.Namespace) -> None:
    # [AI] Must have at least 2 args (child + parent)
    if len(args.ids) < 2:
        print("error: nest requires at least a child and a parent", file=sys.stderr)
        sys.exit(2)


def _handle_unnest(args: argparse.Namespace) -> None:
    pass


def _handle_link(args: argparse.Namespace) -> None:
    # [AI] Must have at least 2 IDs
    if len(args.ids) < 2:
        print("error: link requires at least 2 IDs", file=sys.stderr)
        sys.exit(2)


def _handle_unlink(args: argparse.Namespace) -> None:
    # [AI] Must have at least 2 IDs
    if len(args.ids) < 2:
        print("error: unlink requires at least 2 IDs", file=sys.stderr)
        sys.exit(2)

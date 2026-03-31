from __future__ import annotations

import argparse
import sys
import typing as T


# [AI] Query commands: show, info, path, deps, ls, tags, archive.
# ls has complex filtering with validation and mutual exclusion.

VALID_STATUSES = ("open", "in_progress", "closed")
VALID_SORTS = ("priority", "mtime")


def _positive_int(value: str) -> int:
    # [AI] Custom argparse type: must be int > 0
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid int value: '{value}'")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"limit must be a positive integer, got {n}")
    return n


def register(subparsers: T._GenericAlias) -> None:  # type: ignore[name-defined]
    # show <id> [--json]
    p_show = subparsers.add_parser("show", help="Display ticket")
    p_show.add_argument("id", help="Ticket ID")
    p_show.add_argument("--json", action="store_true", help="Output as JSON")
    p_show.set_defaults(func=_handle_show)

    # info <id> [--json]
    p_info = subparsers.add_parser("info", help="Frontmatter + relationships")
    p_info.add_argument("id", help="Ticket ID")
    p_info.add_argument("--json", action="store_true", help="Output as JSON")
    p_info.set_defaults(func=_handle_info)

    # path <id>
    p_path = subparsers.add_parser("path", help="Print file path")
    p_path.add_argument("id", help="Ticket ID")
    p_path.set_defaults(func=_handle_path)

    # deps <id> [--full]
    p_deps = subparsers.add_parser("deps", help="Show dependency tree")
    p_deps.add_argument("id", help="Ticket ID")
    p_deps.add_argument("--full", action="store_true", help="Disable dedup")
    p_deps.set_defaults(func=_handle_deps)

    # [AI] ls: many optional filters, mutual exclusion for --ready/--blocked
    p_ls = subparsers.add_parser("ls", help="List tickets")
    p_ls.add_argument(
        "--status", choices=VALID_STATUSES,
        help="Filter by status (open|in_progress|closed)",
    )

    ready_group = p_ls.add_mutually_exclusive_group()
    ready_group.add_argument("--ready", action="store_true", help="Actionable tickets")
    ready_group.add_argument("--blocked", action="store_true", help="Blocked tickets")

    p_ls.add_argument("--completed", action="store_true", help="Resolution = completed")
    p_ls.add_argument("--canceled", action="store_true", help="Resolution = canceled")
    p_ls.add_argument("--assignee", help="Filter by assignee")
    p_ls.add_argument("--tag", help="Filter by tag")
    p_ls.add_argument("--type", help="Filter by type")
    p_ls.add_argument(
        "--sort", choices=VALID_SORTS, default="priority",
        help="Sort by field (priority|mtime)",
    )
    p_ls.add_argument("--limit", type=_positive_int, help="Limit results")
    p_ls.add_argument("--jsonl", action="store_true", help="Output as JSON Lines")
    p_ls.set_defaults(func=_handle_ls)

    # tags (no args)
    p_tags = subparsers.add_parser("tags", help="List all tags with counts")
    p_tags.set_defaults(func=_handle_tags)

    # links (no args)
    p_links = subparsers.add_parser("links", help="List all linked pairs")
    p_links.set_defaults(func=_handle_links)

    # archive (no args)
    p_archive = subparsers.add_parser("archive", help="Move closed tickets to archive")
    p_archive.set_defaults(func=_handle_archive)


def _handle_show(args: argparse.Namespace) -> None:
    pass


def _handle_info(args: argparse.Namespace) -> None:
    pass


def _handle_path(args: argparse.Namespace) -> None:
    pass


def _handle_deps(args: argparse.Namespace) -> None:
    pass


def _handle_ls(args: argparse.Namespace) -> None:
    pass


def _handle_tags(args: argparse.Namespace) -> None:
    pass


def _handle_links(args: argparse.Namespace) -> None:
    pass


def _handle_archive(args: argparse.Namespace) -> None:
    pass

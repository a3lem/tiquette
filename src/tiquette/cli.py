from __future__ import annotations

import argparse
import sys
import typing as T

from tiquette.commands import autofix, content, fields, lifecycle, query, relationships, validate
from tiquette.store import TicketsNotFoundError


# [AI]
# Context: cli-design.md spec, two-tier help system
# Intent: bare `tq` shows a scannable summary; `tq --help` shows the full
#   reference with all flags, intended for system prompts and detailed lookup
HELP_SUMMARY = """\
tq - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Lifecycle:
  create [title]                        Create ticket, prints ID
  start <id>                            Set status to in_progress
  close <id>                            Close as completed
  cancel <id>                           Close as canceled
  reopen <id>                           Reopen (clears resolution)
  archive                               Move closed tickets to archive

Relationships:
  dep <id> <dep-id>...                  Add blocking dependency
  undep <id> <dep-id>...                Remove dependency
  nest <child>... <parent>              Set parent
  unnest <id>...                        Remove from parent
  link <id> <id>...                     Associate tickets (symmetric)
  unlink <id> <id>...                   Remove association(s)
  deps <id>                             Show dependency tree
  links                                 List all linked pairs

Fields:
  assign <id> [assignee]                Set or clear assignee
  change-prio <id> <priority>           Update priority (0-4)
  change-type <id> <type>               Change ticket type
  tag <id> <tag> [tag...]               Append tag(s)
  untag <id> <tag> [tag...]             Remove tag(s)
  xref <id> [xref]                      Set or clear external reference
  tags                                  List all tags with counts

Content:
  describe <id> <text>                  Set/replace description
  add-note <id> <text>                  Append timestamped note

View:
  ls [options]                          List tickets
  show <id>                             Display ticket
  info <id>                             Frontmatter + relationships
  path <id>                             Print file path

Maintenance:
  validate                              Check tickets for integrity problems
  autofix                               Update tickets to match current behavior

Run tq --help for full reference with all flags and options.
"""

HELP_TEXT = """\
tq - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Frequently Used
---------------
  ls --ready                            List open tickets that are not blocked
  show <id>                             Display ticket (meta + body)
  create [title]                        Create new ticket (prints ID)
  start <id>                            Set ticket status to in_progress
  close <id>                            Close ticket as completed

Commands
--------

Lifecycle:
  create [title] [options]              Create ticket, prints ID
    -d, --description TEXT              Body content (markdown below frontmatter)
    -t, --type TYPE                     bug|feature|task|epic|chore [default: task]
    -p, --priority N                    0-4, 0=highest [default: 2]
    -a, --assignee NAME                 Assignee [default: null]
    --xref REF                          External reference (e.g., gh-123, JIRA-456)
    --parent ID                         Parent ticket ID
    --tag TAG                           Tag (repeat for multiple)
    --dep ID                            Blocker ID (repeat for multiple)
  start <id>                            Set status to in_progress
  close <id> [-f]                       Set status to closed (resolution: completed)
                                        -f/--force cascades through open descendants
  cancel <id> [-f]                      Set status to closed (resolution: canceled)
                                        -f/--force cascades through open descendants
  reopen <id>                           Set status to open (clears resolution)
  archive                               Move closed/canceled tickets to archive directory

Relationships:
  dep <id> <dep-id> [dep-id...]         Add dependency (id is blocked by dep-ids)
  undep <id> <dep-id> [dep-id...]       Remove blocking dependency
  nest <child> [child...] <parent>      Set parent (last arg is destination, like mv)
  unnest <id> [id...]                   Remove from parent
  link <id> <id> [id...]                Associate tickets (symmetric, informational)
  unlink <id> <id> [id...]              Remove association(s)
  deps <id> [--full]                    Show dependency tree (--full disables dedup)
  links                                 List all linked pairs across tickets

Fields:
  assign <id> [assignee]                Set or clear assignee
  change-prio <id> <priority>           Update priority: 0-4, 0=highest
  change-type <id> <type>               Change ticket type
  tag <id> <tag> [tag...]               Append tag(s)
  untag <id> <tag> [tag...]             Remove tag(s)
  xref <id> [xref]                      Set or clear external reference
  tags                                  List all tags with counts, sorted by frequency

Content:
  describe <id> <text>                  Set/replace description section
  add-note <id> <text>                  Append timestamped note (or pipe via stdin)

View:
  ls [options]                          List tickets [default: all statuses]
    --status X                          Filter: open|in_progress|closed
    --ready                             Actionable: no unresolved deps or open children
    --blocked                           Has unresolved deps or open children
    --completed                         Resolution = completed (implies --status closed)
    --canceled                          Resolution = canceled (implies --status closed)
    --assignee NAME                     Filter by assignee
    --tag TAG                           Filter by tag
    --type TYPE                         Filter by type
    --sort FIELD                        Sort: priority|mtime [default: priority]
    --limit N                           Limit results
    --jsonl                             Output as JSON Lines (one object per ticket)
  show <id> [--json]                    Display ticket (frontmatter + body)
  info <id> [--json]                    Frontmatter + computed relationships (no body)
  path <id>                             Print file path for direct editing

Maintenance:
  validate                              Check all tickets for referential integrity
  autofix                               Update tickets to be consistent with current behavior
"""


class SectionedHelpAction(argparse._HelpAction):
    # [AI] Override the default help action to print the static help text.
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: T.Any,
        option_string: str | None = None,
    ) -> T.NoReturn:
        sys.stdout.write(HELP_TEXT)
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tq",
        description="tq - a minimal ticket system for AI agents that need to track tasks",
        add_help=False,
    )
    # [AI] Replace default -h/--help with our sectioned help action
    parser.add_argument(
        "-h",
        "--help",
        action=SectionedHelpAction,
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    # [AI] Register all command groups
    lifecycle.register(subparsers)
    relationships.register(subparsers)
    fields.register(subparsers)
    content.register(subparsers)
    query.register(subparsers)
    validate.register(subparsers)
    autofix.register(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        sys.stdout.write(HELP_SUMMARY)
        return

    try:
        args.func(args)
    except TicketsNotFoundError:
        sys.stderr.write("No .tickets/ directory found\n")
        sys.exit(1)

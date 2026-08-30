from __future__ import annotations

import argparse
import difflib
import re
import sys
import typing as T

from tiquette import __version__
from tiquette.commands import autofix, edit, lifecycle, query, validate
from tiquette.store import TicketParseError, TicketsNotFoundError


# [AI]
# Context: cli-redesign-v1.2 -- consolidates field mutations into `edit`;
#   renames terminal status `completed` → `closed`.
# Intent: bare `tq` prints HELP_SUMMARY; `tq --help` prints HELP_TEXT (the
#   full reference matching docs/cli-design.md).
HELP_SUMMARY = """\
tq - a minimal ticket system with dependency tracking

Usage: tq [--dir PATH] <command> [args]

Lifecycle:
  create <title>                        Create ticket, prints ID
  edit <id>                             Modify ticket fields
  start <id>...                         Set status to in_progress
  close <id>...                         Set status to closed (ticket is complete)
  cancel <id>...                        Set status to canceled
  reopen <id>...                        Set status to open
  archive                               Move closed and canceled tickets to archive

View:
  ls [options]                          List tickets
  show <id>...                          Display ticket
  info <id>...                          Frontmatter + relationships
  path <id>...                          Print file path
  deps <id>                             Show dependency tree
  links                                 List all linked pairs
  tags                                  List all tags with counts

Maintenance:
  validate                              Check tickets for integrity problems
  autofix                               Update tickets to match current behavior
  prune [filters] [-y]                  Permanently delete archived tickets by filter

Run tq --help for full reference with all flags and options.
"""

HELP_TEXT = """\
tq (tiquette) - a minimal ticket system with dependency tracking

Usage: tq [--dir PATH] <command> [args]

Global options (before the command)
-----------------------------------
  --dir PATH                            Operate on the store at PATH/.tickets.
                                        Overrides TICKETS_DIR and walk-up. In a
                                        monorepo, targets one project's tickets.

Frequently Used
---------------
  ls --ready                            List open tickets that are not blocked
  show <id>...                          Display ticket (meta + body)
  create <title> [field-options]        Create new ticket (prints ID)
  edit <id> [field-options]             Modify ticket fields
  start <id>...                         Set ticket status to in_progress
  close <id>...                         Set status to closed (ticket is complete)

Commands
--------
(<id> / ID below always refers to a ticket ID)

Lifecycle:
  create <title> [field-options]        Create ticket, prints ID
    -d, --description TEXT              Description (markdown body)
    -t, --type TYPE                     bug|feature|task|epic|chore [default: task]
    -p, --priority N                    0-4, 0=highest [default: 2]
    -A, --assignee NAME                 Assignee [default: null]
        --xref REF                      External reference, e.g. gh-123
        --parent ID                     Nest under parent (makes this ticket a child of ID)
        --tag TAG                       Add tag (repeatable)
        --dep ID                        Register blocking dependency on other ticket (repeatable)
        --link ID                       Associate ticket (repeatable, symmetric)
        --note TEXT                     Append timestamped note (repeatable)

  edit <id> [field-options]             Modify ticket fields
                                        Accepts all create field-options (above), plus:
        --title TEXT                    Rename ticket
        --untag TAG                     Remove tag (repeatable)
        --undep ID                      Remove blocker (repeatable)
        --unlink ID                     Remove association (repeatable)
        --unset FIELD                   Clear a single-value field (repeatable)
                                        FIELD in {parent, xref, assignee}
                                        Setting and unsetting the same field in
                                        the same call is an error.

  start <id>... [--note]                Set status to in_progress
  close <id>... [-f] [--note]           Set status to closed (ticket is complete)
                                        -f/--force cascades through open descendants
                                        Multiple IDs: validated up front, all-or-nothing
  cancel <id>... [-f] [--note]          Set status to canceled
                                        -f/--force cascades through open descendants
                                        Multiple IDs: validated up front, all-or-nothing
  reopen <id>... [--note]               Set status to open
                                        Optional --note on all status changes to motivate
                                        status change (repeatable)
  archive                               Move closed and canceled tickets to archive

View:
  ls [options]                          List tickets [default: all statuses]
    -s, --status X                      Filter: open|in_progress|closed|canceled
    --ready                             Actionable: no unresolved deps or open children
    --blocked                           Has unresolved deps or open children
    -a, --all                           Include archived tickets
    --archived                          Show only archived tickets
    --tag TAG                           Filter by tag
    --type TYPE                         Filter by type
    -A, --assignee NAME                 Filter by assignee
    --parent ID                         Show ticket and its descendants as a tree
    --dep ID                            Show tickets that directly depend on ID (flat list)
    -r, --recursive                     Aggregate every store at/below the root, grouped by
                                        store path (read-only; not with --parent/--dep)
    --sort FIELD                        Sort: priority|mtime [default: priority]
    --limit N                           Limit results
    --jsonl                             Output as JSON Lines (one object per ticket)
  show <id>... [--json]                 Display ticket (frontmatter + body)
  info <id>... [--json]                 Frontmatter + computed relationships (no body)
                                        --json: one object for a single ID, a
                                        JSON array for multiple IDs
  path <id>...                          Print file path for direct editing
  deps <id> [--full]                    Show dependency tree (--full disables dedup)
  links                                 List all linked pairs across tickets
  tags                                  List all tags with counts, sorted by frequency

Maintenance:
  validate                              Check all tickets for referential integrity
  autofix                               Update tickets to be consistent with current behavior
  prune [filters] [-y]                  Permanently delete archived tickets by filter
    -s, --status X                      Filter: closed|canceled
    -t, --type TYPE                     Filter by type
    --before YYYY-MM-DD                 Match tickets created strictly before date
    -y, --yes                           Actually delete (default: dry run)
                                        At least one filter required

Examples
--------
  tq create 'Fix parser dropping trailing commas' -d 'parser.py:142' -t bug -p 1
  tq edit abf1 --tag urgent --untag stale -p 0 --note 'customer escalation'
  tq edit abf1 --parent 9zk2 --dep 4mn8
  tq ls --ready --tag backend --sort priority
"""


# [AI]
# Context: variadic-read-commands -- unknown-command hints (tiqt-aa0e).
# Intent: teach the canonical form instead of aliasing. A 2026-08 usage
#   analysis showed agents guessing `note`/`comment`/`tree`; v1.2 removed the
#   per-field verbs "gone, not aliased" -- these hints keep that stance while
#   collapsing the three-round-trip recovery into one error message. Values
#   are full canonical invocations (error text, never new surface).
_REDIRECT_HINTS: dict[str, str] = {
    # note-taking guesses
    "note": "tq edit <id> --note TEXT",
    "comment": "tq edit <id> --note TEXT",
    "annotate": "tq edit <id> --note TEXT",
    "log": "tq edit <id> --note TEXT",
    # hierarchy view (the help says "tree" under ls --parent)
    "tree": "tq ls --parent <id>",
    # v1.2-removed verbs -> their edit equivalents
    "add-note": "tq edit <id> --note TEXT",
    "tag": "tq edit <id> --tag TAG",
    "untag": "tq edit <id> --untag TAG",
    "dep": "tq edit <id> --dep ID",
    "undep": "tq edit <id> --undep ID",
    "link": "tq edit <id> --link ID",
    "unlink": "tq edit <id> --unlink ID",
    "nest": "tq edit <child> --parent <parent-id>",
    "unnest": "tq edit <id> --unset parent",
    "assign": "tq edit <id> -A NAME",
    "describe": "tq edit <id> -d TEXT",
    "xref": "tq edit <id> --xref REF",
    "change-prio": "tq edit <id> -p N",
    "change-type": "tq edit <id> -t TYPE",
    # `update` would difflib-match `create`; map it to edit explicitly
    "update": "tq edit <id> [field-options]",
    "list": "tq ls",
}


class HintingArgumentParser(argparse.ArgumentParser):
    # [AI]
    # Context: variadic-read-commands -- unknown-command hints.
    # Intent: argparse reports a subcommand typo as
    #   "argument command: invalid choice: 'X' ...". Intercept exactly that
    #   shape and append a hint: the canonical invocation from _REDIRECT_HINTS,
    #   else a difflib closest-match over the registered commands. Option-level
    #   invalid choices produce "argument -t/--type: ..." and fall through to
    #   the stock error. Only the root parser uses this class (subparsers are
    #   stock ArgumentParser via parser_class in build_parser). Exit code stays
    #   2, so a hinted unknown command is still a hard rejection.
    def error(self, message: str) -> T.NoReturn:
        match = re.match(r"argument command: invalid choice: '([^']+)'", message)
        if match is not None:
            wrong = match.group(1)
            hint = self._command_hint(wrong)
            if hint is not None:
                self.print_usage(sys.stderr)
                sys.stderr.write(
                    f"{self.prog}: error: unknown command '{wrong}'; {hint}\n"
                )
                self.exit(2)
        super().error(message)

    def _command_hint(self, wrong: str) -> str | None:
        canonical = _REDIRECT_HINTS.get(wrong)
        if canonical is not None:
            return f"use: {canonical}"
        commands: list[str] = []
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                commands = list(action.choices)
                break
        matches = difflib.get_close_matches(wrong, commands, n=1, cutoff=0.6)
        if matches:
            return f"did you mean '{matches[0]}'?"
        return None


class SectionedHelpAction(argparse._HelpAction):
    # [AI] Override the default help action to print the static help text.
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | T.Sequence[str] | None,
        option_string: str | None = None,
    ) -> T.NoReturn:
        sys.stdout.write(HELP_TEXT)
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    parser = HintingArgumentParser(
        prog="tq",
        description="tq - a minimal ticket system for AI agents that need to track tasks",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action=SectionedHelpAction,
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"tq (tiquette) {__version__}",
        help="Show version and exit",
    )
    # [AI]
    # Context: monorepo-store-targeting -- ticket-store requirement=store-targeting-with-dir
    # Intent: global option, declared before add_subparsers so it lands on the
    #   shared namespace (args.dir) for every command. Must precede the command
    #   word: `tq --dir packages/api ls`. Targets <path>/.tickets, overriding
    #   TICKETS_DIR and walk-up.
    parser.add_argument(
        "--dir",
        dest="dir",
        metavar="PATH",
        default=None,
        help="Operate on the store at PATH/.tickets (overrides TICKETS_DIR and walk-up)",
    )

    # [AI] parser_class pins subparsers to the stock ArgumentParser: the
    # register() signatures expect _SubParsersAction[ArgumentParser], and only
    # the root parser needs the unknown-command hint override.
    subparsers = parser.add_subparsers(
        dest="command", parser_class=argparse.ArgumentParser
    )

    # [AI]
    # Context: cli-redesign-v1.2
    # Intent: only the post-v1.2 command groups are registered. The per-field
    #   verbs (tag, untag, dep, undep, nest, unnest, link, unlink, assign,
    #   change-prio, change-type, describe, add-note, xref) are gone; their
    #   behavior moved into `edit`.
    lifecycle.register(subparsers)
    edit.register(subparsers)
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
    except TicketParseError as exc:
        # [AI]
        # Context: tiqt-280e -- malformed/legacy frontmatter should produce a
        #   clean diagnostic, not a Python traceback. The most common case is
        #   a legacy `status: completed` value, which `tq autofix` migrates.
        sys.stderr.write(f"error: {exc}\n")
        if "invalid status 'completed'" in str(exc):
            sys.stderr.write("hint: run `tq autofix` to migrate legacy statuses\n")
        sys.exit(1)

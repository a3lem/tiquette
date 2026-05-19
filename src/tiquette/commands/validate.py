from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tiquette.store import find_tickets_dir, load_all_tickets


# [AI]
# Context: add-ticket-validate change, ticket-validate capability
# Intent: scan non-archived tickets for dangling deps, parent, and links references

Problem = tuple[str, str, str]  # (ticket_id, level, message)


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    p = subparsers.add_parser(
        "validate", help="Check tickets for referential integrity"
    )
    p.set_defaults(func=_handle_validate)


def _collect_problems(tickets_dir: Path) -> list[Problem]:
    active = load_all_tickets(tickets_dir, source="active")
    archived = load_all_tickets(tickets_dir, source="archived")
    all_tickets = {**archived, **active}  # active wins on collision
    active_ids = set(active.keys())
    archived_ids = set(archived.keys()) - active_ids

    problems: list[Problem] = []

    for ticket_id in sorted(active_ids):
        ticket = all_tickets[ticket_id]

        for dep_id in ticket.deps:
            if dep_id in active_ids:
                continue
            if dep_id in archived_ids:
                problems.append(
                    (ticket_id, "warning", f'depends on archived ticket "{dep_id}"')
                )
            else:
                problems.append(
                    (ticket_id, "error", f'depends on non-existent ticket "{dep_id}"')
                )

        if ticket.parent is not None:
            if ticket.parent not in active_ids:
                if ticket.parent in archived_ids:
                    problems.append(
                        (ticket_id, "warning", f'has archived parent "{ticket.parent}"')
                    )
                else:
                    problems.append(
                        (
                            ticket_id,
                            "error",
                            f'has non-existent parent "{ticket.parent}"',
                        )
                    )

        for link_id in ticket.links:
            if link_id in active_ids:
                continue
            if link_id in archived_ids:
                problems.append(
                    (ticket_id, "warning", f'links to archived ticket "{link_id}"')
                )
            else:
                problems.append(
                    (ticket_id, "error", f'links to non-existent ticket "{link_id}"')
                )

    problems.sort(key=lambda p: (p[0], p[1] == "warning"))
    return problems


def _format_summary(errors: int, warnings: int) -> str:
    if errors == 0 and warnings == 0:
        return "all tickets valid"
    e_label = "error" if errors == 1 else "errors"
    w_label = "warning" if warnings == 1 else "warnings"
    return f"{errors} {e_label}, {warnings} {w_label}"


def _handle_validate(args: argparse.Namespace) -> None:
    tickets_dir = find_tickets_dir()
    problems = _collect_problems(tickets_dir)

    errors = 0
    warnings = 0

    for ticket_id, level, message in problems:
        sys.stderr.write(f"{ticket_id}: {level}: {message}\n")
        if level == "error":
            errors += 1
        else:
            warnings += 1

    sys.stderr.write(_format_summary(errors, warnings) + "\n")

    if errors > 0:
        sys.exit(1)

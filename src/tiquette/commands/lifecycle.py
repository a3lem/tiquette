from __future__ import annotations

import argparse
import sys
from tiquette.timestamps import now_iso

from tiquette.commands._fields import add_create_flags, namespace_to_field_changes
from tiquette.store import (
    FieldChangeError,
    Status,
    Ticket,
    TicketNotFoundError,
    _append_note,
    apply_field_changes,
    generate_id,
    is_terminal,
    load_all_tickets,
    read_ticket,
    resolve_id_in_dir,
    resolve_store,
    write_ticket,
)


# [AI] Status-transition-notes: maps target status to the verb tag that
# prefixes any --note written by a transition. Keyed on target Status because
# that's what _handle_status already has via args.target_status.
_TRANSITION_TAG: dict[Status, str] = {
    Status.IN_PROGRESS: "started",
    Status.CLOSED: "closed",
    Status.CANCELED: "canceled",
    Status.OPEN: "reopened",
}


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    # [AI]
    # Context: cli-redesign-v1.2 -- ticket-lifecycle requirement=create-ticket
    # Intent: title is required positional. Field-flags come from the shared
    #   _fields schema so `create` and `edit` stay in lockstep.
    p_create = subparsers.add_parser("create", help="Create ticket, prints ID")
    p_create.add_argument("title", help="Ticket title")
    add_create_flags(p_create)
    p_create.set_defaults(func=_handle_create)

    # [AI] Context: lifecycle-multi-id -- ticket-lifecycle requirements=start/close/cancel/reopen
    # Intent: each transition subparser takes one or more IDs (nargs="+"); the
    #   shared _handle_status validates them all up front before mutating, so a
    #   batch that names an unknown or descendant-blocked ticket leaves the store
    #   untouched. close/cancel still gain -f/--force to cascade open descendants.
    #   Each subparser carries its target Status in set_defaults so _handle_status
    #   dispatches on the Status enum, not on the subcommand name.
    for name, helptext, target in [
        (
            "start",
            "Set status to in_progress (rejects if already in_progress)",
            Status.IN_PROGRESS,
        ),
        ("close", "Set status to closed (rejects if already closed)", Status.CLOSED),
        (
            "cancel",
            "Set status to canceled (rejects if already canceled)",
            Status.CANCELED,
        ),
        ("reopen", "Set status to open (rejects if already open)", Status.OPEN),
    ]:
        p = subparsers.add_parser(name, help=helptext)
        p.add_argument("id", nargs="+", help="Ticket ID(s)")
        if name in ("close", "cancel"):
            p.add_argument(
                "-f",
                "--force",
                action="store_true",
                help="Force closure; cascade to open descendants",
            )
        # [AI] status-transition-notes: repeatable --note attaches a tagged
        # entry (verb-prefixed) to every ticket whose status this invocation
        # actually changes. No short flag; consistent with create/edit.
        p.add_argument(
            "--note",
            action="append",
            default=[],
            metavar="TEXT",
            help="Append a tagged note to every ticket changed by this command",
        )
        p.set_defaults(func=_handle_status, target_status=target)


# [AI]
# Context: cli-redesign-v1.2 -- ticket-lifecycle requirement=create-ticket
# Intent: create a fresh ticket then route through the shared
#   apply_field_changes pipeline. The note timestamp is the same UTC
#   instant as the ticket's `created` field (one clock read per call).
def _handle_create(args: argparse.Namespace) -> None:
    # [AI]
    # Context: monorepo-store-targeting -- ticket-store requirement=store-targeting-with-dir
    # Intent: --dir initialises <path>/.tickets; without it, an existing store
    #   (env/walk-up) is preferred, else a fresh .tickets in cwd. must_exist=False
    #   folds the old catch-TicketsNotFoundError-then-mkdir logic into the resolver.
    tickets_dir = resolve_store(args.dir, must_exist=False)
    tickets_dir.mkdir(parents=True, exist_ok=True)

    now = now_iso()
    ticket_id = generate_id(tickets_dir)
    ticket = Ticket(id=ticket_id, title=args.title, created=now)

    changes = namespace_to_field_changes(args, edit_mode=False)
    # Defaults: only apply when the user didn't pass the flag.
    if changes.type is None:
        changes.type = "task"
    if changes.priority is None:
        changes.priority = 2

    try:
        extra = apply_field_changes(ticket, changes, tickets_dir, note_timestamp=now)
    except FieldChangeError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    for other in extra:
        write_ticket(other, tickets_dir)
    write_ticket(ticket, tickets_dir)
    sys.stdout.write(ticket_id + "\n")


# [AI]
# Context: ticket-lifecycle requirements for start/close/cancel/reopen
# Intent: collect all open descendants by walking parent→child tree recursively;
#   returns a dict so callers can reuse the loaded Ticket objects for mutation.
def _find_open_descendants(
    ticket_id: str,
    all_tickets: dict[str, Ticket],
) -> dict[str, Ticket]:
    children_of: dict[str, list[Ticket]] = {}
    for t in all_tickets.values():
        if t.parent:
            children_of.setdefault(t.parent, []).append(t)

    open_descendants: dict[str, Ticket] = {}

    def _walk(parent_id: str) -> None:
        for child in children_of.get(parent_id, []):
            if not is_terminal(child.status):
                open_descendants[child.id] = child
            _walk(child.id)

    _walk(ticket_id)
    return open_descendants


# [AI]
# Context: ticket-lifecycle requirement=close-command scenario=close-notifies-last-open-child
# Intent: notify when closing a child leaves its parent with no open children
def _check_last_open_child(
    ticket: Ticket,
    all_tickets: dict[str, Ticket],
) -> None:
    if not ticket.parent:
        return

    for sibling in all_tickets.values():
        if sibling.id == ticket.id:
            continue
        if sibling.parent == ticket.parent and not is_terminal(sibling.status):
            return

    sys.stdout.write(f"note: {ticket.parent} has no remaining open children\n")


# [AI] Context: lifecycle-multi-id -- ticket-lifecycle requirements=start/close/cancel/reopen,invalid-operations,transition-output
# Intent: apply one target status to every supplied ID atomically. Three phases:
#   (1) resolve+load all IDs (dedup, first-seen order) -- any unknown ID aborts
#       before a single write; (2) for terminal targets without --force, reject if
#       ANY target has open descendants (per-target, independent check) -- abort
#       before writing; (3) mutate + emit. This extends the existing single-ticket
#       "leave it re-runnable on partial failure" guarantee to the whole batch.
def _handle_status(args: argparse.Namespace) -> None:
    tickets_dir = resolve_store(args.dir)
    target: Status = args.target_status

    # [AI] status-transition-notes: one timestamp per invocation, shared across
    # every note appended to every affected ticket. Computed once up front but
    # only used if --note was supplied; otherwise notes is empty and we write
    # nothing to Notes.
    notes: list[str] = list(getattr(args, "note", None) or [])
    note_tag = _TRANSITION_TAG[target]
    note_ts = now_iso() if notes else None

    def _attach_notes(ticket: Ticket) -> None:
        for note in notes:
            assert note_ts is not None
            _append_note(ticket, note, note_ts, tag=note_tag)

    # Phase 1: resolve + load every ID before mutating anything.
    # Dedup on resolved ID, preserving first-seen order, so a ticket named twice
    # is processed once.
    targets: list[Ticket] = []
    seen: set[str] = set()
    try:
        for raw_id in args.id:
            ticket_id = resolve_id_in_dir(raw_id, tickets_dir)
            if ticket_id in seen:
                continue
            seen.add(ticket_id)
            targets.append(read_ticket(ticket_id, tickets_dir))
    except TicketNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        sys.exit(1)

    # [AI] Reject idempotent transitions (any target already at the requested
    # status). Pre-flight all targets so a single already-at-status ticket
    # aborts the whole batch before any write, matching the atomic semantics
    # of the unknown-ID and open-descendants checks.
    already: list[Ticket] = [t for t in targets if t.status == target]
    if already:
        for t in already:
            sys.stderr.write(f"error: {t.id} is already {target.value}\n")
        sys.exit(1)

    if not is_terminal(target):
        for ticket in targets:
            ticket.status = target
            _attach_notes(ticket)
            write_ticket(ticket, tickets_dir)
            # [AI] Context: transition-output -- print after write so output only
            #   appears for committed changes (failures sys.exit before this line).
            sys.stdout.write(ticket.id + "\n")
        return

    # Terminal target (closed/canceled): no resolution field is written.
    all_tickets = load_all_tickets(tickets_dir)

    # Phase 2: per-target descendant pre-flight. Without --force, a target with
    # open descendants is rejected; if any target is rejected the whole run aborts
    # before writing.
    open_desc_by_target: dict[str, dict[str, Ticket]] = {
        t.id: _find_open_descendants(t.id, all_tickets) for t in targets
    }
    if not args.force:
        blocked = [t for t in targets if open_desc_by_target[t.id]]
        if blocked:
            for t in blocked:
                desc_list = ", ".join(sorted(open_desc_by_target[t.id]))
                sys.stderr.write(f"error: {t.id} has open descendants: {desc_list}\n")
            sys.exit(1)

    # Phase 3: mutate + emit. Cascade each target's open descendants first so a
    # partial failure leaves the parent open (re-runnable). The written set keeps
    # a ticket that is both a descendant of one target and an explicit target from
    # being written twice.
    written: set[str] = set()
    closed_targets: list[Ticket] = []
    for ticket in targets:
        for desc in open_desc_by_target[ticket.id].values():
            if desc.id in written:
                continue
            desc.status = target
            _attach_notes(desc)
            write_ticket(desc, tickets_dir)
            written.add(desc.id)
            all_tickets[desc.id] = desc
            sys.stdout.write(desc.id + "\n")
        if ticket.id in written:
            continue
        ticket.status = target
        _attach_notes(ticket)
        write_ticket(ticket, tickets_dir)
        written.add(ticket.id)
        all_tickets[ticket.id] = ticket
        sys.stdout.write(ticket.id + "\n")
        if target is Status.CLOSED:
            closed_targets.append(ticket)

    # Notify after all writes so each check sees the final sibling statuses.
    for ticket in closed_targets:
        _check_last_open_child(ticket, all_tickets)

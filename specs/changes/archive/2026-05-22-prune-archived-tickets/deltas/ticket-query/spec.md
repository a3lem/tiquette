# Ticket Query

## ADDED Requirements

### Requirement: Prune command

The system SHALL permanently delete archived tickets matching the supplied filters when `tq prune` is invoked. Prune SHALL operate only on `.tickets/archive/`; it SHALL NOT consider or modify active tickets.

At least one filter SHALL be supplied. IF no filter (`--status`, `--type`, `--before`) is given, the system SHALL exit non-zero with a usage error and delete nothing.

Filters combine with logical AND. The available filters are:
- `--status` (short: `-s`) accepts one of `closed` or `canceled`.
- `--type` (short: `-t`) accepts one of `bug`, `feature`, `task`, `epic`, `chore`.
- `--before` accepts a `YYYY-MM-DD` date and matches archived tickets whose `created` timestamp is strictly before midnight (00:00) of that date. IF the value is not a valid `YYYY-MM-DD` date, the system SHALL exit non-zero with a usage error and delete nothing.

By default the command performs a dry run: it SHALL print every archived ticket that matches the filters, SHALL print a summary line stating the count of tickets that would be deleted and that `-y` is required to delete them, and SHALL delete nothing. WHEN `-y` / `--yes` is supplied, the system SHALL delete the matching ticket files from `.tickets/archive/`.

Prune SHALL NOT perform referential-integrity checks. Deleting an archived ticket still referenced by an active ticket's `deps`, `links`, or `parent` is permitted and leaves a dangling reference; detecting and repairing such references is the responsibility of `tq validate` / `tq autofix`.

#### Scenario: Prune deletes matching canceled tickets with confirmation
- Given archived tickets "arc-001" (status `canceled`) and "arc-002" (status `closed`)
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

#### Scenario: Dry run by default deletes nothing
- Given an archived ticket "arc-001" with status `canceled`
- When the user runs `tq prune --status canceled`
- Then the command exits 0
- And stdout contains "arc-001"
- And stdout contains a summary line reporting "1" ticket would be deleted
- And stdout indicates `-y` is required to delete
- And "arc-001" still exists in `.tickets/archive/`

#### Scenario: Bare prune is rejected
- Given an archived ticket "arc-001" exists
- When the user runs `tq prune`
- Then the command exits non-zero
- And stderr indicates at least one filter is required
- And "arc-001" still exists in `.tickets/archive/`

#### Scenario: Filters combine with AND
- Given archived ticket "arc-001" (status `canceled`, type `bug`)
- And archived ticket "arc-002" (status `canceled`, type `task`)
- When the user runs `tq prune --status canceled --type bug -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

#### Scenario: Before filters on created date
- Given archived ticket "arc-001" created "2025-06-01T10:00:00"
- And archived ticket "arc-002" created "2026-03-01T10:00:00"
- When the user runs `tq prune --before 2026-01-01 -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

#### Scenario: Prune ignores active tickets
- Given an active ticket "act-001" with status `canceled`
- And no archive directory exists
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And "act-001" still exists as an active ticket

#### Scenario: No matches reports nothing pruned
- Given an archived ticket "arc-001" with status `closed`
- When the user runs `tq prune --status canceled -y`
- Then the command exits 0
- And stdout indicates no tickets matched

#### Scenario: Prune rejects invalid status
- When the user runs `tq prune --status open`
- Then the command exits non-zero

#### Scenario: Prune rejects invalid type
- When the user runs `tq prune --type invalid`
- Then the command exits non-zero

#### Scenario: Prune rejects invalid before date
- When the user runs `tq prune --before not-a-date`
- Then the command exits non-zero

#### Scenario: Prune accepts short flags
- Given archived ticket "arc-001" (status `canceled`, type `bug`)
- And archived ticket "arc-002" (status `closed`, type `task`)
- When the user runs `tq prune -s canceled -t bug -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`
- And "arc-002" still exists in `.tickets/archive/`

#### Scenario: Prune allows deleting a ticket still referenced by an active ticket
- Given an active ticket "act-001" with a dep on "arc-001"
- And an archived ticket "arc-001" with status `closed`
- When the user runs `tq prune --status closed -y`
- Then the command exits 0
- And "arc-001" no longer exists in `.tickets/archive/`

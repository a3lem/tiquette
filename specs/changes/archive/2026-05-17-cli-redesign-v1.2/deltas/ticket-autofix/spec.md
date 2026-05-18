# Ticket Autofix

## ADDED Requirements

### Requirement: Migrate completed status to closed

WHEN a ticket has `status: completed`, `tq autofix` SHALL rewrite the status to `closed`. The migration SHALL apply unconditionally; no flag, no opt-in. The migration SHALL apply to active tickets and to tickets in `.tickets/archive/`. Each run SHALL print a single summary line `- Migrated N tickets from completed status` where N is the count of tickets whose status was rewritten. WHEN no tickets carry `status: completed`, the line SHALL NOT be printed.

#### Scenario: Active completed ticket migrated
- Given ticket "t-001" has `status: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: closed`
- And stdout contains "- Migrated 1 ticket from completed status"

#### Scenario: Archived completed ticket migrated
- Given an archived ticket "arc-001" has `status: completed`
- When the user runs `tq autofix`
- Then the archived ticket has `status: closed`

#### Scenario: Multiple tickets migrated
- Given tickets "t-001", "t-002", "t-003" all have `status: completed`
- When the user runs `tq autofix`
- Then all three tickets have `status: closed`
- And stdout contains "- Migrated 3 tickets from completed status"

#### Scenario: No completed tickets is a no-op
- Given no ticket has `status: completed`
- When the user runs `tq autofix`
- Then stdout does not contain "Migrated" and "from completed status"

#### Scenario: Idempotent
- Given ticket "t-001" has `status: completed`
- When the user runs `tq autofix` twice
- Then ticket "t-001" has `status: closed`
- And the second run does not migrate any tickets

## REMOVED Requirements

### Requirement: Migrate legacy closed status

**Reason**: This requirement was added by the earlier
`split-closed-status` change to migrate `status: closed` (with a
`resolution` field) into `status: completed` / `status: canceled`. v1.2
reverses that direction — `closed` is once again the terminal status
for shipped work — so the legacy migration is now ambiguous and would
incorrectly rewrite v1.2 `closed` tickets back into `completed`.
**Migration**: Any ticket store that still carries pre-`split-closed-
status` data (status `closed` with a `resolution` field) must run
`tq autofix` on the last release before v1.2 before upgrading.
Forward-only — v1.2's `autofix` does not handle the
`closed + resolution` case.

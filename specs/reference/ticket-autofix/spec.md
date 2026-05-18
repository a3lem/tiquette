# Ticket Autofix

Covers the `tq autofix` maintenance command, which updates ticket files so they remain consistent with current behavior.

## Requirement: Autofix command

The system SHALL provide a `tq autofix` command that scans tickets, applies safe corrections, and prints a list of fixes that were applied. Each fix entry SHALL be printed on its own line, prefixed with "- ". When no fixes are needed, the command SHALL print "No fixes needed".

### Scenario: No-op when everything is consistent
- Given all tickets already match current expected state
- When the user runs `tq autofix`
- Then stdout contains "No fixes needed"

## Requirement: Stale ID prefix renames

When the project's expected ID prefix (per the `ticket-store` ID-generation rule) does not match a ticket's current prefix, `tq autofix` SHALL rename that ticket to use the expected prefix while preserving the original 4-hex suffix when free, and regenerating the suffix on collision.

The rename SHALL be propagated into every other ticket's `parent`, `deps`, and `links` fields so that no ticket becomes orphaned. Tickets in the `archive/` subdirectory SHALL be processed as well.

### Scenario: Stale prefix renamed and references propagated
- Given a ticket "tiquette-aaaa" exists, and another ticket "tiquette-bbbb" has parent "tiquette-aaaa", deps `[tiquette-aaaa]`, and links `[tiquette-aaaa]`
- And the project directory's expected prefix is "tiqt"
- When the user runs `tq autofix`
- Then the file `tiqt-aaaa.md` exists and `tiquette-aaaa.md` does not
- And the file `tiqt-bbbb.md` exists and `tiquette-bbbb.md` does not
- And the ticket "tiqt-bbbb" has parent "tiqt-aaaa", deps `[tiqt-aaaa]`, links `[tiqt-aaaa]`
- And stdout contains "- Renamed 2 tickets to current ID prefix"

### Scenario: Suffix regenerated on collision
- Given "tiqt-dead" already exists and "tiquette-dead" has a stale prefix
- When the user runs `tq autofix`
- Then "tiqt-dead" is unchanged
- And "tiquette-dead" is renamed to a new ID with prefix "tiqt-" and a freshly generated suffix

### Scenario: Archived tickets are renamed too
- Given an archived ticket "tiquette-a1c1" and an active ticket linking to it
- When the user runs `tq autofix`
- Then the archive contains "tiqt-a1c1.md"
- And the active ticket's links field references "tiqt-a1c1"

## Requirement: Migrate completed status to closed

WHEN a ticket has `status: completed`, `tq autofix` SHALL rewrite the status to `closed`. The migration SHALL apply unconditionally; no flag, no opt-in. The migration SHALL apply to active tickets and to tickets in `.tickets/archive/`. Each run SHALL print a single summary line `- Migrated N tickets from completed status` where N is the count of tickets whose status was rewritten. WHEN no tickets carry `status: completed`, the line SHALL NOT be printed.

### Scenario: Active completed ticket migrated
- Given ticket "t-001" has `status: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: closed`
- And stdout contains "- Migrated 1 ticket from completed status"

### Scenario: Archived completed ticket migrated
- Given an archived ticket "arc-001" has `status: completed`
- When the user runs `tq autofix`
- Then the archived ticket has `status: closed`

### Scenario: Multiple tickets migrated
- Given tickets "t-001", "t-002", "t-003" all have `status: completed`
- When the user runs `tq autofix`
- Then all three tickets have `status: closed`
- And stdout contains "- Migrated 3 tickets from completed status"

### Scenario: No completed tickets is a no-op
- Given no ticket has `status: completed`
- When the user runs `tq autofix`
- Then stdout does not contain "Migrated" and "from completed status"

### Scenario: Idempotent
- Given ticket "t-001" has `status: completed`
- When the user runs `tq autofix` twice
- Then ticket "t-001" has `status: closed`
- And the second run does not migrate any tickets

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

## Requirement: Migrate legacy closed status

WHEN a ticket has `status: closed`, `tq autofix` SHALL rewrite its status using the legacy `resolution` field as a guide and SHALL remove the `resolution` field from the frontmatter:

- IF `resolution` is `completed`, the new status SHALL be `completed`.
- IF `resolution` is `canceled`, the new status SHALL be `canceled`.
- IF the `resolution` field is absent, the new status SHALL be `completed`.

WHEN a ticket carries a `resolution` field but its status is not `closed` (a stray field), `tq autofix` SHALL remove the `resolution` field without changing status.

Migrations SHALL apply to active tickets and to tickets in `.tickets/archive/`. Each run SHALL print a single summary line `- Migrated N tickets from closed status` where N is the count of tickets whose status was rewritten; if N is zero but stray `resolution` fields were stripped, the system SHALL print `- Stripped resolution from N tickets` instead.

### Scenario: Closed + completed resolution → completed
- Given ticket "t-001" has `status: closed` and `resolution: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: completed`
- And ticket "t-001" has no `resolution` field
- And stdout contains "- Migrated 1 ticket from closed status"

### Scenario: Closed + canceled resolution → canceled
- Given ticket "t-001" has `status: closed` and `resolution: canceled`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: canceled`
- And ticket "t-001" has no `resolution` field

### Scenario: Closed without resolution → completed
- Given ticket "t-001" has `status: closed` and no `resolution` field
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: completed`

### Scenario: Stray resolution on non-closed ticket is removed
- Given ticket "t-001" has `status: open` and `resolution: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: open`
- And ticket "t-001" has no `resolution` field
- And stdout contains "- Stripped resolution from 1 ticket"

### Scenario: Archived legacy tickets migrated too
- Given an archived ticket "arc-001" has `status: closed` and `resolution: canceled`
- When the user runs `tq autofix`
- Then the archived ticket has `status: canceled` and no `resolution` field

### Scenario: No legacy data is a no-op
- Given no ticket has `status: closed` or a `resolution` field
- When the user runs `tq autofix`
- Then stdout does not contain "Migrated" or "Stripped resolution"

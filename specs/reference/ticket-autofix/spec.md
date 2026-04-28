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

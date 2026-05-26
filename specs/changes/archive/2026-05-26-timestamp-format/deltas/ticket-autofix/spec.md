# Ticket Autofix

## ADDED Requirements

### Requirement: Normalize legacy timestamps

WHEN a ticket carries a timestamp not in the `YYYY-MM-DDTHH:MMZ` format -- either in its `created` frontmatter field or in any `## Notes` entry -- `tq autofix` SHALL rewrite that timestamp to the new format. The migration SHALL apply unconditionally; no flag, no opt-in. The migration SHALL apply to active tickets and to tickets in `.tickets/archive/`. Each run SHALL print a single summary line `- Normalized N tickets to current timestamp format` where N is the count of tickets whose file content was actually rewritten. WHEN no ticket needed normalising, the line SHALL NOT be printed.

#### Scenario: Active ticket with legacy created timestamp
- Given ticket "t-001" has `created: 2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq autofix`
- Then ticket "t-001" has a `created` field matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`
- And the date and minute components match the original (`2026-04-29T12:48Z`)
- And stdout contains "- Normalized 1 ticket to current timestamp format"

#### Scenario: Archived ticket with legacy created timestamp
- Given an archived ticket "arc-001" has `created: 2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq autofix`
- Then the archived ticket's `created` field matches `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`

#### Scenario: Note timestamp normalized
- Given ticket "t-001" has a `## Notes` entry `- 2026-04-29T12:48:50.906383+00:00: hello`
- When the user runs `tq autofix`
- Then the notes section contains `- 2026-04-29T12:48Z: hello`

#### Scenario: Already-new timestamps are untouched
- Given ticket "t-001" has `created: 2026-05-26T10:00Z` and no legacy note timestamps
- When the user runs `tq autofix`
- Then stdout does not contain "Normalized" and "to current timestamp format"
- And the file on disk is byte-identical to its pre-run state

#### Scenario: Multiple tickets normalized
- Given three tickets, two with legacy `created` timestamps and one with a legacy note timestamp
- When the user runs `tq autofix`
- Then stdout contains "- Normalized 3 tickets to current timestamp format"

#### Scenario: Idempotent
- Given ticket "t-001" has `created: 2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq autofix` twice
- Then ticket "t-001"'s `created` field is in the new format after the first run
- And the second run does not normalize any tickets

# Ticket Autofix

## ADDED Requirements

### Requirement: Migrate legacy closed status

WHEN a ticket has `status: closed`, `tq autofix` SHALL rewrite its status using the legacy `resolution` field as a guide and SHALL remove the `resolution` field from the frontmatter:

- IF `resolution` is `completed`, the new status SHALL be `completed`.
- IF `resolution` is `canceled`, the new status SHALL be `canceled`.
- IF the `resolution` field is absent, the new status SHALL be `completed`.

WHEN a ticket carries a `resolution` field but its status is not `closed` (a stray field), `tq autofix` SHALL remove the `resolution` field without changing status.

Migrations SHALL apply to active tickets and to tickets in `.tickets/archive/`. Each run SHALL print a single summary line `- Migrated N tickets from closed status` where N is the count of tickets whose status was rewritten; if N is zero but stray `resolution` fields were stripped, the system SHALL print `- Stripped resolution from N tickets` instead.

#### Scenario: Closed + completed resolution → completed
- Given ticket "t-001" has `status: closed` and `resolution: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: completed`
- And ticket "t-001" has no `resolution` field
- And stdout contains "- Migrated 1 ticket from closed status"

#### Scenario: Closed + canceled resolution → canceled
- Given ticket "t-001" has `status: closed` and `resolution: canceled`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: canceled`
- And ticket "t-001" has no `resolution` field

#### Scenario: Closed without resolution → completed
- Given ticket "t-001" has `status: closed` and no `resolution` field
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: completed`

#### Scenario: Stray resolution on non-closed ticket is removed
- Given ticket "t-001" has `status: open` and `resolution: completed`
- When the user runs `tq autofix`
- Then ticket "t-001" has `status: open`
- And ticket "t-001" has no `resolution` field
- And stdout contains "- Stripped resolution from 1 ticket"

#### Scenario: Archived legacy tickets migrated too
- Given an archived ticket "arc-001" has `status: closed` and `resolution: canceled`
- When the user runs `tq autofix`
- Then the archived ticket has `status: canceled` and no `resolution` field

#### Scenario: No legacy data is a no-op
- Given no ticket has `status: closed` or a `resolution` field
- When the user runs `tq autofix`
- Then stdout does not contain "Migrated" or "Stripped resolution"

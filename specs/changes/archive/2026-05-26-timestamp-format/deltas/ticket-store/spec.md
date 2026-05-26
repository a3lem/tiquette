# Ticket Store

## ADDED Requirements

### Requirement: Timestamp format

The system SHALL write all ticket timestamps -- the `created` frontmatter field and every Notes-section entry -- in the format `YYYY-MM-DDTHH:MMZ` (minute precision, Zulu suffix). The system SHALL accept on read both this format and the legacy ISO 8601 microsecond-plus-offset format (e.g. `2026-04-29T12:48:50.906383+00:00`). The system SHALL NOT rewrite existing ticket files to migrate their timestamp format.

#### Scenario: New ticket writes new format
- Given a clean tickets directory
- When the user runs `tq create "New ticket"`
- Then the `created` frontmatter value matches the pattern `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`

#### Scenario: New note writes new format
- Given a ticket "t-001" exists
- When the user runs `tq edit t-001 --note "hello"`
- Then the appended Notes entry begins with a timestamp matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`

#### Scenario: Legacy timestamps are read without error
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq show <id>`
- Then the command exits 0
- And the displayed creation time reflects the legacy timestamp

#### Scenario: Legacy ticket is not rewritten on read
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq show <id>`
- Then the file on disk is unchanged

#### Scenario: Editing a legacy ticket preserves its created timestamp
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq edit <id> --priority 1`
- Then the `created` field remains `2026-04-29T12:48:50.906383+00:00`
- And any newly written Notes entries use the new format

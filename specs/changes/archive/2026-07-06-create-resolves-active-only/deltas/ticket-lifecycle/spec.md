# Ticket Lifecycle

## MODIFIED Requirements

### Requirement: Create ticket

The system SHALL create a ticket file in `.tickets/` when `tq create <title>` is invoked, and print the generated ID to stdout. The `<title>` positional SHALL be required; invoking `tq create` with no title SHALL exit non-zero with an argparse usage error. The system SHALL accept the field-options defined by `ticket-edit` plus `--link ID` (repeatable, symmetric) and `--note TEXT` (repeatable, timestamped) on the create surface. Partial IDs passed to `--dep`/`--link`/`--parent` SHALL resolve against active tickets only, per the "ID resolution across commands" requirement in `id-resolution`.

#### Scenario: Create with title
- Given a clean tickets directory
- When the user runs `tq create "My first ticket"`
- Then the command exits 0
- And stdout matches the ticket ID pattern `<prefix>-<4hex>`
- And a ticket file exists with `# My first ticket` as the heading

#### Scenario: Create without title is rejected
- When the user runs `tq create`
- Then the command exits non-zero
- And stderr indicates the title argument is required

#### Scenario: Create with description
- Given a clean tickets directory
- When the user runs `tq create "Test ticket" -d "This is the description"`
- Then the command exits 0
- And the created ticket contains a `## Description` section with "This is the description"

#### Scenario: Create with type
- When the user runs `tq create "Bug ticket" -t bug`
- Then the created ticket has field `type` with value `bug`

#### Scenario: Create with priority
- When the user runs `tq create "High priority" -p 0`
- Then the created ticket has field `priority` with value `0`

#### Scenario: Create with assignee (short flag)
- When the user runs `tq create "Assigned ticket" -A "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

#### Scenario: Create with assignee (long flag)
- When the user runs `tq create "Assigned ticket" --assignee "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

#### Scenario: -a is not accepted for --assignee
- When the user runs `tq create "X" -a "John Doe"`
- Then the command exits non-zero

#### Scenario: Create with external reference
- When the user runs `tq create "External ticket" --xref "JIRA-123"`
- Then the created ticket has field `xref` with value `JIRA-123`

#### Scenario: Create with parent
- Given a ticket exists with ID "parent-001"
- When the user runs `tq create "Child ticket" --parent parent-001`
- Then the created ticket has field `parent` with value `parent-001`

#### Scenario: Create with tags
- When the user runs `tq create "Tagged ticket" --tag ui --tag backend`
- Then the created ticket has tags `[ui, backend]`

#### Scenario: Create with deps
- Given tickets "dep-001" and "dep-002" exist
- When the user runs `tq create "Blocked ticket" --dep dep-001 --dep dep-002`
- Then the created ticket has deps `[dep-001, dep-002]`

#### Scenario: Create with links is symmetric
- Given a ticket "rel-001" exists with no links
- When the user runs `tq create "Related ticket" --link rel-001`
- Then the created ticket lists "rel-001" in links
- And ticket "rel-001" lists the new ticket's id in links

#### Scenario: Create with note
- When the user runs `tq create "Kickoff ticket" --note "initial context"`
- Then the created ticket contains a `## Notes` section
- And the note "initial context" appears with a timestamp in the format defined by `ticket-store` matching the ticket's `created` timestamp

#### Scenario: Create with multiple notes shares one timestamp
- When the user runs `tq create "Multi-note" --note "first" --note "second"`
- Then both notes appear in `## Notes` in order
- And both notes carry the same timestamp in the format defined by `ticket-store`

#### Scenario: Create rejects invalid type
- When the user runs `tq create "Test" -t invalid`
- Then the command exits non-zero

#### Scenario: Create rejects invalid priority
- When the user runs `tq create "Test" -p 5`
- Then the command exits non-zero

#### Scenario: Create rejects negative priority
- When the user runs `tq create "Test" -p -1`
- Then the command exits non-zero

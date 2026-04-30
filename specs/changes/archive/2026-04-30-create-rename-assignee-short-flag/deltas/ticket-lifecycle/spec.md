# Ticket Lifecycle

## MODIFIED Requirements

### Requirement: Create ticket

The system SHALL create a ticket file in `.tickets/` when `tq create` is invoked, and print the generated ID to stdout.

#### Scenario: Create with title
- Given a clean tickets directory
- When the user runs `tq create "My first ticket"`
- Then the command exits 0
- And stdout matches the ticket ID pattern `<prefix>-<4hex>`
- And a ticket file exists with `# My first ticket` as the heading

#### Scenario: Create with default title
- Given a clean tickets directory
- When the user runs `tq create`
- Then the command exits 0
- And the created ticket has title "Untitled"

#### Scenario: Create with description
- Given a clean tickets directory
- When the user runs `tq create "Test ticket" -d "This is the description"`
- Then the command exits 0
- And the created ticket contains a `## Description` section with "This is the description"

#### Scenario: Create with type
- Given a clean tickets directory
- When the user runs `tq create "Bug ticket" -t bug`
- Then the created ticket has field `type` with value `bug`

#### Scenario: Create with priority
- Given a clean tickets directory
- When the user runs `tq create "High priority" -p 0`
- Then the created ticket has field `priority` with value `0`

#### Scenario: Create with assignee (short flag)
- Given a clean tickets directory
- When the user runs `tq create "Assigned ticket" -A "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

#### Scenario: Create with assignee (long flag)
- Given a clean tickets directory
- When the user runs `tq create "Assigned ticket" --assignee "John Doe"`
- Then the created ticket has field `assignee` with value `John Doe`

#### Scenario: -a is no longer accepted for --assignee
- When the user runs `tq create "X" -a "John Doe"`
- Then the command exits non-zero

#### Scenario: Create with external reference
- Given a clean tickets directory
- When the user runs `tq create "External ticket" --xref "JIRA-123"`
- Then the created ticket has field `xref` with value `JIRA-123`

#### Scenario: Create with parent
- Given a ticket exists with ID "parent-001"
- When the user runs `tq create "Child ticket" --parent parent-001`
- Then the created ticket has field `parent` with value `parent-001`

#### Scenario: Create with tags
- Given a clean tickets directory
- When the user runs `tq create "Tagged ticket" --tag ui --tag backend`
- Then the created ticket has tags `[ui, backend]`

#### Scenario: Create with deps
- Given tickets "dep-001" and "dep-002" exist
- When the user runs `tq create "Blocked ticket" --dep dep-001 --dep dep-002`
- Then the created ticket has deps `[dep-001, dep-002]`

#### Scenario: Create rejects invalid type
- When the user runs `tq create "Test" -t invalid`
- Then the command exits non-zero

#### Scenario: Create rejects invalid priority
- When the user runs `tq create "Test" -p 5`
- Then the command exits non-zero

#### Scenario: Create rejects negative priority
- When the user runs `tq create "Test" -p -1`
- Then the command exits non-zero

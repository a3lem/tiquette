# Ticket Query

## MODIFIED Requirements

### Requirement: Show ticket

The system SHALL display a ticket's full content (frontmatter + body) when `tq show <id>` is invoked, whether the ticket is active or archived.

#### Scenario: Show displays ticket content
- Given ticket "show-001" exists with title "Test ticket"
- When the user runs `tq show show-001`
- Then the command exits 0
- And the output contains "id: show-001"
- And the output contains "# Test ticket"

#### Scenario: Show displays all frontmatter fields
- Given ticket "show-001" exists
- When the user runs `tq show show-001`
- Then the output contains `status:`, `deps:`, `links:`, `type:`, `priority:`

#### Scenario: Show displays blockers section
- Given ticket "show-001" depends on "show-002" (status open)
- When the user runs `tq show show-001`
- Then the output contains "## Blockers"
- And the output contains "show-002 [open]"

#### Scenario: Show hides blockers when all deps are in terminal status
- Given ticket "show-001" depends on "show-002" (status closed)
- When the user runs `tq show show-001`
- Then the output does not contain "## Blockers"

#### Scenario: Show displays blocking section (reverse deps)
- Given ticket "show-002" depends on "show-001"
- When the user runs `tq show show-001`
- Then the output contains "## Blocking"
- And the output contains "show-002"

#### Scenario: Show displays children section
- Given ticket "show-002" has parent "show-001"
- When the user runs `tq show show-001`
- Then the output contains "## Children"
- And the output contains "show-002"

#### Scenario: Show displays linked section
- Given ticket "show-001" is linked to "show-002"
- When the user runs `tq show show-001`
- Then the output contains "## Linked"
- And the output contains "show-002"

#### Scenario: Show non-existent ticket
- When the user runs `tq show nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Show with partial ID
- Given ticket "show-001" exists
- When the user runs `tq show 001`
- Then the command exits 0
- And the output contains "id: show-001"

#### Scenario: Show as JSON
- Given ticket "show-001" exists
- When the user runs `tq show show-001 --json`
- Then the command exits 0
- And the output is valid JSON
- And the JSON contains fields: id, status, type, priority, title, body

#### Scenario: Show displays an archived ticket
- Given ticket "show-010" is closed and archived
- When the user runs `tq show show-010`
- Then the command exits 0
- And the output contains "id: show-010"

#### Scenario: Show resolves an archived ticket by partial ID
- Given ticket "show-011" is closed and archived
- When the user runs `tq show 011`
- Then the command exits 0
- And the output contains "id: show-011"

#### Scenario: Show renders an archived ticket's reverse dependency
- Given ticket "show-012" depends on "show-013"
- And "show-012" and "show-013" are closed and archived together
- When the user runs `tq show show-013`
- Then the command exits 0
- And the output contains "## Blocking"
- And the output contains "show-012"

### Requirement: Info command

The system SHALL display a ticket's frontmatter and computed relationships (without body content) when `tq info <id>` is invoked, whether the ticket is active or archived.

#### Scenario: Info displays frontmatter and relationships
- Given ticket "info-001" exists with title "Test ticket"
- And ticket "info-002" depends on "info-001"
- When the user runs `tq info info-001`
- Then the command exits 0
- And the output contains "id: info-001"
- And the output contains "## Blocking"
- And the output does not contain `## Description`

#### Scenario: Info as JSON
- Given ticket "info-001" exists
- When the user runs `tq info info-001 --json`
- Then the command exits 0
- And the output is valid JSON
- And the JSON contains computed relationship fields

#### Scenario: Info non-existent ticket
- When the user runs `tq info nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Info displays an archived ticket
- Given ticket "info-010" is closed and archived
- When the user runs `tq info info-010`
- Then the command exits 0
- And the output contains "id: info-010"

### Requirement: Path command

The system SHALL print the file path of a ticket when `tq path <id>` is invoked, whether the ticket is active or archived.

#### Scenario: Path prints file location
- Given ticket "test-001" exists
- When the user runs `tq path test-001`
- Then the output contains ".tickets/test-001.md"

#### Scenario: Path prints archive file location
- Given ticket "test-010" is closed and archived
- When the user runs `tq path test-010`
- Then the output contains ".tickets/archive/test-010.md"

### Requirement: Show dependency tree

The system SHALL display a transitive dependency tree when `tq deps <id>` is invoked. The root and any transitive dependency may be active or archived.

#### Scenario: Dependency tree shows transitive deps
- Given "task-0001" depends on "task-0002", which depends on "task-0003"
- When the user runs `tq deps task-0001`
- Then the output contains all three IDs with status and title
- And the output uses box-drawing characters

#### Scenario: Dependency tree with multiple children
- Given "task-0001" depends on both "task-0002" and "task-0003"
- When the user runs `tq deps task-0001`
- Then the output contains both dependencies

#### Scenario: Full tree disables deduplication
- Given a diamond dependency pattern
- When the user runs `tq deps --full task-0001`
- Then shared dependencies appear multiple times

#### Scenario: Children sorted by subtree depth then ID
- Given dependencies with varying subtree depths
- When the user runs `tq deps task-0001`
- Then children are sorted by subtree depth ascending, then by ID

#### Scenario: Dependency tree rooted at an archived ticket
- Given "task-0010" depends on "task-0011"
- And "task-0010" and "task-0011" are closed and archived
- When the user runs `tq deps task-0010`
- Then the output contains both "task-0010" and "task-0011" with status and title

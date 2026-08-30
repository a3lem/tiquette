# Ticket Query

## MODIFIED Requirements

### Requirement: Show ticket

The system SHALL display full content (frontmatter + body) for every ticket ID supplied when `tq show <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be displayed once, in first-seen order. WHEN `--json` is supplied with a single ID, the output SHALL be one JSON object (unchanged shape). WHEN `--json` is supplied with multiple IDs, the output SHALL be one JSON array of those objects, in display order.

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

#### Scenario: Show multiple tickets
- Given tickets "show-001" and "show-002" exist
- When the user runs `tq show show-001 show-002`
- Then the command exits 0
- And the output contains "id: show-001"
- And the output contains "id: show-002"

#### Scenario: Show multiple tickets with one unknown prints nothing
- Given ticket "show-001" exists
- When the user runs `tq show show-001 nonexistent`
- Then the command exits non-zero
- And stdout is empty
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Show multiple tickets as JSON emits an array
- Given tickets "show-001" and "show-002" exist
- When the user runs `tq show show-001 show-002 --json`
- Then the command exits 0
- And the output is one valid JSON array with two objects
- And the objects cover "show-001" and "show-002" in argument order

#### Scenario: Show deduplicates repeated IDs
- Given ticket "show-001" exists
- When the user runs `tq show show-001 show-001`
- Then the command exits 0
- And the output contains "id: show-001" exactly once

### Requirement: Info command

The system SHALL display frontmatter and computed relationships (without body content) for every ticket ID supplied when `tq info <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be displayed once, in first-seen order. WHEN `--json` is supplied with a single ID, the output SHALL be one JSON object (unchanged shape). WHEN `--json` is supplied with multiple IDs, the output SHALL be one JSON array of those objects, in display order.

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

#### Scenario: Info multiple tickets
- Given tickets "info-001" and "info-002" exist
- When the user runs `tq info info-001 info-002`
- Then the command exits 0
- And the output contains "id: info-001"
- And the output contains "id: info-002"

#### Scenario: Info multiple tickets as JSON emits an array
- Given tickets "info-001" and "info-002" exist
- When the user runs `tq info info-001 info-002 --json`
- Then the command exits 0
- And the output is one valid JSON array with two objects

### Requirement: Path command

The system SHALL print the file path of every ticket ID supplied, one per line in argument order, when `tq path <id>...` is invoked, whether each ticket is active or archived. At least one ID SHALL be required. The system SHALL resolve all supplied IDs before printing anything; IF any ID is unknown or ambiguous, the system SHALL exit non-zero and print nothing to stdout. IDs that resolve to the same ticket SHALL be printed once, in first-seen order.

#### Scenario: Path prints file location
- Given ticket "test-001" exists
- When the user runs `tq path test-001`
- Then the output contains ".tickets/test-001.md"

#### Scenario: Path prints archive file location
- Given ticket "test-010" is closed and archived
- When the user runs `tq path test-010`
- Then the output contains ".tickets/archive/test-010.md"

#### Scenario: Path prints multiple locations
- Given tickets "test-001" and "test-002" exist
- When the user runs `tq path test-001 test-002`
- Then the output has one path per line
- And the output contains ".tickets/test-001.md"
- And the output contains ".tickets/test-002.md"

#### Scenario: Path with one unknown ID prints nothing
- Given ticket "test-001" exists
- When the user runs `tq path test-001 nonexistent`
- Then the command exits non-zero
- And stdout is empty

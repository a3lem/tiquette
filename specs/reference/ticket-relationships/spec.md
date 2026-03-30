# Ticket Relationships

Covers dependency, parent-child, and link management: `dep`, `undep`, `nest`, `unnest`, `link`, `unlink`.

## Requirement: Add dependency

The system SHALL add a blocking dependency when `tq dep <id> <dep-id>` is invoked. The ticket `<id>` is blocked by `<dep-id>`. Multiple dep-ids may be specified in one call.

### Scenario: Add a dependency
- Given tickets "task-0001" and "task-0002" exist
- When the user runs `tq dep task-0001 task-0002`
- Then the command exits 0
- And ticket "task-0001" has "task-0002" in deps

### Scenario: Dependency is idempotent
- Given ticket "task-0001" already depends on "task-0002"
- When the user runs `tq dep task-0001 task-0002`
- Then the command exits 0

### Scenario: Non-existent dependency target
- Given ticket "task-0001" exists
- When the user runs `tq dep task-0001 nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Non-existent source ticket
- When the user runs `tq dep nonexistent task-0001`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

## Requirement: Cycle detection

The system SHALL reject a dependency that would create a cycle, exiting non-zero.

### Scenario: Direct cycle rejected
- Given ticket "task-0001" depends on "task-0002"
- When the user runs `tq dep task-0002 task-0001`
- Then the command exits non-zero
- And stderr contains "cycle"

### Scenario: Transitive cycle rejected
- Given ticket "task-0001" depends on "task-0002"
- And ticket "task-0002" depends on "task-0003"
- When the user runs `tq dep task-0003 task-0001`
- Then the command exits non-zero
- And stderr contains "cycle"

## Requirement: Remove dependency

The system SHALL remove blocking dependencies when `tq undep <id> <dep-id> [dep-id...]` is invoked. Multiple dep-ids may be specified in one call.

### Scenario: Remove a dependency
- Given ticket "task-0001" depends on "task-0002"
- When the user runs `tq undep task-0001 task-0002`
- Then the command exits 0
- And ticket "task-0001" does not have "task-0002" in deps

### Scenario: Remove multiple dependencies
- Given ticket "task-0001" depends on "task-0002" and "task-0003"
- When the user runs `tq undep task-0001 task-0002 task-0003`
- Then the command exits 0
- And ticket "task-0001" has no deps

### Scenario: Remove non-existent dependency
- Given tickets "task-0001" and "task-0002" exist with no dependency between them
- When the user runs `tq undep task-0001 task-0002`
- Then the command exits non-zero

## Requirement: Link tickets

The system SHALL create symmetric links between tickets when `tq link` is invoked. Linking is bidirectional: both tickets reference each other. Multiple IDs may be specified, linking all pairs.

### Scenario: Link two tickets
- Given tickets "link-0001" and "link-0002" exist
- When the user runs `tq link link-0001 link-0002`
- Then the command exits 0
- And ticket "link-0001" has "link-0002" in links
- And ticket "link-0002" has "link-0001" in links

### Scenario: Link three tickets
- Given tickets "link-0001", "link-0002", and "link-0003" exist
- When the user runs `tq link link-0001 link-0002 link-0003`
- Then the command exits 0
- And all six directional links exist between the three tickets

### Scenario: Link is idempotent
- Given ticket "link-0001" is already linked to "link-0002"
- When the user runs `tq link link-0001 link-0002`
- Then the command exits 0

### Scenario: Link with non-existent ticket
- When the user runs `tq link link-0001 nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

## Requirement: Unlink tickets

The system SHALL remove symmetric links between tickets when `tq unlink` is invoked.

### Scenario: Unlink two tickets
- Given ticket "link-0001" is linked to "link-0002"
- When the user runs `tq unlink link-0001 link-0002`
- Then the command exits 0
- And ticket "link-0001" does not have "link-0002" in links
- And ticket "link-0002" does not have "link-0001" in links

### Scenario: Unlink multiple targets
- Given ticket "link-0001" is linked to "link-0002" and "link-0003"
- When the user runs `tq unlink link-0001 link-0002 link-0003`
- Then the command exits 0
- And all links between these tickets are removed

### Scenario: Unlink non-existent link
- Given tickets "link-0001" and "link-0002" exist with no link between them
- When the user runs `tq unlink link-0001 link-0002`
- Then the command exits non-zero

## Requirement: Nest tickets

The system SHALL set a ticket's parent when `tq nest <child-id> <parent-id>` is invoked. The last argument is the destination parent (like `mv`).

### Scenario: Nest a child under a parent
- Given tickets "child-001" and "parent-001" exist
- When the user runs `tq nest child-001 parent-001`
- Then the command exits 0
- And ticket "child-001" has field `parent` with value `parent-001`

### Scenario: Nest multiple children
- Given tickets "child-001", "child-002", and "parent-001" exist
- When the user runs `tq nest child-001 child-002 parent-001`
- Then the command exits 0
- And both children have field `parent` with value `parent-001`

## Requirement: Unnest tickets

The system SHALL remove a ticket's parent when `tq unnest <id>` is invoked.

### Scenario: Unnest a ticket
- Given ticket "child-001" has parent "parent-001"
- When the user runs `tq unnest child-001`
- Then the command exits 0
- And ticket "child-001" has no `parent` field

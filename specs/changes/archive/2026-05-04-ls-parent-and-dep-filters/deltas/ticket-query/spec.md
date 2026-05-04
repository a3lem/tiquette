# Ticket Query

## ADDED Requirements

### Requirement: List filtered by parent

The system SHALL restrict `tq ls` to a named ticket and its transitive descendants when `--parent <id>` is supplied. The named ticket appears as the root of the tree; its descendants appear nested beneath it via the existing tree rendering. `<id>` SHALL be resolved using the standard partial-ID resolution. `--parent` SHALL stack with all other filters; rows that survive the descendant restriction are then subject to `--status`, `--ready`, `--blocked`, `--tag`, `--type`, `--assignee`, `--limit`, `--sort`, `--archived`, and `--all`. `--parent` and `--dep` SHALL be mutually exclusive.

#### Scenario: Parent shows itself and descendants
- Given "epic-001" has child "task-001" which has child "task-002"
- And unrelated ticket "other-001" exists
- When the user runs `tq ls --parent epic-001`
- Then the output contains "epic-001"
- And the output contains "task-001"
- And the output contains "task-002"
- And the output does not contain "other-001"

#### Scenario: Parent renders as tree with root
- Given "epic-001" has child "task-001"
- When the user runs `tq ls --parent epic-001`
- Then "epic-001" appears at root level without indentation
- And "task-001" appears indented beneath "epic-001" with box-drawing characters

#### Scenario: Parent accepts partial ID
- Given "epic-001" has child "task-001"
- When the user runs `tq ls --parent 001`
- Then the output contains "epic-001"
- And the output contains "task-001"

#### Scenario: Parent with non-existent ID
- When the user runs `tq ls --parent nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Parent with leaf ticket (no descendants)
- Given "leaf-001" has no children
- When the user runs `tq ls --parent leaf-001`
- Then the output contains "leaf-001"
- And no indented child rows appear

#### Scenario: Parent stacks with --ready
- Given "epic-001" has children "task-001" (ready, no deps) and "task-002" (blocked by open "task-003")
- When the user runs `tq ls --parent epic-001 --ready`
- Then the output contains "task-001"
- And the output does not contain "task-002"

#### Scenario: Parent stacks with --status
- Given "epic-001" has children "task-001" (open) and "task-002" (completed)
- When the user runs `tq ls --parent epic-001 --status completed`
- Then the output contains "task-002"
- And the output does not contain "task-001"

#### Scenario: Parent stacks with --tag
- Given "epic-001" has children "task-001" (tag "ui") and "task-002" (tag "backend")
- When the user runs `tq ls --parent epic-001 --tag ui`
- Then the output contains "task-001"
- And the output does not contain "task-002"

### Requirement: List filtered by dependent

The system SHALL restrict `tq ls` to tickets whose `deps` field directly contains `<id>` when `--dep <id>` is supplied. Only direct dependents are included; transitive dependents (tickets that reach `<id>` through a chain of deps) are not. The output SHALL be a flat list using the standard line format from "List ticket line format"; tree rendering from "List with tree rendering" is suppressed under `--dep`. `<id>` SHALL be resolved using the standard partial-ID resolution. `--dep` SHALL stack with all other filters. `--dep` and `--parent` SHALL be mutually exclusive.

#### Scenario: Dep shows direct dependents
- Given "task-002" has deps containing "task-001"
- And "task-003" has deps containing "task-001"
- And unrelated "other-001" exists
- When the user runs `tq ls --dep task-001`
- Then the output contains "task-002"
- And the output contains "task-003"
- And the output does not contain "other-001"

#### Scenario: Dep excludes transitive dependents
- Given "task-002" has deps containing "task-001"
- And "task-003" has deps containing "task-002" (but not "task-001")
- When the user runs `tq ls --dep task-001`
- Then the output contains "task-002"
- And the output does not contain "task-003"

#### Scenario: Dep excludes the target ticket itself
- Given "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep task-001`
- Then the output does not contain "task-001"

#### Scenario: Dep with no dependents
- Given no ticket has "leaf-001" in its deps
- When the user runs `tq ls --dep leaf-001`
- Then the output is empty

#### Scenario: Dep accepts partial ID
- Given "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep 001`
- Then the output contains "task-002"

#### Scenario: Dep with non-existent ID
- When the user runs `tq ls --dep nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

#### Scenario: Dep output is flat (no tree)
- Given "parent-001" has child "task-002"
- And "task-002" has deps containing "task-001"
- When the user runs `tq ls --dep task-001`
- Then "task-002" appears at root level without indentation
- And "parent-001" does not appear as a context heading

#### Scenario: Dep stacks with --status
- Given "task-002" (open) and "task-003" (completed) both have deps containing "task-001"
- When the user runs `tq ls --dep task-001 --status open`
- Then the output contains "task-002"
- And the output does not contain "task-003"

#### Scenario: Dep stacks with --tag
- Given "task-002" (tag "ui") and "task-003" (tag "backend") both have deps containing "task-001"
- When the user runs `tq ls --dep task-001 --tag ui`
- Then the output contains "task-002"
- And the output does not contain "task-003"

#### Scenario: --parent and --dep mutually exclusive
- When the user runs `tq ls --parent epic-001 --dep task-001`
- Then the command exits non-zero

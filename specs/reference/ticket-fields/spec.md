# Ticket Fields

Covers commands that modify individual ticket fields: `assign`, `unassign`, `change-prio`, `change-type`, `tag`, `untag`, `set-ref`, `unset-ref`.

## Requirement: Assign

The system SHALL set a ticket's assignee when `tq assign <id> <assignee>` is invoked.

### Scenario: Assign a user
- Given ticket "t-001" exists with no assignee
- When the user runs `tq assign t-001 "Alice"`
- Then ticket "t-001" has field `assignee` with value `Alice`

### Scenario: Reassign
- Given ticket "t-001" has assignee "Alice"
- When the user runs `tq assign t-001 "Bob"`
- Then ticket "t-001" has field `assignee` with value `Bob`

## Requirement: Unassign

The system SHALL clear a ticket's assignee when `tq unassign <id>` is invoked.

### Scenario: Unassign a user
- Given ticket "t-001" has assignee "Alice"
- When the user runs `tq unassign t-001`
- Then ticket "t-001" has no assignee value

## Requirement: Change priority

The system SHALL update a ticket's priority when `tq change-prio <id> <priority>` is invoked. Valid range is 0–4.

### Scenario: Change priority
- Given ticket "t-001" has priority 2
- When the user runs `tq change-prio t-001 0`
- Then ticket "t-001" has field `priority` with value `0`

### Scenario: Invalid priority rejected
- When the user runs `tq change-prio t-001 5`
- Then the command exits non-zero

## Requirement: Change type

The system SHALL update a ticket's type when `tq change-type <id> <type>` is invoked. Valid types: bug, feature, task, epic, chore.

### Scenario: Change type
- Given ticket "t-001" has type task
- When the user runs `tq change-type t-001 bug`
- Then ticket "t-001" has field `type` with value `bug`

### Scenario: Invalid type rejected
- When the user runs `tq change-type t-001 invalid`
- Then the command exits non-zero

## Requirement: Tag management

The system SHALL append tags when `tq tag <id> <tag,...>` is invoked and remove tags when `tq untag <id> <tag,...>` is invoked. Tags are comma-separated.

### Scenario: Add tags
- Given ticket "t-001" has no tags
- When the user runs `tq tag t-001 ui,backend`
- Then ticket "t-001" has tags `[ui, backend]`

### Scenario: Add tags is additive
- Given ticket "t-001" has tags `[ui]`
- When the user runs `tq tag t-001 backend`
- Then ticket "t-001" has tags `[ui, backend]`

### Scenario: Duplicate tags not added
- Given ticket "t-001" has tags `[ui]`
- When the user runs `tq tag t-001 ui`
- Then ticket "t-001" has tags `[ui]`

### Scenario: Remove tags
- Given ticket "t-001" has tags `[ui, backend]`
- When the user runs `tq untag t-001 backend`
- Then ticket "t-001" has tags `[ui]`

## Requirement: External reference

The system SHALL set or clear an external reference when `tq set-ref` / `tq unset-ref` is invoked.

### Scenario: Set reference
- Given ticket "t-001" has no ref
- When the user runs `tq set-ref t-001 "gh-123"`
- Then ticket "t-001" has field `ref` with value `gh-123`

### Scenario: Clear reference
- Given ticket "t-001" has ref "gh-123"
- When the user runs `tq unset-ref t-001`
- Then ticket "t-001" has no ref value

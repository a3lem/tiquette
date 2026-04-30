# Ticket Query

## MODIFIED Requirements

### Requirement: List ticket line format

The system SHALL format each ticket line in `ls` output as: `<id> <tags> - <checkbox> <title>` where:

- The checkbox represents lifecycle state: `[ ]` for open, `[/]` for in_progress, `[x]` for closed with resolution `completed`, and `[~]` for closed with resolution `canceled`.
- Zero or more tag tokens may appear after the ID, each individually bracketed:
  - The priority tag `[P<n>]` SHALL be shown only when priority is not 2 (the default).
  - The type tag (e.g. `[epic]`, `[feature]`) SHALL be shown only when the type is not "task" (the default).
  - When both are present, priority comes first: `[P1][epic]` (no space between tags).
- When no tags are present, the format collapses to `<id> - <checkbox> <title>`.
- Dependencies are appended after the title as a comma-separated list: `<- [dep-id1, dep-id2]`.

#### Scenario: Default priority and type hidden
- Given ticket "fmt-001" exists with priority 2, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [ ] Fix login`

#### Scenario: Non-default priority shown
- Given ticket "fmt-001" exists with priority 1, type "task", status open, title "Fix login"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P1] - [ ] Fix login`

#### Scenario: Non-default type shown
- Given ticket "fmt-001" exists with priority 2, type "feature", status open, title "Add export"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [feature] - [ ] Add export`

#### Scenario: Both non-default priority and type shown
- Given ticket "fmt-001" exists with priority 3, type "epic", status open, title "Refactor"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 [P3][epic] - [ ] Refactor`

#### Scenario: In-progress renders half checkbox
- Given ticket "fmt-001" exists with priority 2, type "task", status in_progress, title "Working"
- When the user runs `tq ls`
- Then the line for "fmt-001" is `fmt-001 - [/] Working`

#### Scenario: Completed renders checked checkbox
- Given ticket "fmt-001" exists with status closed and resolution `completed`
- When the user runs `tq ls --status closed`
- Then the line contains `[x]`

#### Scenario: Canceled renders tilde checkbox
- Given ticket "fmt-001" exists with status closed and resolution `canceled`
- When the user runs `tq ls --status closed`
- Then the line contains `[~]`
- And the line does not contain `[x]`

#### Scenario: Single dependency appended after title
- Given ticket "fmt-001" depends on "fmt-002"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002]`

#### Scenario: Multiple dependencies appended after title
- Given ticket "fmt-001" depends on "fmt-002" and "fmt-003"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002, fmt-003]`

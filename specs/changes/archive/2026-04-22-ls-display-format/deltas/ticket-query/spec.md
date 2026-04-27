# Ticket Query — Delta: ls-display-format

## ADDED

### Requirement: List ticket line format

The system SHALL format each ticket line in `ls` output as: `<id> [<tags>] - [<checkbox>] <title>` where:

- The checkbox represents status: `[ ]` for open, `[/]` for in_progress, `[x]` for closed.
- The priority tag `[P<n>]` SHALL be shown only when priority is not 2 (the default).
- The type tag (e.g. `[epic]`, `[feature]`) SHALL be shown only when the type is not "task" (the default).
- When both priority and type tags are present, priority comes first: `[P1][epic]`.
- When neither tag is present, the format collapses to `<id> - [<checkbox>] <title>`.
- Dependencies are appended after the title: `<- [dep-id1, dep-id2]`.

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
- Given ticket "fmt-001" exists with status in_progress
- When the user runs `tq ls`
- Then the line contains `[/]`

#### Scenario: Closed renders checked checkbox
- Given ticket "fmt-001" exists with status closed
- When the user runs `tq ls --status closed`
- Then the line contains `[x]`

#### Scenario: Dependencies appended after title
- Given ticket "fmt-001" depends on "fmt-002"
- When the user runs `tq ls`
- Then the line for "fmt-001" ends with `<- [fmt-002]`

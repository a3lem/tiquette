# Ticket Edit

Covers the `tq edit` command: the single post-creation mutation surface for ticket fields.

## Scenarios

### Requirement: Edit command

The system SHALL accept `tq edit <id> [field-options]` as the single
post-creation mutation surface for ticket fields. The system SHALL accept
every field-option that `tq create` accepts (`-d/--description`,
`-t/--type`, `-p/--priority`, `-A/--assignee`, `--xref`, `--parent`,
`--tag`, `--dep`, `--link`, `--note`) and SHALL additionally accept
`--title`, `--untag`, `--undep`, `--unlink`, and `--unset`. WHEN no
field-options are supplied, the system SHALL exit non-zero with a
message indicating at least one field-option is required. WHEN `<id>` does
not resolve to a ticket, the system SHALL exit non-zero.

#### Scenario: Edit changes a single field
- Given ticket "edit-001" has priority 2
- When the user runs `tq edit edit-001 -p 0`
- Then the command exits 0
- And ticket "edit-001" has field `priority` with value `0`

#### Scenario: Edit changes multiple fields in one call
- Given ticket "edit-001" has priority 2 and assignee "Alice"
- When the user runs `tq edit edit-001 -p 0 -A Bob --tag urgent`
- Then the command exits 0
- And ticket "edit-001" has field `priority` with value `0`
- And ticket "edit-001" has field `assignee` with value `Bob`
- And ticket "edit-001" has tag `urgent`

#### Scenario: Edit with no flags is an error
- Given ticket "edit-001" exists
- When the user runs `tq edit edit-001`
- Then the command exits non-zero
- And stderr indicates at least one field-option is required

#### Scenario: Edit on missing id
- When the user runs `tq edit nonexistent -p 0`
- Then the command exits non-zero
- And stderr contains "not found"

### Requirement: Rename via --title

The system SHALL replace the ticket's title with the value supplied to
`--title TEXT` when `tq edit` is invoked. The system SHALL preserve the
ticket id.

#### Scenario: Rename a ticket
- Given ticket "edit-002" has title "Old title"
- When the user runs `tq edit edit-002 --title "New title"`
- Then ticket "edit-002" has title "New title"
- And ticket "edit-002" retains id "edit-002"

### Requirement: Description replace via --description

The system SHALL replace (not append) the ticket's body content with the
value supplied to `--description TEXT` when `tq edit` is invoked. WHEN
`--description` is supplied more than once in a single invocation, the
system SHALL use the last value supplied.

#### Scenario: Replace description
- Given ticket "edit-003" has body "old body"
- When the user runs `tq edit edit-003 -d "new body"`
- Then ticket "edit-003" has body "new body"

#### Scenario: Last --description wins
- Given ticket "edit-003" exists
- When the user runs `tq edit edit-003 -d "first" -d "second"`
- Then ticket "edit-003" has body "second"

### Requirement: Notes append via --note

The system SHALL append a timestamped note to the ticket's `## Notes`
section for each `--note TEXT` supplied to `tq edit`. All notes in one
invocation SHALL share a single timestamp.

#### Scenario: Single note
- Given ticket "edit-004" exists
- When the user runs `tq edit edit-004 --note "kickoff"`
- Then ticket "edit-004" contains a `## Notes` section
- And the notes section contains "kickoff" with an ISO 8601 timestamp

#### Scenario: Multiple notes share a timestamp
- Given ticket "edit-004" exists
- When the user runs `tq edit edit-004 --note "first" --note "second"`
- Then both notes appear in `## Notes` in order
- And both notes carry the same ISO 8601 timestamp

### Requirement: Tag add/remove

The system SHALL add each value supplied to `--tag TAG` to the ticket's
tag list when `tq edit` is invoked. The system SHALL remove each value
supplied to `--untag TAG` from the tag list. Adding a tag that already
exists SHALL be a no-op. Removing a tag that is absent SHALL be a no-op.
Both flags SHALL be repeatable and combinable in one invocation.

#### Scenario: Add and remove tags in one call
- Given ticket "edit-005" has tags ["stale", "backend"]
- When the user runs `tq edit edit-005 --tag urgent --untag stale`
- Then ticket "edit-005" has tags including "urgent" and "backend"
- And ticket "edit-005" does not have tag "stale"

#### Scenario: Re-adding a tag is a no-op
- Given ticket "edit-005" has tag "urgent"
- When the user runs `tq edit edit-005 --tag urgent`
- Then the command exits 0
- And ticket "edit-005" has tag "urgent" exactly once

### Requirement: Dependency add/remove

The system SHALL add each value supplied to `--dep ID` to the ticket's
deps list when `tq edit` is invoked, treating the ticket as blocked by
each dep. The system SHALL remove each value supplied to `--undep ID`
from the deps list. The system SHALL reject adds that would introduce a
cycle. Both flags SHALL be repeatable.

#### Scenario: Add and remove deps in one call
- Given ticket "edit-006" depends on "edit-006a"
- When the user runs `tq edit edit-006 --dep edit-006b --undep edit-006a`
- Then ticket "edit-006" depends on "edit-006b"
- And ticket "edit-006" no longer depends on "edit-006a"

#### Scenario: Add dep that would cycle is rejected
- Given "edit-006" depends on "edit-006b"
- When the user runs `tq edit edit-006b --dep edit-006`
- Then the command exits non-zero
- And stderr indicates a cycle

### Requirement: Link add/remove

The system SHALL add each value supplied to `--link ID` to the ticket's
links list when `tq edit` is invoked. Links SHALL be symmetric: the
target ticket SHALL be updated to back-reference the source. The system
SHALL remove each value supplied to `--unlink ID` from both sides. Both
flags SHALL be repeatable.

#### Scenario: Link is symmetric
- Given tickets "edit-007" and "edit-007b" exist with no links
- When the user runs `tq edit edit-007 --link edit-007b`
- Then ticket "edit-007" lists "edit-007b" in links
- And ticket "edit-007b" lists "edit-007" in links

#### Scenario: Unlink is symmetric
- Given tickets "edit-007" and "edit-007b" are linked
- When the user runs `tq edit edit-007 --unlink edit-007b`
- Then neither ticket lists the other in links

### Requirement: Parent set via --parent

The system SHALL set the ticket's `parent` field to the supplied id when
`--parent ID` is given to `tq edit`. The system SHALL reject parent
assignments that would introduce a cycle (a ticket cannot be its own
ancestor).

#### Scenario: Re-parent a ticket
- Given ticket "edit-008" has parent "edit-008a"
- When the user runs `tq edit edit-008 --parent edit-008b`
- Then ticket "edit-008" has parent "edit-008b"

#### Scenario: Parent assignment that would cycle is rejected
- Given "edit-008" has child "edit-008c"
- When the user runs `tq edit edit-008 --parent edit-008c`
- Then the command exits non-zero
- And stderr indicates a cycle

### Requirement: Single-value field clear via --unset

The system SHALL clear the named single-value field when `--unset FIELD`
is supplied to `tq edit`. FIELD SHALL be one of `parent`, `xref`,
`assignee`. The flag SHALL be repeatable so multiple fields can be
cleared in one call. WHEN `FIELD` is not in the allowed set, the system
SHALL exit non-zero with an argparse "invalid choice" error.

#### Scenario: Clear assignee
- Given ticket "edit-009" has assignee "Alice"
- When the user runs `tq edit edit-009 --unset assignee`
- Then ticket "edit-009" has no assignee

#### Scenario: Clear multiple fields in one call
- Given ticket "edit-009" has assignee "Alice" and xref "gh-1"
- When the user runs `tq edit edit-009 --unset assignee --unset xref`
- Then ticket "edit-009" has no assignee
- And ticket "edit-009" has no xref

#### Scenario: --unset description is rejected
- When the user runs `tq edit edit-009 --unset description`
- Then the command exits non-zero
- And stderr indicates "invalid choice"

#### Scenario: --unset on an already-empty field is a no-op
- Given ticket "edit-009" has no assignee
- When the user runs `tq edit edit-009 --unset assignee`
- Then the command exits 0
- And ticket "edit-009" has no assignee

### Requirement: Set/unset conflict

IF the same field is both set (via its set flag) and cleared (via
`--unset`) in one `tq edit` invocation, the system SHALL exit non-zero
before applying any change, with stderr indicating the conflicting
field.

#### Scenario: Setting and unsetting the same field is rejected
- Given ticket "edit-010" exists
- When the user runs `tq edit edit-010 -A Bob --unset assignee`
- Then the command exits non-zero
- And stderr names `assignee`
- And ticket "edit-010" is unchanged

### Requirement: Type and priority via --type / --priority

The system SHALL set the ticket's `type` field when `-t/--type` is
supplied to `tq edit`. The system SHALL set the ticket's `priority`
field when `-p/--priority` is supplied. Both flags accept the same
value sets as `create`.

#### Scenario: Change type
- Given ticket "edit-011" has type "task"
- When the user runs `tq edit edit-011 -t bug`
- Then ticket "edit-011" has type "bug"

#### Scenario: Change priority
- Given ticket "edit-011" has priority 2
- When the user runs `tq edit edit-011 -p 0`
- Then ticket "edit-011" has priority 0

### Requirement: External reference via --xref

The system SHALL set the ticket's `xref` field to the supplied value
when `--xref REF` is given to `tq edit`. The value SHALL be cleared via
`--unset xref`.

#### Scenario: Set external reference
- Given ticket "edit-012" has no xref
- When the user runs `tq edit edit-012 --xref gh-42`
- Then ticket "edit-012" has xref "gh-42"

### Requirement: Atomicity

The system SHALL apply all field changes from a single `tq edit`
invocation atomically: either every change is written to disk or none
is. WHEN any validation fails (cycle, set/unset conflict, missing
target for `--dep`/`--link`), the system SHALL leave every affected
ticket file unchanged.

#### Scenario: Failed dep target leaves ticket unchanged
- Given ticket "edit-013" has priority 2
- When the user runs `tq edit edit-013 -p 0 --dep nonexistent`
- Then the command exits non-zero
- And ticket "edit-013" still has priority 2

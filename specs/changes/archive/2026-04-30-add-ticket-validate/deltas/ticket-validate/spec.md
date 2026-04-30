# Ticket Validate

Covers the `validate` command, which checks all non-archived tickets for referential integrity.

## ADDED Requirements

### Requirement: Validate command

The system SHALL provide a `tq validate` command that checks every non-archived ticket for integrity problems and reports all violations found.

IF violations are found, the system SHALL exit non-zero. IF only warnings (or no problems) are found, the system SHALL exit zero.

#### Scenario: Clean ticket store
- Given all tickets have valid deps, parents, and links
- When the user runs `tq validate`
- Then the command exits zero
- And no violations or warnings are printed

#### Scenario: Violations found
- Given at least one ticket has an integrity violation
- When the user runs `tq validate`
- Then the command exits non-zero
- And each violation is printed to stderr

#### Scenario: Only warnings found
- Given no ticket has an integrity violation
- But at least one ticket has a warning condition
- When the user runs `tq validate`
- Then the command exits zero
- And each warning is printed to stderr

### Requirement: Output format

The system SHALL print each problem as a single line to stderr in the format `<ticket-id>: <message>`. Violations SHALL be prefixed with `error:` and warnings with `warning:` in the message.

#### Scenario: Violation output
- Given ticket "proj-a001" depends on non-existent ticket "proj-gone"
- When the user runs `tq validate`
- Then stderr contains `proj-a001: error: depends on non-existent ticket "proj-gone"`

#### Scenario: Warning output
- Given ticket "proj-a001" depends on archived ticket "proj-old1"
- When the user runs `tq validate`
- Then stderr contains `proj-a001: warning: depends on archived ticket "proj-old1"`

### Requirement: Summary line

The system SHALL always print a summary line to stderr after all problems. The summary SHALL state the count of violations and warnings found.

#### Scenario: Summary with violations
- Given 2 violations and 1 warning exist
- When the user runs `tq validate`
- Then the last line of stderr is `2 errors, 1 warning`

#### Scenario: Summary all clean
- Given no violations or warnings exist
- When the user runs `tq validate`
- Then the last line of stderr is `all tickets valid`

#### Scenario: Summary warnings only
- Given 0 violations and 2 warnings exist
- When the user runs `tq validate`
- Then the last line of stderr is `0 errors, 2 warnings`

### Requirement: Dependency existence

WHEN a ticket's `deps` list references a ticket ID, the system SHALL verify that the referenced ticket exists among non-archived tickets. IF the referenced dependency does not exist at all, the system SHALL report a violation. IF the referenced dependency exists only as an archived ticket, the system SHALL report a warning.

#### Scenario: Valid dependency
- Given ticket "proj-a001" exists with `deps: [proj-b002]`
- And ticket "proj-b002" exists (non-archived)
- When the user runs `tq validate`
- Then no problem is reported for "proj-a001"

#### Scenario: Missing dependency
- Given ticket "proj-a001" exists with `deps: [proj-gone]`
- And no ticket with ID "proj-gone" exists
- When the user runs `tq validate`
- Then a violation is reported: `proj-a001: error: depends on non-existent ticket "proj-gone"`

#### Scenario: Multiple missing dependencies
- Given ticket "proj-a001" exists with `deps: [proj-gone, proj-also-gone]`
- And neither "proj-gone" nor "proj-also-gone" exists
- When the user runs `tq validate`
- Then a violation is reported for each missing dependency

#### Scenario: Dependency on archived ticket
- Given ticket "proj-a001" exists with `deps: [proj-old1]`
- And ticket "proj-old1" exists only in `.tickets/archive/`
- When the user runs `tq validate`
- Then a warning is reported: `proj-a001: warning: depends on archived ticket "proj-old1"`

### Requirement: Parent existence

WHEN a ticket's `parent` field references a ticket ID, the system SHALL verify that the referenced parent ticket exists among non-archived tickets. IF the referenced parent does not exist at all, the system SHALL report a violation. IF the referenced parent exists only as an archived ticket, the system SHALL report a warning.

#### Scenario: Valid parent
- Given ticket "proj-c003" exists with `parent: proj-p001`
- And ticket "proj-p001" exists (non-archived)
- When the user runs `tq validate`
- Then no problem is reported for "proj-c003"

#### Scenario: Missing parent
- Given ticket "proj-c003" exists with `parent: proj-p001`
- And no ticket with ID "proj-p001" exists
- When the user runs `tq validate`
- Then a violation is reported: `proj-c003: error: has non-existent parent "proj-p001"`

#### Scenario: Parent is archived ticket
- Given ticket "proj-c003" exists with `parent: proj-old1`
- And ticket "proj-old1" exists only in `.tickets/archive/`
- When the user runs `tq validate`
- Then a warning is reported: `proj-c003: warning: has archived parent "proj-old1"`

### Requirement: Link existence

WHEN a ticket's `links` list references a ticket ID, the system SHALL verify that the referenced ticket exists among non-archived tickets. IF the referenced link target does not exist at all, the system SHALL report a violation. IF the referenced link target exists only as an archived ticket, the system SHALL report a warning.

#### Scenario: Valid link
- Given ticket "proj-a001" exists with `links: [proj-b002]`
- And ticket "proj-b002" exists (non-archived)
- When the user runs `tq validate`
- Then no problem is reported for "proj-a001"

#### Scenario: Missing link target
- Given ticket "proj-a001" exists with `links: [proj-gone]`
- And no ticket with ID "proj-gone" exists
- When the user runs `tq validate`
- Then a violation is reported: `proj-a001: error: links to non-existent ticket "proj-gone"`

#### Scenario: Link to archived ticket
- Given ticket "proj-a001" exists with `links: [proj-old1]`
- And ticket "proj-old1" exists only in `.tickets/archive/`
- When the user runs `tq validate`
- Then a warning is reported: `proj-a001: warning: links to archived ticket "proj-old1"`

### Requirement: Scope

The system SHALL check only non-archived tickets. Tickets under `.tickets/archive/` SHALL be excluded from validation but SHALL be recognized when determining whether a reference target exists (to distinguish "missing" from "archived").

#### Scenario: Archived ticket excluded from checks
- Given ticket "proj-old1" is archived and references non-existent dep "proj-gone"
- And no non-archived tickets have violations
- When the user runs `tq validate`
- Then the command exits zero
- And no violation is reported for "proj-old1"

# Ticket Edit

## MODIFIED Requirements

### Requirement: Dependency add/remove

The system SHALL add each value supplied to `--dep ID` to the ticket's
deps list when `tq edit` is invoked, treating the ticket as blocked by
each dep. The system SHALL remove each value supplied to `--undep ID`
from the deps list. The system SHALL reject adds that would introduce a
cycle. Both flags SHALL be repeatable. `--dep`/`--undep` targets SHALL
resolve per the active-only rule in `id-resolution`'s "ID resolution
across commands" requirement.

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
flags SHALL be repeatable. `--link`/`--unlink` targets SHALL resolve per
the active-only rule in `id-resolution`'s "ID resolution across
commands" requirement.

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
ancestor). `--parent` targets SHALL resolve per the active-only rule in
`id-resolution`'s "ID resolution across commands" requirement.

#### Scenario: Re-parent a ticket
- Given ticket "edit-008" has parent "edit-008a"
- When the user runs `tq edit edit-008 --parent edit-008b`
- Then ticket "edit-008" has parent "edit-008b"

#### Scenario: Parent assignment that would cycle is rejected
- Given "edit-008" has child "edit-008c"
- When the user runs `tq edit edit-008 --parent edit-008c`
- Then the command exits non-zero
- And stderr indicates a cycle

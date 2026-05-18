# Ticket Relationships

## MODIFIED Requirements

### Requirement: Cycle detection

The system SHALL reject a dependency change that would create a cycle, exiting non-zero. Cycle detection SHALL apply WHEN `--dep` is used with `tq create` or `tq edit`, and WHEN `--parent` is used with either command.

#### Scenario: Direct dependency cycle rejected
- Given ticket "task-0001" depends on "task-0002"
- When the user runs `tq edit task-0002 --dep task-0001`
- Then the command exits non-zero
- And stderr contains "cycle"

#### Scenario: Transitive dependency cycle rejected
- Given ticket "task-0001" depends on "task-0002"
- And ticket "task-0002" depends on "task-0003"
- When the user runs `tq edit task-0003 --dep task-0001`
- Then the command exits non-zero
- And stderr contains "cycle"

#### Scenario: Parent cycle rejected
- Given ticket "par-0001" has child "par-0002"
- When the user runs `tq edit par-0001 --parent par-0002`
- Then the command exits non-zero
- And stderr contains "cycle"

## REMOVED Requirements

### Requirement: Add dependency

**Reason**: Replaced by `tq edit <id> --dep <dep-id>` (and
`tq create ... --dep <dep-id>` on creation). Cycle detection moves
with the trigger; see the modified "Cycle detection" requirement.
**Migration**: Replace `tq dep <id> <dep-id> [dep-id ...]` with
`tq edit <id> --dep <dep-id> [--dep <dep-id> ...]`.

### Requirement: Remove dependency

**Reason**: Replaced by `tq edit <id> --undep <dep-id>`.
**Migration**: Replace `tq undep <id> <dep-id> [dep-id ...]` with
`tq edit <id> --undep <dep-id> [--undep <dep-id> ...]`.

### Requirement: Link tickets

**Reason**: Replaced by `tq edit <id> --link <other-id>` (and
`tq create ... --link <other-id>` on creation). Links remain
symmetric; both sides are written by `edit`/`create`.
**Migration**: Replace `tq link a b` with `tq edit a --link b` (or
`tq edit b --link a`; both produce the same outcome). For the
three-way pattern `tq link a b c`, use two `edit` calls:
`tq edit a --link b --link c` then `tq edit b --link c`. The
`link a b c` "all-pairs" sugar is not preserved.

### Requirement: Unlink tickets

**Reason**: Replaced by `tq edit <id> --unlink <other-id>`.
**Migration**: Replace `tq unlink a b` with `tq edit a --unlink b`.

### Requirement: Nest tickets

**Reason**: Replaced by `tq edit <child-id> --parent <parent-id>`.
The `mv`-style multi-arg sugar (`tq nest c1 c2 parent`) is not
preserved.
**Migration**: Replace `tq nest <child> <parent>` with
`tq edit <child> --parent <parent>`. For multiple children, run one
`edit` per child or use a shell loop.

### Requirement: Unnest tickets

**Reason**: Replaced by `tq edit <id> --unset parent`.
**Migration**: Replace `tq unnest <id>` with
`tq edit <id> --unset parent`.

# Ticket Relationships

Covers cycle detection for dependency and parent-child relationships.

## Scenarios

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

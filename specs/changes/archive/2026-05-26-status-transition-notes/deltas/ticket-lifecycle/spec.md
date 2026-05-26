# Ticket Lifecycle

## ADDED Requirements

### Requirement: Transition notes via --note

The system SHALL accept `--note TEXT` (repeatable) on `start`, `close`, `cancel`, and `reopen`. For each `--note TEXT` supplied, the system SHALL append a timestamped entry to the `## Notes` section of every ticket whose status was changed by the invocation, prefixing the entry with a verb tag corresponding to the transition: `[started]` for `start`, `[closed]` for `close`, `[canceled]` for `cancel`, `[reopened]` for `reopen`. All notes written in a single invocation SHALL share a single timestamp. IF no `--note` is supplied, the system SHALL NOT write to the Notes section. IF the transition fails (any supplied ID unknown, or a non-forced parent has non-terminal descendants), the system SHALL write no notes.

#### Scenario: Close with note
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 --note "duplicate of t-999"`
- Then the command exits 0
- And ticket "t-001" has field `status` with value `closed`
- And the `## Notes` section of "t-001" contains an entry of the form `[closed]: duplicate of t-999` with a timestamp

#### Scenario: Cancel with note
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq cancel t-001 --note "wontfix"`
- Then ticket "t-001" has field `status` with value `canceled`
- And the `## Notes` section of "t-001" contains an entry of the form `[canceled]: wontfix`

#### Scenario: Start with note
- Given a ticket "t-001" exists with status `open`
- When the user runs `tq start t-001 --note "kicking off the spike"`
- Then ticket "t-001" has field `status` with value `in_progress`
- And the `## Notes` section of "t-001" contains an entry of the form `[started]: kicking off the spike`

#### Scenario: Reopen with note
- Given a ticket "t-001" exists with status `closed`
- When the user runs `tq reopen t-001 --note "regression seen in v0.3"`
- Then ticket "t-001" has field `status` with value `open`
- And the `## Notes` section of "t-001" contains an entry of the form `[reopened]: regression seen in v0.3`

#### Scenario: Transition without --note writes nothing to Notes
- Given a ticket "t-001" exists with status `open` and no `## Notes` section
- When the user runs `tq close t-001`
- Then ticket "t-001" has field `status` with value `closed`
- And ticket "t-001" still has no `## Notes` section

#### Scenario: Multiple notes share one timestamp
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 --note "first reason" --note "second reason"`
- Then both entries appear in the `## Notes` section in order
- And both entries carry the same timestamp
- And both entries are prefixed with `[closed]:`

#### Scenario: Multi-ID transition writes notes on every affected ticket
- Given tickets "t-001" and "t-002" exist with status `open` and no children
- When the user runs `tq close t-001 t-002 --note "Q2 cleanup"`
- Then both tickets have field `status` with value `closed`
- And the `## Notes` section of "t-001" contains `[closed]: Q2 cleanup`
- And the `## Notes` section of "t-002" contains `[closed]: Q2 cleanup`

#### Scenario: Force-close cascade propagates note to descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- And ticket "par-0003" exists with parent "par-0002" and status `in_progress`
- When the user runs `tq close -f par-0001 --note "rolling up Q2"`
- Then all three tickets have field `status` with value `closed`
- And the `## Notes` section of each of "par-0001", "par-0002", "par-0003" contains `[closed]: rolling up Q2`

#### Scenario: Force-close cascade without --note writes nothing
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close -f par-0001`
- Then both tickets have field `status` with value `closed`
- And neither ticket has a `## Notes` section

#### Scenario: Force-cascade does not write notes on already-terminal descendants
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `canceled` and no `## Notes` section
- When the user runs `tq close -f par-0001 --note "rollup"`
- Then ticket "par-0001" has field `status` with value `closed`
- And the `## Notes` section of "par-0001" contains `[closed]: rollup`
- And ticket "par-0002" still has status `canceled`
- And ticket "par-0002" still has no `## Notes` section

#### Scenario: Failed transition writes no notes
- Given a ticket "t-001" exists with status `open` and no children
- When the user runs `tq close t-001 nonexistent --note "should not land"`
- Then the command exits non-zero
- And ticket "t-001" has field `status` with value `open`
- And ticket "t-001" has no `## Notes` section

#### Scenario: Rejected force-less cascade writes no notes
- Given ticket "par-0001" exists with status `open`
- And ticket "par-0002" exists with parent "par-0001" and status `open`
- When the user runs `tq close par-0001 --note "should not land"`
- Then the command exits non-zero
- And ticket "par-0001" has field `status` with value `open`
- And ticket "par-0001" has no `## Notes` section

### Requirement: Reject idempotent transitions

The system SHALL reject any `start`, `close`, `cancel`, or `reopen` invocation in which any target ticket's current status already equals the requested target status. The check SHALL run after ID resolution and before any write, so a single already-at-target ticket aborts the whole batch atomically: no ticket file is modified and no notes are written. The error message SHALL identify the ticket and its current status (e.g. `<id> is already <status>`).

#### Scenario: Reopen on an already-open ticket is rejected
- Given a ticket "t-001" exists with status `open`
- When the user runs `tq reopen t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already open`
- And ticket "t-001" still has status `open`

#### Scenario: Close on an already-closed ticket is rejected
- Given a ticket "t-001" exists with status `closed`
- When the user runs `tq close t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already closed`

#### Scenario: Start on an already-in_progress ticket is rejected
- Given a ticket "t-001" exists with status `in_progress`
- When the user runs `tq start t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already in_progress`

#### Scenario: Cancel on an already-canceled ticket is rejected
- Given a ticket "t-001" exists with status `canceled`
- When the user runs `tq cancel t-001`
- Then the command exits non-zero
- And stderr contains `t-001 is already canceled`

#### Scenario: One already-at-target ticket aborts the whole batch
- Given ticket "t-001" exists with status `open` and no `## Notes` section
- And ticket "t-002" exists with status `closed`
- When the user runs `tq close t-001 t-002 --note "Q2 cleanup"`
- Then the command exits non-zero
- And stderr contains `t-002 is already closed`
- And ticket "t-001" still has status `open`
- And ticket "t-001" still has no `## Notes` section

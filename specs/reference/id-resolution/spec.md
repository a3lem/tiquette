# ID Resolution

Covers partial ticket ID matching, used by all commands that accept a ticket ID.

## Requirement: Partial ID matching

The system SHALL resolve partial IDs to full ticket IDs by matching against all ticket files. It SHALL match by exact match first, then by substring.

### Scenario: Exact ID match
- Given ticket "abc-1234" exists
- When the user runs `tq show abc-1234`
- Then the output contains "id: abc-1234"

### Scenario: Partial match by suffix
- Given ticket "abc-1234" exists
- When the user runs `tq show 1234`
- Then the output contains "id: abc-1234"

### Scenario: Partial match by prefix
- Given ticket "abc-1234" exists
- When the user runs `tq show abc`
- Then the output contains "id: abc-1234"

### Scenario: Partial match by substring
- Given ticket "abc-1234" exists
- When the user runs `tq show c-12`
- Then the output contains "id: abc-1234"

### Scenario: Ambiguous ID error
- Given tickets "abc-1234" and "abc-5678" exist
- When the user runs `tq show abc`
- Then the command exits non-zero
- And stderr contains "ambiguous ID 'abc' matches multiple tickets"

### Scenario: Non-existent ID error
- When the user runs `tq show nonexistent`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Exact match takes precedence over substring
- Given tickets "abc" and "abc-1234" exist
- When the user runs `tq show abc`
- Then the output contains "id: abc"
- And the output contains the title of ticket "abc"

## Requirement: ID resolution across commands

Partial ID resolution SHALL work uniformly across all commands that accept ticket IDs.

### Scenario: Partial ID with dep command
- Given tickets "dep-aaaa" and "dep-bbbb" exist
- When the user runs `tq dep aaaa bbbb`
- Then the command exits 0
- And ticket "dep-aaaa" has "dep-bbbb" in deps

### Scenario: Partial ID with link command
- Given tickets "link-cccc" and "link-dddd" exist
- When the user runs `tq link cccc dddd`
- Then the command exits 0
- And ticket "link-cccc" has "link-dddd" in links

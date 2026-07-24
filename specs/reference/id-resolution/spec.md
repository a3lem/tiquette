# ID Resolution

Covers partial ticket ID matching, used by all commands that accept a ticket ID.

## Requirement: Partial ID matching

The system SHALL resolve partial IDs to full ticket IDs by matching against the candidate ticket set selected by the invoking command (see "ID resolution across commands" for which commands include archived tickets in that set). It SHALL match by exact match first, then by substring. IF the same full ID exists as both an active and an archived ticket file, and the invoking command's candidate set includes both, the system SHALL resolve to the active ticket.

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

### Scenario: Exact match of an archived ticket
- Given archived ticket "arc-1234" exists in `.tickets/archive/`
- And no active ticket "arc-1234" exists
- When the user runs `tq show arc-1234`
- Then the output contains "id: arc-1234"

### Scenario: Partial match of an archived ticket
- Given archived ticket "arc-1234" exists in `.tickets/archive/`
- When the user runs `tq show 1234`
- Then the output contains "id: arc-1234"

### Scenario: Ambiguous ID across active and archived
- Given active ticket "abc-1234" exists
- And archived ticket "abc-5678" exists in `.tickets/archive/`
- When the user runs `tq show abc`
- Then the command exits non-zero
- And stderr contains "ambiguous ID 'abc' matches multiple tickets"

### Scenario: Active ticket wins over an identically-named archived ticket
- Given active ticket "dup-0001" exists with title "Active version"
- And a file `.tickets/archive/dup-0001.md` also exists with title "Archived version"
- When the user runs `tq show dup-0001`
- Then the output contains the title "Active version"

## Requirement: ID resolution across commands

Partial ID resolution SHALL work uniformly across all commands that accept ticket IDs, within the candidate ticket set relevant to that command. WHEN the command only reads a ticket's existing content -- `show`, `info`, `path`, `deps` -- the candidate set SHALL include both active and archived tickets. WHEN the command mutates a ticket or its relationships -- `create`, `edit`, `start`, `close`, `cancel`, `reopen`, including dep/link/parent targets passed to `create` or `edit` -- the candidate set SHALL include only active tickets.

### Scenario: Partial ID with edit --dep
- Given tickets "dep-aaaa" and "dep-bbbb" exist
- When the user runs `tq edit aaaa --dep bbbb`
- Then the command exits 0
- And ticket "dep-aaaa" has "dep-bbbb" in deps

### Scenario: Partial ID with edit --link
- Given tickets "link-cccc" and "link-dddd" exist
- When the user runs `tq edit cccc --link dddd`
- Then the command exits 0
- And ticket "link-cccc" has "link-dddd" in links

### Scenario: Edit's --dep target does not resolve an archive-only ID
- Given active ticket "act-0001" exists
- And archived ticket "arc-9999" exists in `.tickets/archive/`
- And no active ticket "arc-9999" exists
- When the user runs `tq edit act-0001 --dep 9999`
- Then the command exits non-zero
- And stderr contains "ticket '9999' not found"

### Scenario: Create's --dep target does not resolve an archive-only ID
- Given archived ticket "arc-8888" exists in `.tickets/archive/`
- And no active ticket "arc-8888" exists
- When the user runs `tq create "New ticket" --dep 8888`
- Then the command exits non-zero
- And stderr contains "ticket '8888' not found"

## Requirement: Resolution is scoped to a single store

Partial-ID resolution SHALL occur within exactly one store -- the store selected by `--dir`, `TICKETS_DIR`, or walk-up. The active/archived candidate-set distinction from "ID resolution across commands" applies within that single store; it never widens the candidate set to other stores. Recursive listing (`ls -r`) SHALL NOT resolve partial IDs across stores: it produces grouped output by iterating stores, performing no cross-store lookup. Because resolution never spans stores, an identical partial ID present in two different stores does not raise an ambiguity error -- each invocation resolves only against its selected store.

### Scenario: Resolution stays within the targeted store
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-1a2b"
- When the user runs `tq --dir packages/api show 1a2b`
- Then the output contains "id: api-1a2b"
- And the output does not contain "web-1a2b"

### Scenario: A partial matching only another store is not found
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq --dir packages/api show 3c4d`
- Then the command exits non-zero
- And stderr contains "not found"
</content>
</invoke>

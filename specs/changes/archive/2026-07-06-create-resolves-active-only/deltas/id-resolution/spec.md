# ID Resolution

## MODIFIED Requirements

### Requirement: ID resolution across commands

Partial ID resolution SHALL work uniformly across all commands that accept ticket IDs, within the candidate ticket set relevant to that command. WHEN the command only reads a ticket's existing content -- `show`, `info`, `path`, `deps` -- the candidate set SHALL include both active and archived tickets. WHEN the command mutates a ticket or its relationships -- `create`, `edit`, `start`, `close`, `cancel`, `reopen`, including dep/link/parent targets passed to `create` or `edit` -- the candidate set SHALL include only active tickets.

#### Scenario: Partial ID with edit --dep
- Given tickets "dep-aaaa" and "dep-bbbb" exist
- When the user runs `tq edit aaaa --dep bbbb`
- Then the command exits 0
- And ticket "dep-aaaa" has "dep-bbbb" in deps

#### Scenario: Partial ID with edit --link
- Given tickets "link-cccc" and "link-dddd" exist
- When the user runs `tq edit cccc --link dddd`
- Then the command exits 0
- And ticket "link-cccc" has "link-dddd" in links

#### Scenario: Edit's --dep target does not resolve an archive-only ID
- Given active ticket "act-0001" exists
- And archived ticket "arc-9999" exists in `.tickets/archive/`
- And no active ticket "arc-9999" exists
- When the user runs `tq edit act-0001 --dep 9999`
- Then the command exits non-zero
- And stderr contains "ticket '9999' not found"

#### Scenario: Create's --dep target does not resolve an archive-only ID
- Given archived ticket "arc-8888" exists in `.tickets/archive/`
- And no active ticket "arc-8888" exists
- When the user runs `tq create "New ticket" --dep 8888`
- Then the command exits non-zero
- And stderr contains "ticket '8888' not found"

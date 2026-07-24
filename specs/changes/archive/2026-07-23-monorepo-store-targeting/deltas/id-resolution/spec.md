# ID Resolution

## ADDED Requirements

### Requirement: Resolution is scoped to a single store

Partial-ID resolution SHALL occur within exactly one store -- the store selected by `--dir`, `TICKETS_DIR`, or walk-up. The active/archived candidate-set distinction from "ID resolution across commands" applies within that single store; it never widens the candidate set to other stores. Recursive listing (`ls -r`) SHALL NOT resolve partial IDs across stores: it produces grouped output by iterating stores, performing no cross-store lookup. Because resolution never spans stores, an identical partial ID present in two different stores does not raise an ambiguity error -- each invocation resolves only against its selected store.

#### Scenario: Resolution stays within the targeted store
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-1a2b"
- When the user runs `tq --dir packages/api show 1a2b`
- Then the output contains "id: api-1a2b"
- And the output does not contain "web-1a2b"

#### Scenario: A partial matching only another store is not found
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq --dir packages/api show 3c4d`
- Then the command exits non-zero
- And stderr contains "not found"

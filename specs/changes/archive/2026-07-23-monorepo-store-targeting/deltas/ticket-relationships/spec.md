# Ticket Relationships

## ADDED Requirements

### Requirement: Relationships are store-local

The system SHALL treat `deps`, `links`, and `parent` as references within a single store. WHEN a relationship target is supplied to `tq create` or `tq edit` (via `--dep`, `--link`, or `--parent`), the system SHALL resolve it only within the store being mutated -- the store selected by `--dir`, `TICKETS_DIR`, or walk-up. IF a supplied target exists only in a different store, the system SHALL reject it as not found and exit non-zero, mutating nothing. Dependency and parent cycle detection SHALL operate within a single store. Recursive listing (`ls -r`) SHALL NOT create, resolve, or traverse relationships between stores; it renders each store's relationship graph independently.

#### Scenario: Cross-store dependency target is rejected
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq --dir packages/web edit web-3c4d --dep api-1a2b`
- Then the command exits non-zero
- And stderr contains "not found"
- And "web-3c4d" has no dependency on "api-1a2b"

#### Scenario: Cross-store parent target is rejected
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- When the user runs `tq --dir packages/web edit web-3c4d --parent api-1a2b`
- Then the command exits non-zero
- And stderr contains "not found"

#### Scenario: Within-store relationships are unaffected
- Given `packages/web/.tickets/` contains "web-3c4d" and "web-5e6f"
- When the user runs `tq --dir packages/web edit web-3c4d --dep web-5e6f`
- Then the command exits 0
- And "web-3c4d" has "web-5e6f" in deps

# Ticket Store

## MODIFIED Requirements

### Requirement: Directory walking

The system SHALL locate the single store to operate on using the following precedence:
1. An explicit `--dir <path>` option, if supplied (see "Store targeting with --dir") -- the store is `<path>/.tickets/`. `--dir` always prevails when present.
2. Otherwise the `TICKETS_DIR` environment variable, if set -- the store is exactly that path.
3. Otherwise by walking up parent directories from the current working directory until a `.tickets/` directory is found.

Absent `--dir`, behavior is unchanged from prior versions.

### Scenario: Find tickets in current directory
- Given `.tickets/` exists in the current directory
- When the user runs `tq ls`
- Then the command exits 0

### Scenario: Find tickets in parent directory
- Given `.tickets/` exists in a parent directory
- And the user is in a subdirectory
- When the user runs `tq ls`
- Then the command exits 0 and finds the tickets

### Scenario: Find tickets in grandparent directory
- Given `.tickets/` exists two levels up
- And the user is in `src/components/ui`
- When the user runs `tq ls`
- Then the command exits 0 and finds the tickets

### Scenario: TICKETS_DIR takes priority over walk-up
- Given `.tickets/` exists in the current directory
- And `TICKETS_DIR` points to a different directory
- And no `--dir` option is supplied
- When the user runs `tq ls`
- Then the listing reflects the directory specified by `TICKETS_DIR`

### Scenario: Error when no tickets directory found (read command)
- Given no `.tickets/` directory exists in any parent
- When the user runs `tq show nonexistent`
- Then the command exits non-zero
- And stderr contains "no .tickets directory found"

### Scenario: Create initializes in current directory
- Given no `.tickets/` directory exists in any parent
- When the user runs `tq create "First ticket"`
- Then `.tickets/` is created in the current directory

## ADDED Requirements

### Requirement: Store targeting with --dir

The system SHALL accept a global `--dir <path>` option preceding the command word (e.g. `tq --dir packages/api ls`). WHEN `--dir <path>` is supplied, the target store SHALL be `<path>/.tickets/`; the system SHALL NOT walk up parent directories and SHALL ignore `TICKETS_DIR`. IF the target store does not exist, a read command SHALL exit non-zero with "no .tickets directory found", while `tq create` SHALL initialize it. The generated ticket ID prefix SHALL derive from the final path component of `<path>`, per the ID generation rule. `--dir` names a single store unless combined with `-r` (see "Recursive store discovery").

#### Scenario: --dir targets a sibling store for listing
- Given `packages/api/.tickets/` contains ticket "api-1a2b"
- And `packages/web/.tickets/` contains ticket "web-3c4d"
- And the current working directory is the monorepo root
- When the user runs `tq --dir packages/api ls`
- Then the output contains "api-1a2b"
- And the output does not contain "web-3c4d"

#### Scenario: --dir create initializes the store at the path
- Given `packages/api/` exists with no `.tickets/` directory
- When the user runs `tq --dir packages/api create "First"`
- Then `packages/api/.tickets/` is created
- And the new ticket file is written under `packages/api/.tickets/`

#### Scenario: --dir create derives the ID prefix from the path
- Given `packages/api/` exists
- When the user runs `tq --dir packages/api create "First"`
- Then the printed ID matches the pattern `api-[a-f0-9]{4}`

#### Scenario: --dir prevails over TICKETS_DIR when both are set
- Given `TICKETS_DIR` points to `other/.tickets/` containing "oth-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq --dir packages/api ls`
- Then the output contains "api-1a2b"
- And the output does not contain "oth-0001"

#### Scenario: --dir with a missing store errors on a read command
- Given `packages/api/` exists with no `.tickets/` directory
- When the user runs `tq --dir packages/api ls`
- Then the command exits non-zero
- And stderr contains "no .tickets directory found"

### Requirement: Recursive store discovery

WHEN a command runs in recursive mode (`ls -r`), the system SHALL discover every `.tickets/` directory at or below the root, where the root is the `--dir <path>` if supplied, otherwise the current working directory. Discovery proceeds downward only: the system SHALL NOT walk up from the root (unlike the default single-store resolution). The root's own `.tickets/` SHALL be included when present. The system SHALL NOT descend into a discovered `.tickets/` directory to look for further stores (a store's `archive/` subdirectory is never a separate store). The system SHALL skip version-control and dependency directories (e.g. `.git`, `node_modules`) while walking. Discovered stores SHALL be ordered lexicographically by their path relative to the root. Recursive mode SHALL ignore `TICKETS_DIR` (which names a single store).

#### Scenario: Discovers nested stores under the root
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- And the current working directory is the monorepo root
- When the user runs `tq ls -r`
- Then the output contains "api-1a2b"
- And the output contains "web-3c4d"

#### Scenario: Includes the root's own store
- Given `.tickets/` at the root contains "root-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the output contains "root-0001"
- And the output contains "api-1a2b"

#### Scenario: Skips VCS and dependency directories
- Given `node_modules/pkg/.tickets/` contains "dep-9999"
- And `.git/.tickets/` contains "git-9999"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the output contains "api-1a2b"
- And the output does not contain "dep-9999"
- And the output does not contain "git-9999"

#### Scenario: A store's archive is not treated as a separate store
- Given `packages/api/.tickets/` contains active "api-1a2b"
- And `packages/api/.tickets/archive/` contains archived "api-0000"
- When the user runs `tq ls -r`
- Then "packages/api" appears exactly once as a store heading

#### Scenario: Recursive mode does not walk up from the root
- Given `.tickets/` exists at the monorepo root
- And `packages/web/` contains no `.tickets/` and no nested stores
- And the current working directory is `packages/web`
- When the user runs `tq ls -r`
- Then the output is empty

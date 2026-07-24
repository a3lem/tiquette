# Ticket Store

Covers ticket directory resolution, file format, and ID generation.

## Requirement: Directory walking

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

## Requirement: Ticket file format

Tickets SHALL be stored as markdown files with YAML frontmatter in `.tickets/`. The filename is `<id>.md`. The `status` field SHALL hold one of `open`, `in_progress`, `closed`, `canceled`. The schema SHALL NOT include a `resolution` field. Nullable fields (`assignee`, `parent`, `xref`) SHALL be omitted from the frontmatter when their value is null. All other fields are always present.

### Scenario: File structure
- Given a ticket is created with default values
- Then the file contains YAML frontmatter between `---` delimiters
- And the title is a `# heading` below the frontmatter
- And the frontmatter includes: id, status, type, priority, deps, links, tags, created
- And `assignee`, `parent`, `xref` are absent (not written as `null`)
- And no `resolution` field is present

### Scenario: Nullable fields present when non-null
- Given a ticket is created with `--assignee Alice` and `--xref gh-123`
- Then the frontmatter contains `assignee: Alice`
- And the frontmatter contains `xref: gh-123`

### Scenario: Nullable fields absent after being cleared
- Given ticket "t-001" has `assignee: Alice`
- When the user runs `tq edit t-001 --unset assignee`
- Then the frontmatter does not contain an `assignee` line

### Scenario: Resolution field never written
- Given ticket "t-001" exists
- When the user runs `tq close t-001` and then `tq cancel t-001` after `tq reopen t-001`
- Then no version of the file contains a `resolution` line

### Scenario: Closed status uses 'closed', not 'completed'
- Given ticket "t-001" exists with status `open`
- When the user runs `tq close t-001`
- Then the frontmatter contains `status: closed`
- And the frontmatter does not contain `status: completed`

## Requirement: ID generation

The system SHALL generate ticket IDs using an abbreviation of the project directory name as prefix and a random hex suffix, in the format `<prefix>-<4hex>`.

The prefix SHALL be derived as follows:
- Tokenize the directory name on `-` and `_`.
- If a single token results, take the first 4 characters of that token.
- Otherwise take the first letter of each token (up to 4); if fewer than 4 letters result, append the trailing characters of the last token until 4 characters are reached.
- The prefix SHALL be lowercase and at most 4 characters.
- The 4th character SHOULD preferably be a consonant. If it is a vowel (a, e, i, o, u):
  - For single-token names, scan the remaining characters of the token; for multi-token names that filled from the last token, scan the characters of the last token preceding the filled tail (closest-to-tail first). The first consonant encountered replaces the 4th character.
  - If no consonant is found and the 3rd character is a consonant, drop the 4th character and use a 3-character prefix.
  - If no consonant is found and the 3rd character is also a vowel, keep the original vowel as the 4th character.

### Scenario: Single-word directory
- Given the project directory is named "tiquette"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `tiqu-[a-f0-9]{4}`

### Scenario: Multi-word directory with four or more tokens
- Given the project directory is named "my-cool-awesome-project"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `mcap-[a-f0-9]{4}`

### Scenario: Multi-word directory with fewer than four tokens
- Given the project directory is named "ai-ml-research"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `amrh-[a-f0-9]{4}`

### Scenario: Vowel ending replaced by next consonant in single-token name
- Given the project directory is named "tiquette"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `tiqt-[a-f0-9]{4}`

### Scenario: Vowel ending replaced by consonant scanned back in multi-token fill
- Given the project directory is named "ai-ml-data"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `amdt-[a-f0-9]{4}`

### Scenario: Falls back to 3-char prefix when no consonant available and char 3 is consonant
- Given the project directory is named "strae"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `str-[a-f0-9]{4}`

### Scenario: Keeps vowel ending when char 3 is also a vowel
- Given the project directory is named "stoau"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `stoa-[a-f0-9]{4}`

## Requirement: Timestamp format

The system SHALL write all ticket timestamps -- the `created` frontmatter field and every Notes-section entry -- in the format `YYYY-MM-DDTHH:MMZ` (minute precision, Zulu suffix). The system SHALL accept on read both this format and the legacy ISO 8601 microsecond-plus-offset format (e.g. `2026-04-29T12:48:50.906383+00:00`). Read, edit, and status-transition operations SHALL NOT rewrite existing ticket files to migrate their timestamp format; bulk migration is the exclusive job of `tq autofix` (see `ticket-autofix`).

### Scenario: New ticket writes new format
- Given a clean tickets directory
- When the user runs `tq create "New ticket"`
- Then the `created` frontmatter value matches the pattern `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`

### Scenario: New note writes new format
- Given a ticket "t-001" exists
- When the user runs `tq edit t-001 --note "hello"`
- Then the appended Notes entry begins with a timestamp matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z`

### Scenario: Legacy timestamps are read without error
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq show <id>`
- Then the command exits 0
- And the displayed creation time reflects the legacy timestamp

### Scenario: Legacy ticket is not rewritten on read
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq show <id>`
- Then the file on disk is unchanged

### Scenario: Editing a legacy ticket preserves its created timestamp
- Given a ticket file whose `created` field is `2026-04-29T12:48:50.906383+00:00`
- When the user runs `tq edit <id> --priority 1`
- Then the `created` field remains `2026-04-29T12:48:50.906383+00:00`
- And any newly written Notes entries use the new format

## Requirement: Store targeting with --dir

The system SHALL accept a global `--dir <path>` option preceding the command word (e.g. `tq --dir packages/api ls`). WHEN `--dir <path>` is supplied, the target store SHALL be `<path>/.tickets/`; the system SHALL NOT walk up parent directories and SHALL ignore `TICKETS_DIR`. IF the target store does not exist, a read command SHALL exit non-zero with "no .tickets directory found", while `tq create` SHALL initialize it. The generated ticket ID prefix SHALL derive from the final path component of `<path>`, per the ID generation rule. `--dir` names a single store unless combined with `-r` (see "Recursive store discovery").

### Scenario: --dir targets a sibling store for listing
- Given `packages/api/.tickets/` contains ticket "api-1a2b"
- And `packages/web/.tickets/` contains ticket "web-3c4d"
- And the current working directory is the monorepo root
- When the user runs `tq --dir packages/api ls`
- Then the output contains "api-1a2b"
- And the output does not contain "web-3c4d"

### Scenario: --dir create initializes the store at the path
- Given `packages/api/` exists with no `.tickets/` directory
- When the user runs `tq --dir packages/api create "First"`
- Then `packages/api/.tickets/` is created
- And the new ticket file is written under `packages/api/.tickets/`

### Scenario: --dir create derives the ID prefix from the path
- Given `packages/api/` exists
- When the user runs `tq --dir packages/api create "First"`
- Then the printed ID matches the pattern `api-[a-f0-9]{4}`

### Scenario: --dir prevails over TICKETS_DIR when both are set
- Given `TICKETS_DIR` points to `other/.tickets/` containing "oth-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq --dir packages/api ls`
- Then the output contains "api-1a2b"
- And the output does not contain "oth-0001"

### Scenario: --dir with a missing store errors on a read command
- Given `packages/api/` exists with no `.tickets/` directory
- When the user runs `tq --dir packages/api ls`
- Then the command exits non-zero
- And stderr contains "no .tickets directory found"

## Requirement: Recursive store discovery

WHEN a command runs in recursive mode (`ls -r`), the system SHALL discover every `.tickets/` directory at or below the root, where the root is the `--dir <path>` if supplied, otherwise the current working directory. Discovery proceeds downward only: the system SHALL NOT walk up from the root (unlike the default single-store resolution). The root's own `.tickets/` SHALL be included when present. The system SHALL NOT descend into a discovered `.tickets/` directory to look for further stores (a store's `archive/` subdirectory is never a separate store). The system SHALL skip version-control and dependency directories (e.g. `.git`, `node_modules`) while walking. Discovered stores SHALL be ordered lexicographically by their path relative to the root. Recursive mode SHALL ignore `TICKETS_DIR` (which names a single store).

### Scenario: Discovers nested stores under the root
- Given `packages/api/.tickets/` contains "api-1a2b"
- And `packages/web/.tickets/` contains "web-3c4d"
- And the current working directory is the monorepo root
- When the user runs `tq ls -r`
- Then the output contains "api-1a2b"
- And the output contains "web-3c4d"

### Scenario: Includes the root's own store
- Given `.tickets/` at the root contains "root-0001"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the output contains "root-0001"
- And the output contains "api-1a2b"

### Scenario: Skips VCS and dependency directories
- Given `node_modules/pkg/.tickets/` contains "dep-9999"
- And `.git/.tickets/` contains "git-9999"
- And `packages/api/.tickets/` contains "api-1a2b"
- When the user runs `tq ls -r`
- Then the output contains "api-1a2b"
- And the output does not contain "dep-9999"
- And the output does not contain "git-9999"

### Scenario: A store's archive is not treated as a separate store
- Given `packages/api/.tickets/` contains active "api-1a2b"
- And `packages/api/.tickets/archive/` contains archived "api-0000"
- When the user runs `tq ls -r`
- Then "packages/api" appears exactly once as a store heading

### Scenario: Recursive mode does not walk up from the root
- Given `.tickets/` exists at the monorepo root
- And `packages/web/` contains no `.tickets/` and no nested stores
- And the current working directory is `packages/web`
- When the user runs `tq ls -r`
- Then the output is empty

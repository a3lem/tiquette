# Ticket Store

Covers ticket directory resolution, file format, and ID generation.

## Requirement: Directory walking

The system SHALL find the `.tickets/` directory by walking up parent directories from the current working directory. The `TICKETS_DIR` environment variable, if set, takes priority.

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

### Scenario: TICKETS_DIR takes priority
- Given `.tickets/` exists in the current directory
- And `TICKETS_DIR` points to a different directory
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

Tickets SHALL be stored as markdown files with YAML frontmatter in `.tickets/`. The filename is `<id>.md`. The `status` field SHALL hold one of `open`, `in_progress`, `completed`, `canceled`. The schema SHALL NOT include a `resolution` field. Nullable fields (`assignee`, `parent`, `xref`) SHALL be omitted from the frontmatter when their value is null. All other fields are always present.

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
- When the user runs `tq assign t-001` (clears assignee)
- Then the frontmatter does not contain an `assignee` line

### Scenario: Resolution field never written
- Given ticket "t-001" exists
- When the user runs `tq close t-001` and then `tq cancel t-001` after `tq reopen t-001`
- Then no version of the file contains a `resolution` line

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

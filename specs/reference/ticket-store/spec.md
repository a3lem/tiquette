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

Tickets SHALL be stored as markdown files with YAML frontmatter in `.tickets/`. The filename is `<id>.md`.

### Scenario: File structure
- Given a ticket is created
- Then the file contains YAML frontmatter between `---` delimiters
- And the title is a `# heading` below the frontmatter
- And the frontmatter includes: id, status, type, priority, assignee, deps, links, parent, tags, ref, resolution, created

## Requirement: ID generation

The system SHALL generate ticket IDs using the directory name as prefix and a random hex suffix, in the format `<prefix>-<4hex>`.

### Scenario: ID format
- Given the project directory is named "myproj"
- When the user runs `tq create "Test"`
- Then the printed ID matches the pattern `myproj-[a-f0-9]{4}`

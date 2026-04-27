# Ticket Store

## MODIFIED Requirements

### Requirement: Ticket file format

Tickets SHALL be stored as markdown files with YAML frontmatter in `.tickets/`. The filename
is `<id>.md`. Nullable fields (`assignee`, `parent`, `xref`, `resolution`) SHALL be omitted
from the frontmatter when their value is null. All other fields are always present.

#### Scenario: File structure
- Given a ticket is created with default values
- Then the file contains YAML frontmatter between `---` delimiters
- And the title is a `# heading` below the frontmatter
- And the frontmatter includes: id, status, type, priority, deps, links, tags, created
- And `assignee`, `parent`, `xref`, `resolution` are absent (not written as `null`)

#### Scenario: Nullable fields present when non-null
- Given a ticket is created with `--assignee Alice` and `--xref gh-123`
- Then the frontmatter contains `assignee: Alice`
- And the frontmatter contains `xref: gh-123`

#### Scenario: Nullable fields absent after being cleared
- Given ticket "t-001" has `assignee: Alice`
- When the user runs `tq assign t-001` (clears assignee)
- Then the frontmatter does not contain an `assignee` line

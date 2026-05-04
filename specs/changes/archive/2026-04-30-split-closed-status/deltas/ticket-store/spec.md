# Ticket Store

## MODIFIED Requirements

### Requirement: Ticket file format

Tickets SHALL be stored as markdown files with YAML frontmatter in `.tickets/`. The filename is `<id>.md`. The `status` field SHALL hold one of `open`, `in_progress`, `completed`, `canceled`. The schema SHALL NOT include a `resolution` field. Nullable fields (`assignee`, `parent`, `xref`) SHALL be omitted from the frontmatter when their value is null. All other fields are always present.

#### Scenario: File structure
- Given a ticket is created with default values
- Then the file contains YAML frontmatter between `---` delimiters
- And the title is a `# heading` below the frontmatter
- And the frontmatter includes: id, status, type, priority, deps, links, tags, created
- And `assignee`, `parent`, `xref` are absent (not written as `null`)
- And no `resolution` field is present

#### Scenario: Nullable fields present when non-null
- Given a ticket is created with `--assignee Alice` and `--xref gh-123`
- Then the frontmatter contains `assignee: Alice`
- And the frontmatter contains `xref: gh-123`

#### Scenario: Nullable fields absent after being cleared
- Given ticket "t-001" has `assignee: Alice`
- When the user runs `tq assign t-001` (clears assignee)
- Then the frontmatter does not contain an `assignee` line

#### Scenario: Resolution field never written
- Given ticket "t-001" exists
- When the user runs `tq close t-001` and then `tq cancel t-001` after `tq reopen t-001`
- Then no version of the file contains a `resolution` line

# CLI Design

Options come after positional arguments.

```
tq - minimal ticket system with dependency tracking

Usage: tq <command> [args]

Lifecycle:
  create [title] [options]   Create ticket, prints ID
    -d, --description        Body content (markdown below frontmatter)
    -t, --type               Type (bug|feature|task|epic|chore) [default: task]
    -p, --priority           Priority 0-4, 0=highest [default: 2]
    -a, --assignee           Assignee [default: null]
    --ref                    External reference (e.g., gh-123, JIRA-456)
    --parent                 Parent ticket ID
    --tags                   Comma-separated tags (e.g., --tags ui,backend,urgent)
    --deps                   Comma-separated blocker IDs
  start <id>                 Set status to in_progress
  close <id>                 Set status to closed (resolution: completed)
  cancel <id>                Set status to closed (resolution: canceled)
  reopen <id>                Set status to open (clears resolution)

Relationships:
  dep <id> <dep-id> [dep-id...]
                             Add dependency (id depends on dep-id(s): it is blocked by dep-id(s)).
                             Rejects with non-zero exit if cycle detected
  undep <id> <dep-id> [dep-id...]
                             Remove blocking dependency
  nest <child-id> [child-id...] <parent-id>
                             Set parent (last arg is destination, like mv)
  unnest <id> [id...]        Remove from parent
  link <id> <id> [id...]     Associate tickets (symmetric, informational)
  unlink <id> <id> [id...]   Remove association(s)

Fields:
  assign <id> <assignee>     Set assignee
  unassign <id>              Clear assignee
  change-prio <id> <priority>   Update priority: 0-4, 0=highest
  change-type <id> <type>       Change ticket type
  tag <id> <tag,...>          Append tag(s)
  untag <id> <tag,...>        Remove tag(s)
  set-ref <id> <ref>          Set external reference (e.g., gh-123, JIRA-456)
  unset-ref <id>             Clear external reference

Content:
  describe <id> [text]       Set/replace description section
  add-note <id> [text]       Append timestamped note (or pipe via stdin)

Query:
  show <id> [--json]           Display ticket (frontmatter + body)
  info <id> [--json]           Frontmatter + computed relationships (no body)
  path <id>                    Print file path for direct editing
  show-deps <id> [--full]      Show dependency tree (--full disables dedup)
  ls [options]                 List tickets [default: open + in_progress]
    --status X                 Filter by status (open|in_progress|closed)
    --ready                    Actionable: no unresolved deps or open children
    --blocked                  Has unresolved deps or open children
    --completed                Resolution = completed (implies --status closed)
    --canceled                 Resolution = canceled (implies --status closed)
    --assignee X               Filter by assignee
    --tag X                    Filter by tag
    --type X                   Filter by type
    --sort X                   Sort by field (priority|mtime) [default: priority]
    --limit N                  Limit results
    --jsonl                    Output as JSON Lines (one object per ticket)
  tags                         List all tags with counts, sorted by frequency
  archive                      Move closed/canceled tickets to archive directory

Plumbing:
  super <cmd> [args]         Bypass plugins, run built-in command directly
```

## Ticket File Format

Tickets are markdown files in `.tickets/` with YAML frontmatter:

```markdown
---
id: proj-a1b2
status: open
type: task
priority: 2
assignee:
deps: []
links: []
parent:
tags: []
ref:
resolution:
created: 2026-03-30T12:00:00Z
---
# Ticket title

## Description

Body content goes here.

## Notes

- [2026-03-30T12:00:00Z] First note
- [2026-03-30T13:00:00Z] Second note
```

### Key design decisions

- **Title** is the `# heading`, not a YAML field
- **Description** is the `## Description` section (set by `-d`/`--description` or `describe` command)
- **Notes** are append-only timestamped lines in the `## Notes` section
- **Status** values: `open`, `in_progress`, `closed`
- **Resolution** (only when status=closed): `completed`, `canceled`
- **ID format**: directory-name prefix + random suffix (e.g., `proj-a1b2`)
- **Partial ID matching**: `tq show a1b` matches `proj-a1b2`

### Behavioral rules

- `close` rejects if ticket has open children (exit non-zero, lists open children)
- `close` prints notification when closing last open child of a parent
- `dep` validates for cycles on write (rejects and rolls back)
- `ls --ready`: open/in_progress tickets with no unresolved deps AND no open children
- `ls --blocked`: open/in_progress tickets with unresolved deps OR open children
- A parent with open children is implicitly blocked (even without explicit deps)

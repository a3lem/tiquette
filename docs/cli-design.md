# CLI Design

## Command Reference

```
tq - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Lifecycle:
  create [title]                        Create ticket, prints ID
  start <id>                            Set status to in_progress
  close <id>                            Close as completed
  cancel <id>                           Close as canceled
  reopen <id>                           Reopen (clears resolution)
  archive                               Move closed tickets to archive

Relationships:
  dep <id> <dep-id>...                  Add blocking dependency
  undep <id> <dep-id>...                Remove dependency
  nest <child>... <parent>              Set parent
  unnest <id>...                        Remove from parent
  link <id> <id>...                     Associate tickets (symmetric)
  unlink <id> <id>...                   Remove association(s)
  deps <id>                             Show dependency tree
  links                                 List all linked pairs

Fields:
  assign <id> [assignee]                Set or clear assignee
  change-prio <id> <priority>           Update priority (0-4)
  change-type <id> <type>               Change ticket type
  tag <id> <tag> [tag...]                Append tag(s)
  untag <id> <tag> [tag...]              Remove tag(s)
  xref <id> [xref]                      Set or clear external reference
  tags                                  List all tags with counts

Content:
  describe <id> <text>                  Set/replace description
  add-note <id> <text>                  Append timestamped note

View:
  ls [options]                          List tickets
  show <id>                             Display ticket
  info <id>                             Frontmatter + relationships
  path <id>                             Print file path
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
xref:
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

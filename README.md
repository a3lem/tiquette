# tiquette

Minimal file-based ticket system with dependency tracking. Tickets are markdown files with YAML frontmatter, stored in `.tickets/` alongside your code.

```
uv tool install git+https://github.com/a3lem/tiquette
```

## Usage

```
tq - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Frequently Used
---------------
  ls --ready                            List open tickets that are not blocked
  show <id>                             Display ticket (meta + body)
  create [title]                        Create new ticket (prints ID)
  start <id>                            Set ticket status to in_progress
  close <id>                            Close ticket as completed

Commands
--------

Lifecycle:
  create [title] [options]              Create ticket, prints ID
    -d, --description TEXT              Body content (markdown below frontmatter)
    -t, --type TYPE                     bug|feature|task|epic|chore [default: task]
    -p, --priority N                    0-4, 0=highest [default: 2]
    -A, --assignee NAME                 Assignee [default: null]
    --xref REF                          External reference (e.g., gh-123, JIRA-456)
    --parent ID                         Parent ticket ID
    --tag TAG                           Tag (repeat for multiple)
    --dep ID                            Blocker ID (repeat for multiple)
  start <id>                            Set status to in_progress
  close <id> [-f]                       Set status to completed
                                        -f/--force cascades through open descendants
  cancel <id> [-f]                      Set status to canceled
                                        -f/--force cascades through open descendants
  reopen <id>                           Set status to open
  archive                               Move completed and canceled tickets to archive directory

Relationships:
  dep <id> <dep-id> [dep-id...]         Add dependency (id is blocked by dep-ids)
  undep <id> <dep-id> [dep-id...]       Remove blocking dependency
  nest <child> [child...] <parent>      Set parent (last arg is destination, like mv)
  unnest <id> [id...]                   Remove from parent
  link <id> <id> [id...]                Associate tickets (symmetric, informational)
  unlink <id> <id> [id...]              Remove association(s)
  deps <id> [--full]                    Show dependency tree (--full disables dedup)
  links                                 List all linked pairs across tickets

Fields:
  assign <id> [assignee]                Set or clear assignee
  change-prio <id> <priority>           Update priority: 0-4, 0=highest
  change-type <id> <type>               Change ticket type
  tag <id> <tag> [tag...]               Append tag(s)
  untag <id> <tag> [tag...]             Remove tag(s)
  xref <id> [xref]                      Set or clear external reference
  tags                                  List all tags with counts, sorted by frequency

Content:
  describe <id> <text>                  Set/replace description section
  add-note <id> <text>                  Append timestamped note (or pipe via stdin)

View:
  ls [options]                          List tickets [default: all statuses]
    -s, --status X                      Filter: open|in_progress|completed|canceled
    --ready                             Actionable: no unresolved deps or open children
    --blocked                           Has unresolved deps or open children
    --assignee NAME                     Filter by assignee
    --tag TAG                           Filter by tag
    --type TYPE                         Filter by type
    --sort FIELD                        Sort: priority|mtime [default: priority]
    --limit N                           Limit results
    --jsonl                             Output as JSON Lines (one object per ticket)
  show <id> [--json]                    Display ticket (frontmatter + body)
  info <id> [--json]                    Frontmatter + computed relationships (no body)
  path <id>                             Print file path for direct editing

Maintenance:
  validate                              Check all tickets for referential integrity
  autofix                               Update tickets to be consistent with current behavior
```

## License

MIT

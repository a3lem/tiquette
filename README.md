<!-- This file is managed by `shablon`. Do not edit directly. Instead, modify template in .shablon/templates/. -->

# tiquette

Minimal file-based ticket system with dependency tracking. Tickets are markdown files with YAML frontmatter, stored in `.tickets/` alongside your code.

```
uv tool install git+https://github.com/a3lem/tiquette
```

## Usage

```
tq (tiquette) - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Frequently Used
---------------
  ls --ready                            List open tickets that are not blocked
  show <id>                             Display ticket (meta + body)
  create <title> [field-options]        Create new ticket (prints ID)
  edit <id> [field-options]             Modify ticket fields
  start <id>                            Set ticket status to in_progress
  close <id>                            Set status to closed (ticket is complete)

Commands
--------
(<id> / ID below always refers to a ticket ID)

Lifecycle:
  create <title> [field-options]        Create ticket, prints ID
    -d, --description TEXT              Description (markdown body)
    -t, --type TYPE                     bug|feature|task|epic|chore [default: task]
    -p, --priority N                    0-4, 0=highest [default: 2]
    -A, --assignee NAME                 Assignee [default: null]
        --xref REF                      External reference, e.g. gh-123
        --parent ID                     Nest under parent (makes this ticket a child of ID)
        --tag TAG                       Add tag (repeatable)
        --dep ID                        Register blocking dependency on other ticket (repeatable)
        --link ID                       Associate ticket (repeatable, symmetric)
        --note TEXT                     Append timestamped note (repeatable)

  edit <id> [field-options]             Modify ticket fields
                                        Accepts all create field-options (above), plus:
        --title TEXT                    Rename ticket
        --untag TAG                     Remove tag (repeatable)
        --undep ID                      Remove blocker (repeatable)
        --unlink ID                     Remove association (repeatable)
        --unset FIELD                   Clear a single-value field (repeatable)
                                        FIELD in {parent, xref, assignee}
                                        Setting and unsetting the same field in
                                        the same call is an error.

  start <id>                            Set status to in_progress
  close <id> [-f]                       Set status to closed (ticket is complete)
                                        -f/--force cascades through open descendants
  cancel <id> [-f]                      Set status to canceled
                                        -f/--force cascades through open descendants
  reopen <id>                           Set status to open
  archive                               Move closed and canceled tickets to archive

View:
  ls [options]                          List tickets [default: all statuses]
    -s, --status X                      Filter: open|in_progress|closed|canceled
    --ready                             Actionable: no unresolved deps or open children
    --blocked                           Has unresolved deps or open children
    -a, --all                           Include archived tickets
    --archived                          Show only archived tickets
    --tag TAG                           Filter by tag
    --type TYPE                         Filter by type
    -A, --assignee NAME                 Filter by assignee
    --parent ID                         Show ticket and its descendants as a tree
    --dep ID                            Show tickets that directly depend on ID (flat list)
    --sort FIELD                        Sort: priority|mtime [default: priority]
    --limit N                           Limit results
    --jsonl                             Output as JSON Lines (one object per ticket)
  show <id> [--json]                    Display ticket (frontmatter + body)
  info <id> [--json]                    Frontmatter + computed relationships (no body)
  path <id>                             Print file path for direct editing
  deps <id> [--full]                    Show dependency tree (--full disables dedup)
  links                                 List all linked pairs across tickets
  tags                                  List all tags with counts, sorted by frequency

Maintenance:
  validate                              Check all tickets for referential integrity
  autofix                               Update tickets to be consistent with current behavior

Examples
--------
  tq create 'Fix parser dropping trailing commas' -d 'parser.py:142' -t bug -p 1
  tq edit abf1 --tag urgent --untag stale -p 0 --note 'customer escalation'
  tq edit abf1 --parent 9zk2 --dep 4mn8
  tq ls --ready --tag backend --sort priority
```

## License

MIT

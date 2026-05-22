---
name: tiquette
description: >
  This skill should be used when the user asks to "create a ticket", "add a task",
  "track an issue", "manage dependencies", "show blocked tickets", "list open tickets",
  "close a ticket", "cancel a ticket", "add notes to a ticket", "link tickets",
  "what's ready to work on", "what's blocking", "break down an epic",
  or any task management operation using the `tq` CLI. Also triggers when the user
  mentions "tq", "tiquette", "ticket system", ".tickets", or asks about project task organization.
metadata:
  author: plugin_src
  version: 0.2.3
  note: Generated. Do not modify
---

# tq – CLI Ticket System

`tq` is a file-based issue tracker. Tickets are markdown with YAML frontmatter in `.tickets/`, committed alongside code. Designed for humans and AI agents.

Use `Bash(tq ...)` for project work tracking instead of `Todo*(...)`. Each `tq` call should be a separate Bash tool invocation so the user sees each step.

**Before starting any multi-step task**, check for existing tickets:

```bash
tq ls --ready       # actionable work
tq ls --blocked     # stuck work
tq ls --jsonl | jq 'select(.title | test("keyword"; "i"))'   # search by title
```

If a matching ticket exists, use it. If not, create one. Trivial one-shot changes don't need a ticket.

## Core Concepts

| Concept | Details |
|---------|---------|
| **IDs** | `prefix-hexsuffix` (e.g., `proj-a1b2`). Prefix = directory name. Partial IDs work everywhere. |
| **Files** | `.tickets/<id>.md` – YAML frontmatter + markdown body |
| **Statuses** | `open` → `in_progress` → `closed` (via `start`/`close`/`cancel`) |
| **Priority** | 0–4, 0 is highest. Default 2. |
| **Types** | `bug`, `feature`, `task`, `epic`, `chore`. Default `task`. |
| **Terminal status** | `closed` (via `close`) or `canceled` (via `cancel`) |
| **Dependencies** | Directed: "A depends on B" means B blocks A |
| **Links** | Symmetric, informational only (don't affect blocking) |

## CLI Reference

```
tq (tiquette) - a minimal ticket system with dependency tracking

Usage: tq <command> [args]

Frequently Used
---------------
  ls --ready                            List open tickets that are not blocked
  show <id>                             Display ticket (meta + body)
  create <title> [field-options]        Create new ticket (prints ID)
  edit <id> [field-options]             Modify ticket fields
  start <id>...                         Set ticket status to in_progress
  close <id>...                         Set status to closed (ticket is complete)

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

  start <id>...                         Set status to in_progress
  close <id>... [-f]                    Set status to closed (ticket is complete)
                                        -f/--force cascades through open descendants
                                        Multiple IDs: validated up front, all-or-nothing
  cancel <id>... [-f]                   Set status to canceled
                                        -f/--force cascades through open descendants
                                        Multiple IDs: validated up front, all-or-nothing
  reopen <id>...                        Set status to open
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
  prune [filters] [-y]                  Permanently delete archived tickets by filter
    -s, --status X                      Filter: closed|canceled
    --type TYPE                         Filter by type
    --before YYYY-MM-DD                 Match tickets created strictly before date
    -y, --yes                           Actually delete (default: dry run)
                                        At least one filter required

Examples
--------
  tq create 'Fix parser dropping trailing commas' -d 'parser.py:142' -t bug -p 1
  tq edit abf1 --tag urgent --untag stale -p 0 --note 'customer escalation'
  tq edit abf1 --parent 9zk2 --dep 4mn8
  tq ls --ready --tag backend --sort priority
```

## Things --help Won't Tell You

### Always write a description

Pass `-d "..."` on `tq create` for anything that will outlive the current task. Titles get terse fast -- "fix parser bug" is meaningless a week later. The description is the only place to anchor the ticket in its original context: what prompted it, what the user actually said, links to relevant files or PRs, what "done" looks like.

```bash
tq create "Fix parser dropping trailing commas" \
  -d "User reported on 2026-05-04 that comma-trailing JSON5 inputs raise. See parser.py:142. Done = round-trip test passes for trailing commas in arrays and objects."
```

The only time it's safe to skip `-d`: short-lived subtasks created during a single session where the parent ticket or surrounding conversation already carries the context, and you expect to close them the same day.

### Editing fields not covered by a command

To change a ticket's title, edit `.tickets/<id>.md` directly. Use `tq path <id>` to get the file path, then Read and Edit.

### Ready vs blocked logic

**Ready** = open/in_progress AND no unresolved deps AND no open children.
**Blocked** = open/in_progress AND (has unresolved deps OR has open children).

Parents are implicitly blocked by open children, even without explicit deps. This is transitive – grandparents are blocked too.

### Any ticket type can have children

Parenting is not restricted by type. A `task` can have subtasks, a `feature` can have child bugs, etc. By convention `epic` groups `feature`s, but that's a convention, not a constraint -- reach for `epic` only when you actually want an epic-sized container, not just because a ticket has children.

### Parenting via `tq edit`

There is no `tq nest`. Move a ticket under a parent with `tq edit <child> --parent <parent>`. For multiple children, run one `edit` per child (or a shell loop). Clear a parent with `tq edit <child> --unset parent`.

### No assignee default

`tq` does not auto-assign to the git user. Always pass `-A` explicitly when creating or editing.

### Closing or cancelling a parent

Both `tq close` and `tq cancel` reject a ticket with open descendants. Pass `-f` / `--force` to cascade through the subtree -- every open descendant is closed (or cancelled) along with the parent. Already-terminal descendants are left alone. Each affected ID is printed on its own line in write order.

### Checkbox glyphs in `tq ls`

`[ ]` open, `[/]` in_progress, `[x]` closed, `[~]` canceled. The tilde is a deliberate strikethrough cue -- match both `[x]` and `[~]` if you're parsing for "terminal".

### Listing shows tree context

When a filtered ticket has a parent outside the result set, the parent appears as a context row (shown but not counted against `--limit`). `--ready` and `--blocked` skip context parents.

### JSON output

`ls --jsonl` emits one JSON object per line. Pipe to `jq` for filtering:

```bash
tq ls --jsonl | jq 'select(.priority == 0)'
tq ls --jsonl | jq 'select(.tags | index("api"))'
```

### Plugin system

External executables named `tq-<cmd>` or `tiquette-<cmd>` in PATH are invoked as subcommands. `tq super <cmd>` bypasses plugins.

## Workflow Patterns

### Starting work

```bash
tq ls --ready                  # what's actionable?
tq start <id>                  # claim it
# ... do the work ...
tq close <id>                  # done
```

### Breaking down an epic

```bash
epic=$(tq create "Auth system" -t epic -A claude)
schema=$(tq create "Design auth schema" --parent "$epic" -A claude)
oauth=$(tq create "Implement OAuth" --parent "$epic" --dep "$schema" -A claude)
```

(Or set the dep afterwards: `tq edit "$oauth" --dep "$schema"`.)

### Checking progress

```bash
tq ls --blocked                # what's stuck?
tq deps <epic-id>              # visualize dependency graph
tq ls --status closed --limit 5  # recently finished
```

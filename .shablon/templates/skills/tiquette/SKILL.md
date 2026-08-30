---
name: tiquette
description: >
  This skill should be used when the user asks to "create a ticket", "add a task",
  "track an issue", "manage dependencies", "show blocked tickets", "list open tickets",
  "close a ticket", "cancel a ticket", "add notes to a ticket", "link tickets",
  "what's ready to work on", "what's blocking", "break down an epic",
  or any task management operation using the `tq` CLI. Also triggers when the user
  mentions "tq", "tiquette", "ticket system", ".tickets", or asks about project task organization.
{% include "_includes/meta.yaml" -%}
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
{{ help_text }}```

## Things --help Won't Tell You

### Always write a description

Pass `-d "..."` on `tq create` for anything that will outlive the current task. Titles get terse fast -- "fix parser bug" is meaningless a week later. The description is the only place to anchor the ticket in its original context: what prompted it, what the user actually said, links to relevant files or PRs, what "done" looks like.

```bash
tq create "Fix parser dropping trailing commas" \
  -d "User reported on 2026-05-04 that comma-trailing JSON5 inputs raise. See parser.py:142. Done = round-trip test passes for trailing commas in arrays and objects."
```

The only time it's safe to skip `-d`: short-lived subtasks created during a single session where the parent ticket or surrounding conversation already carries the context, and you expect to close them the same day.

### There is no `note` command (and no `-m`)

To record progress, append a timestamped note: `tq edit <id> --note "text"` (repeatable). The status verbs (`start`/`close`/`cancel`/`reopen`) also accept `--note`; those entries are auto-tagged with the verb (`[closed]: ...`). `tq note`, `tq comment`, and a `-m` short flag do not exist -- the CLI rejects them and points back to `edit --note`. Never append notes to the ticket file by hand; that bypasses the timestamped format.

### There is no `tree` command

`tq ls --parent <id>` renders a ticket and its descendants as a tree. `tq deps <id>` is the other tree: dependencies, not hierarchy.

### Editing the body beyond -d and notes

`--description` replaces the body; `--note` appends. For body surgery not covered by either (e.g. restructuring sections), use `tq path <id>` to get the file path, then Read and Edit the file directly.

### `ls` filter pairs that don't combine

`ls` enforces three mutually exclusive pairs: `--ready`/`--blocked`, `-a`/`--archived`, and `--parent`/`--dep`. `-r` also excludes `--parent`/`--dep`. Everything else stacks.

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

## Workflow Patterns

### Starting work

```bash
tq ls --ready                                             # what's actionable?
tq start <id>                                             # claim it
# ... do the work ...
tq edit <id> --note "root cause in parser.py; fix behind flag"   # log progress
tq close <id> --note "fixed in 3f2c1a9"                   # done, with reason
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

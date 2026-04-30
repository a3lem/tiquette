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
| **Resolution** | `completed` (via `close`) or `canceled` (via `cancel`) |
| **Dependencies** | Directed: "A depends on B" means B blocks A |
| **Links** | Symmetric, informational only (don't affect blocking) |

## CLI Reference

```
{{ help_text }}```

## Things --help Won't Tell You

### Editing fields not covered by a command

To change a ticket's title, edit `.tickets/<id>.md` directly. Use `tq path <id>` to get the file path, then Read and Edit.

### Ready vs blocked logic

**Ready** = open/in_progress AND no unresolved deps AND no open children.
**Blocked** = open/in_progress AND (has unresolved deps OR has open children).

Parents are implicitly blocked by open children, even without explicit deps. This is transitive – grandparents are blocked too.

### Nest argument order

`nest` follows `mv` convention: last argument is the destination (parent).

```bash
tq nest child1 child2 parent   # both children move under parent
```

### No assignee default

`tq` does not auto-assign to the git user. Always pass `-a` explicitly when creating or assigning.

### Closing or cancelling a parent

Both `tq close` and `tq cancel` reject a ticket with open descendants. Pass `-f` / `--force` to cascade through the subtree -- every open descendant is closed (or cancelled) with the same resolution as the parent. Already-closed descendants are left alone. Each affected ID is printed on its own line in write order.

### Checkbox glyphs in `tq ls`

`[ ]` open, `[/]` in_progress, `[x]` closed-completed, `[~]` closed-cancelled. The tilde is a deliberate strikethrough cue -- match both `[x]` and `[~]` if you're parsing for "closed".

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
epic=$(tq create "Auth system" -t epic -a claude)
schema=$(tq create "Design auth schema" --parent "$epic" -a claude)
oauth=$(tq create "Implement OAuth" --parent "$epic" -a claude)
tq dep "$oauth" "$schema"     # OAuth depends on schema
```

### Checking progress

```bash
tq ls --blocked                # what's stuck?
tq deps <epic-id>             # visualize dependency graph
tq ls --completed --limit 5   # recently finished
```

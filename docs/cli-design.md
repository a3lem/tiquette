# tq CLI design v1.2

Drops the per-field mutation verbs (`tag`, `untag`, `dep`, `undep`, `nest`,
`unnest`, `link`, `unlink`, `assign`, `change-prio`, `change-type`, `describe`,
`add-note`, `xref`) in favour of a single `edit` command. `create` and `edit`
share one field-flag vocabulary, defined once.

## `tq -h`

```
tq (tiquette)- a minimal ticket system with dependency tracking

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
                                        **Accepts all create field-options (above)**, plus:
        --title TEXT                    Rename ticket
        --untag TAG                     Remove tag (repeatable)
        --undep ID                      Remove blocker (repeatable)
        --unlink ID                     Remove association (repeatable)
        --unset FIELD                   Clear a single-value field (repeatable)
                                        FIELD ∈ {parent, xref, assignee}
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

Examples
--------
  tq create 'Fix parser dropping trailing commas' -d 'parser.py:142' -t bug -p 1
  tq edit abf1 --tag urgent --untag stale -p 0 --note 'customer escalation'
  tq edit abf1 --parent 9zk2 --dep 4mn8
  tq ls --ready --tag backend --sort priority
```

## Notes

- `edit` is the only post-creation mutation path. Field options are anchored
  under `create` (the common path) and `edit` extends them with the removers.
  Removed verbs (`tag`, `nest`, `change-prio`, `describe`, ...) are gone, not
  aliased.
- `--description` replaces; `--note` appends. Both repeatable on `edit` is
  legal but only the last `--description` wins.
- Adders vs setters: collection fields (tag, dep, link) use add/remove pairs
  (`--tag`/`--untag`, etc.). Single-value fields (parent, xref, assignee)
  use one `--unset` flag with a field-name argument, not mirror
  `--unparent`/`--unxref`/... flags. Different semantics → different syntax:
  a collection has many elements you add or remove individually; a single-value
  field has one slot you fill or empty. `description` is intentionally not an
  `--unset` target: emptying the body is ambiguous (delete the section vs.
  blank string) and the operation is unlikely to be needed; reach for direct
  file editing (`tq path <id>`) in that rare case.
- `--unset FIELD` was chosen over empty-string magic (`--parent ''`) and over
  mirror flags. Empty-string-as-action looks like a value, requires shell
  quoting, and reads as "set to empty string" rather than "clear." Mirror
  flags (`--unparent`, `--unxref`, ...) would multiply surface area for no
  semantic gain and produce ugly names like `--undesc`. `--unset` is one
  flag, prior-supported (env vars: `unset FOO`), and the field enum is
  discoverable from `--help`. Setting and unsetting the same field in one
  call is an error (fail loud on ambiguous intent).
- `nest`'s mv-style multi-arg ergonomics (`tq nest c1 c2 parent`) are gone. The
  equivalent is two `edit` calls, or a shell loop. Worth it for one canonical
  surface.
- Single-letter shorts: `-d`, `-t`, `-p`, `-A` on `create`/`edit`; `-s`, `-a`,
  `-A` on `ls`. `ls` carries both `-a` (`--all`, include archived) and `-A`
  (`--assignee`) — a case-sensitive pair on a single command, which is a known
  readability trap. It exists today and is kept as-is, but it's a wart, not a
  pattern to extend: don't introduce further case-sensitive short pairs.
  `--tag` has no short — four characters is short enough.
- Status vocabulary: `open`, `in_progress`, `closed`, `canceled`. `closed`
  means the ticket is complete (work shipped); `canceled` means it was
  abandoned. "Completed" is no longer a status name — use "closed", or
  "complete(d)" only as informal synonyms in prose.
- Migration: existing tickets with `status: completed` need a one-time
  rewrite to `status: closed`. `autofix` is the natural home for this.
- `cancel` not `reject`: this is a personal ticket system, so you're both
  author and gatekeeper. "Reject" implies external authority (rejecting
  someone else's request); "cancel" fits self-authored work being abandoned.
- Title is positional on `create`, no `--title` flag. Matches the universal
  `<verb> <name>` CLI prior (`mkdir foo`, `git branch foo`, `docker run foo`),
  keeps the command's primary subject adjacent to the verb, and avoids a
  case-sensitive short pair with `-t` (type). `edit` exposes `--title` for
  renames, since `edit`'s positional slot is the id.
- `ls --parent` and `ls --dep` are not flat filters: `--parent ID` renders ID
  with its descendants as a tree, `--dep ID` lists the tickets that directly
  depend on ID. This is inherited unchanged from the current CLI.
- `edit`, not `update`. `update` connotes sync-from-remote in CLI vocabulary
  (`apt update`, `brew update`, `git remote update`). tq is file-local, so
  the sync reading would mislead. `edit` matches the in-place-modify prior
  (`gh issue edit`, `crontab -e`, `kubectl edit`).

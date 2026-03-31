---
name: tk-to-tq migration mapping
description: Mapping of tk (ticket-fork) features/commands to tq (tiquette) equivalents, including behavioral changes
type: project
---

tiquette is a Python reimplementation of the bash ticket CLI with a redesigned interface.

**Key renames/replacements:**
- `close --reason rejected` → `cancel` command; `close_reason` field → `resolution`; `rejected` value → `canceled`
- `status <id> <status>` removed; use `start`/`close`/`cancel`/`reopen`
- `ready`/`blocked`/`closed` commands → `ls --ready`/`ls --blocked`/`ls --status closed`
- `query`/`query-all` plugins → `ls --jsonl` + `show --json`/`info --json`
- `ticket-tags` plugin → `tags` core command (now in Fields group)
- `ticket-archive` plugin → `archive` core command (now in Lifecycle group)
- Plugin prefix: `tq-`/`tiquette-` instead of `tk-`/`ticket-`
- `--external-ref` → `--xref`; field name → `xref`
- `set-ref`/`unset-ref` → `xref <id> [xref]` (omit to clear)
- `assign`/`unassign` → `assign <id> [assignee]` (omit to clear)
- `dep tree` → `deps <id> [--full]`
- New command: `links` (list all linked pairs)
- `--design`/`--acceptance` flags on create: removed
- Help sections: View, Lifecycle, Relationships, Fields, Content (not "Query")

**Why:** The original bash implementation had fragile sed-based YAML handling and duplicated listing logic. The redesign consolidates commands and promotes plugins to core.

**How to apply:** `docs/cli-design.md` and `tq --help` are the authoritative sources. `docs/migration-notes.md` is marked stale.

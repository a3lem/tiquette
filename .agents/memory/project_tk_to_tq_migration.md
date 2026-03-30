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
- `ticket-tags` plugin → `tags` core command
- `ticket-archive` plugin → `archive` core command
- Plugin prefix: `tq-`/`tiquette-` instead of `tk-`/`ticket-`
- `--external-ref` → `--ref`; field name `external-ref` → `ref`
- `--design`/`--acceptance` flags on create: removed

**Why:** The original bash implementation had fragile sed-based YAML handling and duplicated listing logic. The redesign consolidates commands and promotes plugins to core.

**How to apply:** When adapting tk tests/specs to tq, always check migration-notes.md for the correct command names, flag names, and field names.

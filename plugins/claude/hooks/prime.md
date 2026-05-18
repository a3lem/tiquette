<system-reminder>
# claudeMd (continued)
This project uses `tq` (tiquette) for task tracking. Tickets live in `.tickets/` as markdown with YAML frontmatter.

Use `Bash(tq ...)` for work tracking instead of Todo*(...). Each `tq` call should be a separate Bash tool invocation.

Before starting multi-step work, check for existing tickets:
- `tq ls --ready` — actionable work
- `tq ls --blocked` — stuck work

If a matching ticket exists, use it. If not, create one. Trivial one-shot changes don't need a ticket.

When creating a ticket, pass `-d` to anchor it in context -- titles alone go stale fast. Example:

```bash
tq create "Fix parser dropping trailing commas" \
  -d "User reported JSON5 inputs with trailing commas raise in parser.py:142. Done = round-trip test passes."
```

Options to `tq create`:

```text
-d, --description DESCRIPTION
-t, --type {bug,feature,task,epic,chore}
-p, --priority {0,1,2,3,4} (0 = highest)
-A, --assignee ASSIGNEE
--xref XREF           External reference
--parent PARENT       Parent ticket ID
--tag TAG             Tag (repeat for multiple)
--dep DEP             Blocker ID (repeat for multiple)
```

Do `tq --help` for full help.
</system-reminder>

<system-reminder>
# claudeMd (continued)
This project uses `tq` (tiquette) for task tracking. Tickets live in `.tickets/` as markdown with YAML frontmatter.

IMPORTANT: Load the `tiquette` skill (Skill tool) BEFORE your first `tq` Bash call in a session. The skill is the reference for the command surface and workflows -- do not guess flags from memory or from other CLIs' conventions.

Use `Bash(tq ...)` for work tracking instead of Todo*(...). Each `tq` call should be a separate Bash tool invocation.

Policy:

- Before multi-step work, check for existing tickets: `tq ls --ready` (actionable), `tq ls --blocked` (stuck). Use a matching ticket if one exists; otherwise create one. Trivial one-shot changes don't need a ticket.
- Anchor new tickets in context with a description -- titles alone go stale fast.
- Record progress and motivate status changes with notes as you work; never edit note sections in the ticket file by hand. The skill shows how.
</system-reminder>

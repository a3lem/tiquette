## Context

`_format_ticket_line()` in `commands/query.py` is the sole formatter for ticket lines. It's used by both `ls` (via `_format_ticket_line_with_deps`) and `deps` (directly). Currently produces `<id> [P<n>][<status>] - <title>`.

## Goals / Non-Goals

**Goals:** Match the `tk ls` display format -- checkbox for status, hide default priority/type, show non-default type.

**Non-goals:** Changing the `deps` tree output format (though it shares the formatter and will get the new format too, which is fine). Changing JSONL output.

## Decisions

### Single formatter, same call sites

Modify `_format_ticket_line` in place. No new functions, no new parameters. Both `ls` and `deps` get the updated format -- the `deps` tree benefits from the same noise reduction.

**Alternatives considered:** Separate formatters for `ls` vs `deps`. Rejected -- there's no reason for them to differ, and two formatters means two places to update.

### Status-to-checkbox mapping

A dict lookup at module level:

```python
_STATUS_CHECKBOX: dict[str, str] = {
    "open": "[ ]",
    "in_progress": "[/]",
    "closed": "[x]",
}
```

Unknown statuses fall through to `[?]` to avoid crashing on bad data while remaining visible.

**Alternatives considered:** A function with if/elif. Overkill for a three-case mapping.

### Tag string construction

Build a tag string from non-default fields, then interpolate once:

```python
tags = ""
if t.priority != 2:
    tags += f" [P{t.priority}]"
if t.type != "task":
    tags += f" [{t.type}]"
```

When `tags` is empty, the format collapses naturally to `<id> - [checkbox] <title>`.

## Risks / Trade-offs

- `[/]` for in_progress is non-standard markdown. Fine -- this is terminal output, not rendered markdown.
- `deps` output format changes too. This is a feature, not a risk.

## Verification

1. Existing tests pass unchanged -- they assert on IDs and `<- [dep]`, not on `[P2][open]`.
2. New tests in `TestLsBehavior` for each delta scenario: default tags hidden, non-default priority shown, non-default type shown, both shown, checkbox per status, deps appended.
3. Manual `tq ls` against this project's `.tickets/`.

## Open Questions

None.

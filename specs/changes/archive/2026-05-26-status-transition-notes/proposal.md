# Status-Transition Notes

## Why

`tq close`, `tq cancel`, `tq start`, and `tq reopen` currently flip status with no way to record *why*. Users have been reaching for `-m` out of `git commit` muscle memory; the natural answer is to reuse the existing `--note` machinery and have the transition command auto-tag the entry with the verb that produced it.

## What Changes

- `--note TEXT` (repeatable) is accepted on `start`, `close`, `cancel`, and `reopen` -- same shape as on `create` and `edit`.
- Each note written by a transition command is prefixed with the verb tag: `[started]`, `[closed]`, `[canceled]`, `[reopened]`. The user supplies only the message text; the prefix is automatic.
- When `close -f` or `cancel -f` cascades to descendants, every descendant whose status is actually changed receives the same tagged note(s) -- but only when `--note` is supplied. Cascades without `--note` write nothing to Notes.
- Transition commands invoked without `--note` write nothing to the Notes section -- no empty `[closed]:` lines.
- All notes written in a single invocation share one timestamp, matching existing `--note` semantics on `create` and `edit`.

## Capabilities

### Modified Capabilities

- `ticket-lifecycle`: `start`, `close`, `cancel`, and `reopen` accept `--note TEXT` (repeatable), auto-tagging entries with the verb. Force-cascades propagate tagged notes to every affected descendant when `--note` is supplied.

## Impact

- Argparse surfaces for `start`, `close`, `cancel`, `reopen` gain `--note`.
- The Notes-writing path (currently used by `create` and `edit`) needs to accept an optional verb tag.
- Force-cascade code path needs to write notes to descendants when `--note` was supplied.
- New scenarios in the lifecycle spec; existing transition scenarios are unaffected.

## Out of Scope

- A short flag like `-m`. Stick with `--note` for consistency with `create` and `edit`.
- A full status-change history log (every transition recorded regardless of `--note`). That's a separate feature.
- Editing or removing previously-written transition notes.
- Special rendering of tagged notes in `tq show` / `tq info` (they display as plain text).

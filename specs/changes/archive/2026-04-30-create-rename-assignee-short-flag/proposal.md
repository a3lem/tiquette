# Proposal: Rename `tq create` assignee short flag to `-A`

## Why

`tq ls` is renaming its `--assignee` short flag from `-a` to `-A` (see change `ls-archived-flags`) to free `-a` for `--all`. `tq create` should use the same short flag so users don't have to remember different conventions across commands.

## What Changes

- **BREAKING:** Rename the short flag for `tq create --assignee` from `-a` to `-A`.

## Capabilities

### Modified Capabilities

- `ticket-lifecycle`: `tq create` short flag for `--assignee`.

## Impact

- `src/tiquette/commands/lifecycle.py`: argparse for `create`.
- Scripts using `tq create ... -a "Name"` will break; they must switch to `-A "Name"` or `--assignee "Name"`.

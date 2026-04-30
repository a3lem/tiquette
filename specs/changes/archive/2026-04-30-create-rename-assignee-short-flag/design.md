# Design: Rename `tq create` assignee short flag to `-A`

## Context

`src/tiquette/commands/lifecycle.py:39` declares:

```python
p_create.add_argument("-a", "--assignee", default=None, help="Assignee")
```

The sibling change `ls-archived-flags` rebinds `-a` on `tq ls` to mean `--all`. To keep short-flag semantics consistent across commands, `tq create` mirrors that rename: `-a` → `-A`.

## Goals

- `-A` and `--assignee` set the assignee on `tq create`.
- `-a` no longer accepted on `tq create` (argparse will reject as unknown short flag).

## Non-Goals

- Changing any other `tq create` flag.
- Adding `-a`/`--all` semantics to `create` (no source axis on a write command).

## Decisions

### Single-line argparse change

Rewrite the existing line:

```python
p_create.add_argument("-A", "--assignee", default=None, help="Assignee")
```

No `default=None` → no behavior change beyond the short-flag character. `argparse` will reject `tq create -a "Name"` with a standard "unrecognized arguments" exit-non-zero, which is exactly what the spec scenario asserts.

**Alternatives considered:**

- *Keep `-a` as a hidden alias for one release.* Rejected: the user explicitly chose breaking consistency over silent dual support, matching the `ls` change.

### Tests

Update existing `tq create` tests that pass `-a "Name"` to use `-A "Name"`. Add one regression test asserting `tq create -a "Name"` exits non-zero.

## Risks / Trade-offs / Limitations

- *[Risk] Scripts and habits using `tq create -a "Name"` break.* → Mitigation: CHANGELOG entry under the version bump; ship together with `ls-archived-flags` so the convention shifts atomically.

## Open Questions

None.

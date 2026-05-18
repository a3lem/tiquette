# Field Mutations via `edit`

All post-creation mutations go through `tq edit <id> [field-options]`.
This drive exercises every field-flag, including the removers and `--unset`.

## Setup

Create a single ticket to work with:

```
tq create 'Tracking field changes' -t task -p 2
```

Note the ID printed (referred to as `$ID` below).

## Steps

### 1. Change priority and type in one call

```
tq edit $ID -p 0 -t bug
```

`show $ID` should reflect `priority: 0` and `type: bug`.

### 2. Assign and verify

```
tq edit $ID -A alice
```

`show $ID` should show `assignee: alice`.

### 3. Clear the assignee with `--unset`

```
tq edit $ID --unset assignee
```

`show $ID` should show no assignee field (not even `null` inline).

### 4. Add multiple tags, then remove one

```
tq edit $ID --tag api --tag urgent
tq edit $ID --untag urgent
```

After both calls, `show $ID` should show `tags: [api]`. Running `tags`
should list `api` with count 1.

### 5. Set and clear an external reference

```
tq edit $ID --xref JIRA-42
```

`show $ID` should show `xref: JIRA-42`.

```
tq edit $ID --unset xref
```

`show $ID` should show no xref.

### 6. Replace description

```
tq edit $ID -d 'First description'
tq edit $ID -d 'Replacement description'
```

`show $ID` should show only "Replacement description" -- the first is gone.

### 7. Add notes (append-only, shared timestamp per call)

```
tq edit $ID --note 'First note' --note 'Second note'
```

`show $ID` should show a `## Notes` section with both notes, each prefixed
by the same ISO 8601 timestamp. Then:

```
tq edit $ID --note 'Third note added later'
```

`show $ID` should show all three notes. The third has a different (later)
timestamp than the first two.

### 8. Rename the ticket

```
tq edit $ID --title 'Renamed ticket'
```

`show $ID` should show the new title. The ID is unchanged.

### 9. Multi-field edit in one call

```
tq edit $ID -p 1 -t feature -A bob --tag backend --note 'combined edit'
```

`show $ID` should reflect all five changes atomically.

### 10. Error: no flags supplied

```
tq edit $ID
```

Should exit non-zero. Stderr should mention that at least one field-option
is required. The ticket is unchanged.

### 11. Error: set and unset same field

```
tq edit $ID -A carol --unset assignee
```

Should exit non-zero. Stderr should name `assignee`. `show $ID` should
confirm the assignee is unchanged (still `bob` from step 9).

### 12. Error: `--unset description` is rejected

```
tq edit $ID --unset description
```

Should exit non-zero with an "invalid choice" error. `description` is not
in the `--unset` enum (`parent`, `xref`, `assignee`). Use `tq path $ID`
and edit the file directly if you need to blank the body.

## Dependency edges

Create two helper tickets:

```
tq create 'Blocker A'   # $DEP_A
tq create 'Blocker B'   # $DEP_B
```

### 13. Add and remove deps in one call

```
tq edit $ID --dep $DEP_A
tq edit $ID --dep $DEP_B --undep $DEP_A
```

After the second call, `deps $ID` should show only `$DEP_B`.
`ls --ready` should not list `$ID` (it has an unresolved dep).

### 14. Cycle detection

```
tq edit $DEP_B --dep $ID
```

Should exit non-zero. Stderr should indicate a cycle. `deps $DEP_B`
should remain empty.

## Link edges

Create a peer ticket:

```
tq create 'Peer ticket'   # $PEER
```

### 15. Add a symmetric link

```
tq edit $ID --link $PEER
```

`links` should list the pair. `show $PEER` should back-reference `$ID`.

### 16. Remove the link symmetrically

```
tq edit $ID --unlink $PEER
```

`links` should no longer list the pair. `show $PEER` should not reference
`$ID`.

## Parent edges

Create a parent ticket:

```
tq create 'Epic parent'   # $PARENT
```

### 17. Set parent

```
tq edit $ID --parent $PARENT
```

`show $ID` should show `parent: $PARENT`. `ls --parent $PARENT` should
list `$ID` as a child.

### 18. Change parent

```
tq create 'Another epic'   # $PARENT2
tq edit $ID --parent $PARENT2
```

`show $ID` should now show `parent: $PARENT2`.

### 19. Clear parent via `--unset`

```
tq edit $ID --unset parent
```

`show $ID` should show no parent field.

### 20. Parent cycle detection

```
tq create 'Child of ID'   # $CHILD
tq edit $CHILD --parent $ID
tq edit $ID --parent $CHILD
```

The last command should exit non-zero. Stderr should indicate a cycle.
`show $ID` should still show no parent.

## What to watch for

- All changes apply atomically: if `--dep nonexistent -p 0` fails, the
  priority must also be unchanged.
- `--unset description` exits non-zero (invalid choice), not silently ignored.
- Symmetric link/unlink patches both ticket files; check both with `show`.
- Notes accumulate across calls; description is always replaced.
- Multiple `--note` flags in one call share one timestamp; notes across
  two calls get distinct timestamps.

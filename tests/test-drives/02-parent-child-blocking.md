# Parent-Child Blocking

Parents can't close while children are still open. This exercises the
hierarchy enforcement and the "last open child" notification.

## Setup

Empty tickets directory.

## Steps

1. Create an epic: "Redesign auth system" (type task, priority 1).
2. Create two children under the epic: "Design new schema" and "Implement OAuth flow". Use `--parent` on create.
3. Try to close the epic. Should fail with an error listing both open children.
4. Close "Design new schema". Should succeed with no special message (the epic still has another open child).
5. Close "Implement OAuth flow". Should succeed AND print a notification that the epic now has no remaining open children.
6. Now close the epic. Should succeed cleanly.

## Variation: grandchild blocking

7. Reopen the epic and "Implement OAuth flow".
8. Create a grandchild under "Implement OAuth flow": "Write OAuth tests".
9. Close "Implement OAuth flow". Should fail because its child is still open.
10. Close "Write OAuth tests" first, then "Implement OAuth flow", then the epic. All should succeed in that order.

## What to watch for

- The error message from step 3 lists the specific open descendants.
- The notification in step 5 mentions the epic's ID.
- Grandchild blocking (step 9) works transitively -- you can't skip levels.

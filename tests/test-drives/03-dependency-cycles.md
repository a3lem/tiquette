# Dependency Cycles

Dependency tracking must reject cycles. This exercises cycle detection
across direct, indirect, and self-referential cases.

## Setup

Empty tickets directory.

## Steps

1. Create three tickets: A ("Database migration"), B ("API update"), C ("Frontend refresh").
2. Add dep: A depends on B. Should succeed.
3. Add dep: B depends on C. Should succeed.
4. Add dep: C depends on A. Should fail -- this would create A → B → C → A.
5. Verify A still only depends on B (the failed operation didn't leave partial state).
6. Try: A depends on A (self-dep). Should fail.

## Interaction with ready/blocked

7. Check `ls --blocked`. A and B should appear (they have unresolved deps). C should not.
8. Check `ls --ready`. Only C should appear.
9. Close C. Now check `ls --blocked` -- only A should be blocked (B's dep on C is resolved). B should now be ready.
10. Close B. A should move from blocked to ready.

## What to watch for

- Cycle rejection is atomic: no partial dep additions on failure.
- `ls --ready` and `ls --blocked` correctly track resolution of deps.
- Closing a ticket unblocks its dependents immediately.

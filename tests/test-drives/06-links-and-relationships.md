# Links and Relationships

Test the symmetric link system and the `deps` tree / `links` list views.

## Setup

Empty tickets directory.

## Steps

1. Create four tickets: A, B, C, D.
2. Link A to B. Verify `show A` lists B as linked AND `show B` lists A as linked (symmetric).
3. Link A to C. Verify A now shows both B and C as linked.
4. Run `links`. Should list all linked pairs.
5. Unlink A from B. Verify the link is gone from both sides.
6. Add deps: D depends on A and B.
7. Run `deps D`. Should show a tree with A and B as direct deps.
8. Add dep: A depends on C. Run `deps D` again. Should show the transitive chain: D → A → C.
9. Nest B under A (`nest B A`). Verify `show A` lists B as a child. Verify `show B` lists A as parent.
10. Unnest B. Verify both sides are cleared.

## What to watch for

- Links are always symmetric: adding from one side shows on both.
- Unlinking from one side removes from both.
- `deps` shows transitive dependencies, not just direct ones.
- `nest` and `unnest` update the parent field correctly.

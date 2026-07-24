# Monorepo Stores

Targeting per-project stores with `--dir`, aggregating them with `ls -r`, and
the store-selection precedence between `--dir` and `TICKETS_DIR`.

## Setup

Unlike the other drives, this one does not point `TICKETS_DIR` at a single
store. Build a throwaway monorepo tree and `cd` into its root:

```bash
root=$(mktemp -d)
mkdir -p "$root/packages/api" "$root/packages/web" "$root/node_modules/pkg"
cd "$root"
unset TICKETS_DIR
```

No `.tickets/` exists anywhere yet.

## Steps

### Targeting with --dir

1. From the root, run `tq --dir packages/api create "Add /health endpoint" -t feature`.
   Verify the printed ID matches `api-????` and the file lands under
   `packages/api/.tickets/` (`tq --dir packages/api path <id>`). The prefix comes
   from the *project directory* name, not from `.tickets`.
2. Run `tq --dir packages/web create "Fix login redirect" -t bug`. Verify a
   `web-????` ID under `packages/web/.tickets/`.
3. Run `tq create "Bump CI runners"` at the root (no `--dir`). Walk-up finds no
   store, so a root `.tickets/` is created. Note its prefix comes from the temp
   dir's random name — that's expected.
4. Drop a decoy store that discovery must ignore:
   `tq --dir node_modules/pkg create "vendored noise"`.

### Aggregating with ls -r

5. From the root, run `tq ls -r`. Expect three sections, each headed by the
   store's path relative to root, in lexicographic order: `.` (the root store),
   then `packages/api`, then `packages/web`. The `node_modules` store does **not**
   appear.
6. Run `tq ls -r --jsonl`. Expect one JSON object per line, no headings, and
   every object carrying a `"store"` field (`.`, `packages/api`, or
   `packages/web`). Confirm with `tq ls -r --jsonl | jq -r .store | sort -u`.
7. Close the api ticket (`tq --dir packages/api close <api-id>`), then run
   `tq ls -r --status open`. The `packages/api` section is omitted entirely
   (no matching tickets), not shown empty.
8. Confirm `-r` refuses single-ticket scopes: `tq ls -r --parent web` and
   `tq ls -r --dep web` both exit non-zero.

### Cross-store isolation

9. Reopen the api ticket. Try to point a web ticket at it across stores:
   `tq --dir packages/web edit <web-id> --dep <api-id>`. It exits non-zero with
   "not found" — resolution is scoped to the web store. The web ticket's deps are
   unchanged.
10. Prove within-store still works: create a second web ticket and
    `tq --dir packages/web edit <web-id-1> --dep <web-id-2>` succeeds.

### Precedence: --dir vs TICKETS_DIR

11. Point the env at the root store and target api by flag:
    `TICKETS_DIR="$root/.tickets" tq --dir packages/api ls`. The listing shows
    api tickets — the typed `--dir` flag wins over the ambient `TICKETS_DIR`.
12. Without `--dir`, the env wins over walk-up:
    `cd packages/web && TICKETS_DIR="$root/.tickets" tq ls` shows the *root*
    store, not web's. `cd "$root"` when done.

## What to watch for

- IDs are prefixed from the **project directory** (`api-`, `web-`), independent
  of the fixed `.tickets` basename.
- `ls -r` headings are relative paths; the root store is `.`; sections are
  lexicographically ordered; empty stores are omitted.
- `node_modules`, `.git`, and a store's own `archive/` are never surfaced as
  stores.
- Cross-store `--dep`/`--parent`/`--link` targets are rejected as "not found" —
  stores are isolated.
- Location precedence: `--dir` > `TICKETS_DIR` > walk-up.
- Clean up: `rm -rf "$root"`.

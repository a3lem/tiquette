# Tasks: monorepo store targeting

## Implementation

### Store resolution
- [x] Add global `--dir <path>` to the top-level parser in `cli.py` (before `add_subparsers`).
- [x] Add a shared `resolve_store(args)` that returns `Path(args.dir)/".tickets"` when `--dir` is set (no walk-up, ignore `TICKETS_DIR`), else delegates to `find_tickets_dir()`.
- [x] Switch every handler that calls `find_tickets_dir()` to the shared resolver so `--dir` works across all commands.
- [x] Route `create`'s store-initialization target through the resolved store (init `<path>/.tickets/` under `--dir`, `cwd/.tickets/` otherwise).

### Recursive discovery
- [x] Add `discover_stores(root)` in `store.py`: `os.walk` with denylist pruning (`.git`, `node_modules`, `.venv`, `__pycache__`, `.tox`, `dist`, `build`, `.mypy_cache`, `.ruff_cache`); register a store on seeing a `.tickets/` child and stop descending into it; keep descending siblings; return stores ordered by relpath. Ignore `TICKETS_DIR`.

### ls -r
- [x] Add `-r`/`--recursive` to the `ls` subparser.
- [x] Guard: `-r` with `--parent` or `--dep` exits non-zero.
- [x] Recursive human render: per store, print the relpath heading (root → `.`), then the existing filtered/sorted/tree listing; omit empty stores; sections in relpath order; `--limit` per store.
- [x] Recursive JSONL render: flat stream, one object per ticket across stores, each extended with `"store": <relpath>`; no headings; leave non-recursive `--jsonl` output unchanged.

### Docs
- [x] Update `docs/cli-design.md`, `HELP_TEXT` in `cli.py`, and `CHANGELOG.md` (document `--dir` and `ls -r`).
- [x] Land the `tests/test-drives/11-monorepo-stores.md` walkthrough (already drafted) and run it once by hand.

## Verification

One test (or scenario group) per requirement; annotate tests with `# spec:` back-references.

- [x] **ticket-store / Directory walking** — walk-up and `TICKETS_DIR` still resolve with no `--dir`; precedence `--dir` > `TICKETS_DIR` > walk-up holds.
- [x] **ticket-store / Store targeting with --dir** — `--dir` targets a sibling store; `create` initializes and derives the prefix from the path; prevails over `TICKETS_DIR`; missing store errors on read.
- [x] **ticket-store / Recursive store discovery** — nested stores discovered; root store included; `.git`/`node_modules` skipped; `archive/` not a separate store.
- [x] **ticket-query / Recursive listing across stores** — grouped output; lexicographic order; empty stores omitted; filters within each store; JSONL flat with `store` field; root heading `.`; `-r` × `--parent`/`--dep` rejected.
- [x] **ticket-relationships / Relationships are store-local** — cross-store `--dep` and `--parent` rejected as not found; within-store relationship still works.
- [x] **id-resolution / Resolution is scoped to a single store** — identical suffix in two stores resolves per `--dir` with no ambiguity error; a partial matching only another store is not found.

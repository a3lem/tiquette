# Implementation notes

## Testing a monorepo needs the tq binary, not `uv run tq`

The existing CLI tests shell out with `subprocess.run(["uv", "run", "tq", ...])`
and leave `cwd` at the project root, isolating stores via `TICKETS_DIR`. That
does not work here: `-r` and walk-up must operate on a temp tree, so `cwd` has
to be *inside* that tree — but `uv run` would then fail to resolve the tiquette
project from the temp cwd.

`tests/test_cli_monorepo.py` resolves the installed console script once
(`<venv>/bin/tq`, via `sys.executable`'s dir) and invokes it directly. Its
shebang points at the project venv, so tiquette imports regardless of `cwd`,
and `cwd` is free to be the temp monorepo root. The `run()` helper also pops
`TICKETS_DIR` from the child env (the autouse conftest fixture sets it) so
walk-up/`--dir`/`-r` are exercised cleanly.

## Global `--dir` and in-process handler tests

`--dir` is declared on the top-level parser before `add_subparsers`, so it lands
on the shared namespace as `args.dir` for every command — no per-subparser
wiring. The one catch: a test that constructs an `argparse.Namespace` by hand and
calls a handler in-process (e.g. `lc._handle_status(ns)`) must include
`dir=None`, since handlers now read `args.dir`. Only one such test existed
(`test_cli_lifecycle.py::...test_parent_still_open...`); it was updated. The real
CLI always supplies the default, so production code reads `args.dir` directly
rather than `getattr`-guarding.

## Isolation was free

No enforcement code was added for cross-store isolation. Mutations already
resolve dep/link/parent targets with `resolve_id_in_dir` against the single
mutated store and detect cycles within it; `--dir` only changes which store that
is. The cross-store rejection ("not found") falls out of the existing resolver.

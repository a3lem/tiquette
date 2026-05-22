# Design: Prune archived tickets

## Approach

Add `_handle_prune` and a `prune` subparser in `src/tiquette/commands/query.py`, next to the existing `archive` command. The handler loads only archived tickets, applies the filters, and either prints (dry run) or deletes.

## Subparser

```
p_prune = subparsers.add_parser("prune", help="Permanently delete archived tickets by filter")
p_prune.add_argument("-s", "--status", choices=["closed", "canceled"])
p_prune.add_argument("-t", "--type", choices=["bug", "feature", "task", "epic", "chore"])
p_prune.add_argument("--before", metavar="YYYY-MM-DD")
p_prune.add_argument("-y", "--yes", action="store_true")
p_prune.set_defaults(func=_handle_prune)
```

`choices=` gives argparse-level rejection of invalid status/type (covers the "rejects invalid" scenarios). `--before` is validated in the handler (parse with `datetime.date.fromisoformat`; on failure, exit non-zero).

## Loading archived tickets

Reuse the existing store API: `iter_tickets(tickets_dir, source="archived")` yields only tickets under `.tickets/archive/`. If the archive dir doesn't exist this yields nothing, which naturally satisfies the "ignores active tickets / no archive" scenarios.

## Filtering

AND-combine the supplied filters. Each unset filter is a pass-through.
- status: `t.status == args.status`
- type: `t.type == args.type`
- before: `t.created < datetime` where the cutoff is midnight of the parsed date. `created` is an ISO 8601 datetime string; parse both sides to comparable datetimes. Strictly-before (`<`), so a ticket created exactly at midnight of the cutoff is kept.

## Filter-required guard

If `args.status is None and args.type is None and args.before is None`, write a usage error to stderr and exit non-zero before touching the filesystem.

## Dry run vs delete

- Default (`--yes` absent): print each matching ticket ID, delete nothing.
- `--yes`: delete each matching file from `.tickets/archive/`, printing each removed ID.
- No matches: print a "no tickets matched" message, exit 0, in both modes.

Deletion is `Path.unlink()` per matched file. No reference-safety check (out of scope, per proposal).

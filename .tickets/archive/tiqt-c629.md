---
id: tiqt-c629
status: closed
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:55Z
---
# Consolidate glob-and-parse-all-tickets loops

## Description

The pattern 'for p in dir.glob("*.md"): read_ticket(p)' appears in lifecycle.py:97-100, lifecycle.py:126-133, autofix.py:86-89, and store.build_dep_graph at store.py:385-391. Plus active/archived dir enumeration is re-encoded in validate.py:24-29, autofix.py:31-44, query.py:163-169. Fix: add 'iter_tickets(tickets_dir: Path, *, include_archive: bool = False) -> Iterator[Ticket]' and 'load_all_tickets(...) -> dict[str, Ticket]' in store.py, and route the call sites through them.

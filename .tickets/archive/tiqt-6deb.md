---
id: tiqt-6deb
status: closed
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:55Z
---
# Filter self-links on read, not just on write

## Description

query.py:769 builds 'tuple(sorted([t.id, link_id]))' for the symmetric-link pair set; if a ticket has a self-link in its links list (possible on old data), this yields '(id, id)'. store.apply_field_changes filters self-links on write (store.py:518) but read paths trust the data. Fix: in read_ticket (or a normalisation step there), drop self-references from links/deps with a warning logged once per file, so downstream code never sees them.

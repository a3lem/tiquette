---
id: tiqt-3c26
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-05-19T11:25:10.969735+00:00
---
# Stop re-globbing archived/ in validate after load_all_tickets

## Description

commands/validate.py:25-30 calls load_all_tickets(source='all') and then globs archived/ again separately to compute archived_ids. The store already walked them. Either return (active_ids, archived_ids) from the store or use two source-specific loads. Follow-up to tiqt-c629 (consolidate glob loops).

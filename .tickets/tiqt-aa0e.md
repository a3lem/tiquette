---
id: tiqt-aa0e
status: closed
type: feature
priority: 2
assignee: claude
deps: []
links: []
tags: []
created: 2026-08-30T13:57Z
---
# Teach the tq surface: prime/skill split, canonical-form hints, variadic reads

## Description

Carry-over from canceled tiqt-8e5c after design review. The surface stays canonical (no note/tree verbs, no -m). Decisions: (1) prime.md becomes policy-only and mandates a tiquette-skill load before the first tq call; the skill is the sole home of the command surface, including 'there is no note/tree/-m' tips. (2) Unknown commands print a hint that teaches the canonical form (tq note -> 'use: tq edit <id> --note TEXT'); typos get closest-match. (3) show/info/path accept multiple IDs, validated up front; --json emits one object for a single ID and a JSON array for multiple. (4) Reads stay fail-fast on malformed files; the existing autofix hint is the remedy. Also: help documents prune -t; skill drops the inherited nonexistent plugin-system section. Done = tests pass, ticket-query deltas applied, shablon regenerated.

## Notes

- 2026-08-30T14:03Z: Shipped: policy-only prime.md with skill-load mandate; skill gains no-note/no-tree/no--m tips and drops the plugin-system section; canonical-form hints on unknown commands (exit 2, nothing aliased); variadic show/info/path with up-front validation and JSON-array shape for multiple IDs; prune -t in help. ticket-query deltas applied; change archived as specs/changes/archive/2026-08-30-variadic-read-commands. 541 tests pass (21 new), basedpyright 0 errors, ruff findings equal to baseline.
- 2026-08-30T14:03Z [closed]: not committed; working tree holds the change


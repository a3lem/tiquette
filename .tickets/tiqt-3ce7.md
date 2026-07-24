---
id: tiqt-3ce7
status: open
type: chore
priority: 3
deps: []
links: []
tags: []
created: 2026-07-06T18:18Z
---
# Spec undep/unlink behavior against an archived target

## Description

spexl-spec-critic (ticket-edit-active-only-crossref inter-spec review, 2026-07-06) found that ticket-edit's --undep/--unlink resolve per the same active-only rule as --dep/--link/--parent adds, but the removal path behaves differently in code: store.py's _resolve_optional falls back to the literal partial string on TicketNotFoundError instead of erroring, so a partial ID targeting an archived-only ticket silently no-ops (nothing removed, no error) rather than matching or failing loudly. Meanwhile ticket-autofix and ticket-validate both document that active tickets legitimately keep deps/links/parent pointing at now-archived tickets. Neither id-resolution nor ticket-edit specs this no-op-on-partial-archived-target removal semantics. Done = spec delta (id-resolution and/or ticket-edit) documenting the intended --undep/--unlink behavior against archived-only targets, plus a scenario/test.

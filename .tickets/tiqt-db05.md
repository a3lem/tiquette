---
id: tiqt-db05
status: open
type: chore
priority: 4
deps: []
links: []
tags: []
created: 2026-07-06T18:18Z
---
# Align ticket-lifecycle and ticket-edit cross-reference wording

## Description

spexl-spec-critic (ticket-edit-active-only-crossref inter-spec review, 2026-07-06) flagged that ticket-lifecycle's Create ticket requirement and ticket-edit's three requirements (Dependency/Link add-remove, Parent set) point at the same id-resolution active-only rule with different phrasing: ticket-lifecycle says 'Partial IDs passed to --dep/--link/--parent SHALL resolve against active tickets only, per...'; ticket-edit's three (identical to each other) say '...targets SHALL resolve per the active-only rule in...'. Semantically equivalent, not verbatim. Low priority cosmetic cleanup -- fix next time either file is opened for an unrelated change, pick ticket-edit's template since it's already used 3x.

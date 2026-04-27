# Proposal: ls display format

## Motivation

`tq ls` output deviates from the original `tk ls` format in three ways:

1. Priority is always shown, even when P2 (the default) -- adds noise
2. Ticket type is never shown -- `[epic]`, `[feature]` etc. are useful context
3. Status is shown as text labels `[open]`/`[in_progress]` instead of markdown checkboxes

The `tk` format is denser and more scannable. Checkboxes (`[ ]`, `[x]`) are instantly parseable. Hiding defaults (P2 priority, "task" type) reduces visual clutter.

## What changes

The `ls` line format changes from:

```
kap-ctg [P2][open] - Configurable k for number of examples
kap-0wp [P2][open] - Deployment configuration files
```

To:

```
kap-ctg - [ ] Configurable k for number of examples
kap-0wp [feature] - [ ] Deployment configuration files
kap-eag [P1] - [ ] Locally E2E Testable JDN Deployment
└── kap-kj2 - [/] AI Web API v1
```

Rules:
- Priority tag shown only when not P2
- Type tag shown only when not "task"
- Status rendered as checkbox: `[ ]` = open, `[/]` = in_progress, `[x]` = closed

## Capabilities affected

- `ticket-query` (List tickets display format)

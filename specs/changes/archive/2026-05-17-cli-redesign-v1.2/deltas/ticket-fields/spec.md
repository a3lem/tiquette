# Ticket Fields

## REMOVED Requirements

### Requirement: Assign

**Reason**: Replaced by `tq edit <id> -A <assignee>` and
`tq edit <id> --unset assignee`. See the `ticket-edit` capability.
**Migration**: Replace `tq assign <id> <assignee>` with
`tq edit <id> -A <assignee>`. Replace `tq assign <id>` (clear) with
`tq edit <id> --unset assignee`.

### Requirement: Change priority

**Reason**: Replaced by `tq edit <id> -p <priority>`. See the
`ticket-edit` capability.
**Migration**: Replace `tq change-prio <id> <priority>` with
`tq edit <id> -p <priority>`.

### Requirement: Change type

**Reason**: Replaced by `tq edit <id> -t <type>`. See the `ticket-edit`
capability.
**Migration**: Replace `tq change-type <id> <type>` with
`tq edit <id> -t <type>`.

### Requirement: Tag management

**Reason**: Replaced by `tq edit <id> --tag <tag>` and
`tq edit <id> --untag <tag>`. See the `ticket-edit` capability.
**Migration**: Replace `tq tag <id> <tag>...` with
`tq edit <id> --tag <tag> [--tag <tag> ...]`. Replace
`tq untag <id> <tag>...` with `tq edit <id> --untag <tag>
[--untag <tag> ...]`.

### Requirement: External reference

**Reason**: Replaced by `tq edit <id> --xref <ref>` and
`tq edit <id> --unset xref`. See the `ticket-edit` capability.
**Migration**: Replace `tq xref <id> <ref>` with
`tq edit <id> --xref <ref>`. Replace `tq xref <id>` (clear) with
`tq edit <id> --unset xref`.

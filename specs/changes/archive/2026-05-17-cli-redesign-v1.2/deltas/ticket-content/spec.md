# Ticket Content

## REMOVED Requirements

### Requirement: Add note

**Reason**: Replaced by `tq edit <id> --note <text>` (and `tq create
<title> --note <text>` on the creation surface). See the `ticket-edit`
and `ticket-lifecycle` capabilities.
**Migration**: Replace `tq add-note <id> <text>` with
`tq edit <id> --note <text>`. Stdin piping is no longer supported;
shell substitution (`$(...)`) covers the same use case.

### Requirement: Describe

**Reason**: Replaced by `tq edit <id> -d <text>`. See the `ticket-edit`
capability. Note that `--unset description` is intentionally not
supported; for the rare case of needing to empty a description, use
`tq path <id>` and edit the file directly.
**Migration**: Replace `tq describe <id> <text>` with
`tq edit <id> -d <text>`.

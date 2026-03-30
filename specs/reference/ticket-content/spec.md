# Ticket Content

Covers commands that modify ticket body content: `describe`, `add-note`.

## Requirement: Add note

The system SHALL append a timestamped note to the `## Notes` section of a ticket when `tq add-note` is invoked.

### Scenario: Add a note
- Given ticket "note-0001" exists
- When the user runs `tq add-note note-0001 "This is my note"`
- Then the command exits 0
- And ticket "note-0001" contains a `## Notes` section
- And the notes section contains "This is my note"

### Scenario: Note has timestamp
- Given ticket "note-0001" exists
- When the user runs `tq add-note note-0001 "Timestamped note"`
- Then the note line includes an ISO 8601 timestamp

### Scenario: Multiple notes are appended
- Given ticket "note-0001" exists
- When the user adds "First note" then "Second note"
- Then both notes appear in the `## Notes` section in order

### Scenario: Add note to ticket with existing notes section
- Given ticket "note-0001" already has a `## Notes` section
- When the user runs `tq add-note note-0001 "Additional note"`
- Then the note is appended to the existing section

### Scenario: Empty note adds timestamp-only entry
- Given ticket "note-0001" exists
- When the user runs `tq add-note note-0001 ""`
- Then the command exits 0
- And the notes section contains a timestamp entry

### Scenario: Add note to non-existent ticket
- When the user runs `tq add-note nonexistent "My note"`
- Then the command exits non-zero
- And stderr contains "ticket 'nonexistent' not found"

### Scenario: Add note with partial ID
- Given ticket "note-0001" exists
- When the user runs `tq add-note 0001 "Partial ID note"`
- Then the command exits 0

### Scenario: Add note via stdin
- Given ticket "note-0001" exists
- When the user pipes "Piped note content" to `tq add-note note-0001`
- Then the command exits 0
- And the notes section contains "Piped note content"

## Requirement: Describe

The system SHALL set or replace the `## Description` section of a ticket when `tq describe` is invoked.

### Scenario: Set description
- Given ticket "desc-0001" exists with no description
- When the user runs `tq describe desc-0001 "New description content"`
- Then the command exits 0
- And ticket "desc-0001" has a `## Description` section containing "New description content"

### Scenario: Replace existing description
- Given ticket "desc-0001" has description "Old content"
- When the user runs `tq describe desc-0001 "New content"`
- Then the description section contains "New content"
- And the description section does not contain "Old content"

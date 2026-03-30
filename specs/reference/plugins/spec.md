# Plugins

Covers the plugin discovery and execution system, and the `super` bypass command.

## Requirement: Plugin discovery

The system SHALL discover executables named `tq-<cmd>` or `tiquette-<cmd>` in PATH and execute them when `tq <cmd>` is invoked for an unknown command.

### Scenario: Plugin in PATH is executed
- Given a plugin `tq-hello` that outputs "Hello from plugin!"
- When the user runs `tq hello`
- Then the command exits 0
- And the output is "Hello from plugin!"

### Scenario: Plugin receives command arguments
- Given a plugin `tq-echo` that echoes its arguments
- When the user runs `tq echo foo bar baz`
- Then the output is "foo bar baz"

### Scenario: tiquette- prefix plugins are also discovered
- Given a plugin `tiquette-greet` that outputs "Greetings!"
- When the user runs `tq greet`
- Then the output is "Greetings!"

### Scenario: tq- prefix takes precedence over tiquette- prefix
- Given both `tq-test` and `tiquette-test` exist
- When the user runs `tq test`
- Then the `tq-test` plugin is executed

## Requirement: Plugin environment

The system SHALL pass `TICKETS_DIR` and `TQ_SCRIPT` environment variables to plugins.

### Scenario: Plugin receives TICKETS_DIR
- Given a plugin that outputs `$TICKETS_DIR`
- When the user runs the plugin
- Then the output contains the path to `.tickets/`

### Scenario: Plugin receives TQ_SCRIPT
- Given a plugin that outputs `$TQ_SCRIPT`
- When the user runs the plugin
- Then the output contains the path to the `tq` executable

## Requirement: Super command

The system SHALL bypass plugin dispatch and execute the built-in command directly when `tq super <cmd>` is invoked.

### Scenario: Super bypasses plugin
- Given a plugin `tq-create` exists
- When the user runs `tq super create "Test ticket"`
- Then the built-in create command runs (not the plugin)
- And the output matches a ticket ID pattern

## Requirement: Built-in commands take precedence

The system SHALL execute built-in commands even when a matching plugin exists, unless the plugin explicitly overrides a built-in. Built-in commands always win.

### Scenario: Built-in still works with plugin present
- Given a plugin `tq-hello` exists
- When the user runs `tq create "Normal ticket"`
- Then the built-in create command runs
- And the output matches a ticket ID pattern

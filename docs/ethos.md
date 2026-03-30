# Ethos

## Why reimplement `ticket`?

Greg Wedow's [ticket](https://github.com/wedow/ticket) gets the fundamentals right. Tickets are plain markdown files with YAML frontmatter. The core is a single script. Every feature is verified by behavioral tests. It's easy to extend with plugins. And in practice, AI agents spend far fewer tokens on task management with `tk` than with alternatives.

So why rewrite it?

### Maintainability over portability

The original is bash + awk. Portable, fast, dependency-free. But the author of this fork is a Python programmer. Reasoning about sed-based YAML manipulation and 200-line inline awk blocks is slow and error-prone. A tool you can confidently modify beats one you have to reverse-engineer.

The portability loss is minimal. Python 3 is everywhere that matters, and `tk` already requires bash specifically (not sh), so POSIX purity was already off the table.

### Real parsing instead of string hacking

The original manipulates YAML with sed. Values containing `/`, `&`, or newlines corrupt the file. Array operations use unanchored regex that can mangle similar IDs. A proper YAML library eliminates an entire class of bugs.

### The test suite makes it safe

The original has ~730 BDD scenarios in behave (Python). They test the CLI end-to-end, not internal functions. This means they work as a regression suite for a reimplementation with minimal changes to step definitions. We're not rewriting and hoping -- we're rewriting against a contract.

### A cleaner interface

The reimplementation is also an opportunity to rethink the CLI surface. Consolidating `ready`/`blocked`/`closed` into `ls` with flags. Adding field-update commands so every attribute set at creation time can be modified later. Replacing `close --reason` with distinct `close` and `cancel` verbs. These changes emerged from using the tool and noticing friction.

## Design principles

**Agents are first-class users.** Most invocations come from AI agents, not humans. Commands should be unambiguous, composable, and produce structured output (`--json`, `--jsonl`) for machine consumption.

**Humans shouldn't suffer for it.** Short command names, clear help text, sensible defaults. `tq ls --ready` should be obvious without reading the docs.

**Files are the source of truth.** Tickets are markdown files in `.tickets/`. No database, no index, no lock files. Git handles versioning, diffing, and collaboration. The CLI is a convenience layer over a file format.

**Do less, well.** No workflow engine, no notification system, no web UI. Create tickets, track status, manage relationships. The plugin system handles everything else.

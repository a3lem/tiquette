---
id: tiqt-d348
status: closed
type: chore
priority: 2
deps: []
links: []
tags: []
created: 2026-05-19T08:54:48.267952+00:00
---
# Replace T._GenericAlias subparser annotation with correct argparse type

## Description

All five command modules annotate the subparsers arg as 'subparsers: T._GenericAlias  # type: ignore[name-defined]' (commands/query.py:58, lifecycle.py:25, edit.py:25, validate.py:18, autofix.py:23). T._GenericAlias is a private CPython typing internal -- not a real public type -- and the type: ignore hides the breakage. Fix: replace with 'argparse._SubParsersAction[argparse.ArgumentParser]' (or a typing alias in commands/__init__.py) and drop the ignore.

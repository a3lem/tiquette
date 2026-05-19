---
id: tiqt-0fd3
status: open
type: bug
priority: 3
deps: []
links: []
tags: []
created: 2026-05-19T08:55:49.353645+00:00
---
# Reject empty-string --dep and --parent instead of falling through

## Description

query.py:586 and query.py:516 use truthy tests on args.dep / args.parent to decide whether the user supplied a scope flag. An invocation like 'tq ls --dep ""' passes argparse but is then silently treated as 'no scope', producing a tree of every ticket. Fix: in the argparse setup (or at the top of _handle_ls), reject empty strings with a clear error before scope dispatch.

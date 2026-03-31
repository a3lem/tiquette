#!/usr/bin/env bash
# [AI]
# Context: user request for auto-updating README CLI help section
# Intent: replace content between CLI-HELP markers with current `tq --help` output
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
README="$REPO_ROOT/README.md"
TMPFILE="$(mktemp)"
trap 'rm -f "$TMPFILE"' EXIT

inside=0
while IFS= read -r line; do
    if [[ "$line" == *"<!-- BEGIN:CLI-HELP -->"* ]]; then
        echo "$line" >> "$TMPFILE"
        echo '```' >> "$TMPFILE"
        uv run tq --help >> "$TMPFILE"
        echo '```' >> "$TMPFILE"
        inside=1
    elif [[ "$line" == *"<!-- END:CLI-HELP -->"* ]]; then
        echo "$line" >> "$TMPFILE"
        inside=0
    elif [[ "$inside" -eq 0 ]]; then
        echo "$line" >> "$TMPFILE"
    fi
done < "$README"

mv "$TMPFILE" "$README"

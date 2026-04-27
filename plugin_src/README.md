# `plugin_src/`

Jinja2 templates for generating agent plugin artifacts (skills, priming content, rules).

The directory structure under `templates/` mirrors the output layout relative to the repo root.

Example:

```
# The rendered content of the template file located at:
#   $REPO_ROOT/plugin_src/templates/plugins/claude/hooks/prime.md
# Is written to:
#   $REPO_ROOT/plugins/claude/hooks/prime.md
```

Partials live in `templates/_includes/`. These are included by other templates. They do not correspond to an output file.

## Usage

```bash
uv run scripts/generate-plugin-files.py           # render
```

## Context variables

| Variable | Source |
|----------|--------|
| `help_text` | `tq --help` |
| `version` | `pyproject.toml` |

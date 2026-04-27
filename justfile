default:
    @just --list

sync-readme:
    bash scripts/sync-readme.sh

plugins:
    uv run scripts/generate-plugin-files.py

sync: sync-readme plugins

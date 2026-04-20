default:
    @just --list

sync-readme:
    bash scripts/sync-readme.sh

plugins:
    uv run scripts/build-plugins.py

plugins-check:
    uv run scripts/build-plugins.py --check

sync: sync-readme plugins

default:
    @just --list

test:
    uv run pytest -n 4

sync-readme:
    bash scripts/sync-readme.sh

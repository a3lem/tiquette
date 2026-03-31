default:
    @just --list

test:
    pytest -n 4

sync-readme:
    bash scripts/sync-readme.sh

default:
    @just --list

sync:
    shablon generate

test:
    uv run pytest -n 4

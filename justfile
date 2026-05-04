default:
    @just --list

shablon:
    shablon generate

test:
    uv run pytest -n 4

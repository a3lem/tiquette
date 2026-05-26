default:
    @just --list

shablon:
    shablon generate

test:
    uv run pytest -n 4

bump bump_type:
    uv run bump-my-version bump {{bump_type}}

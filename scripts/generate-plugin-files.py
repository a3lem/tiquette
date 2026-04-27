#!/usr/bin/env python3
"""Build plugin artifacts from Jinja2 templates.

Templates live in plugin_src/templates/. The directory structure mirrors the
output layout relative to PROJECT_ROOT. Directories named _includes/ contain
partials available for inclusion but never rendered directly.

Usage:
    uv run scripts/build-plugins.py
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "plugin_src" / "templates"


def main() -> None:
    context = _build_context()
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        keep_trailing_newline=True,
    )

    artifacts = _discover(env)
    _generate(artifacts, env, context)


def _build_context() -> dict[str, str]:
    help_text = subprocess.run(
        ["tq", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    pyproject = PROJECT_ROOT / "pyproject.toml"
    with pyproject.open("rb") as f:
        version = tomllib.load(f)["project"]["version"]

    return {
        "help_text": help_text,
        "version": version,
    }


def _discover(env: Environment) -> list[tuple[str, Path]]:
    """Walk templates, skipping _includes/ directories."""
    artifacts: list[tuple[str, Path]] = []

    assert env.loader is not None
    for template_name in env.loader.list_templates():
        if "/_includes/" in f"/{template_name}":
            continue
        output_path = PROJECT_ROOT / template_name
        artifacts.append((template_name, output_path))

    return artifacts


def _render(template_name: str, env: Environment, context: dict[str, str]) -> str:
    return env.get_template(template_name).render(**context)


def _generate(
    artifacts: list[tuple[str, Path]], env: Environment, context: dict[str, str]
) -> None:
    for template_name, output_path in artifacts:
        rendered = _render(template_name, env, context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)
        sys.stdout.write(f"  wrote {output_path.relative_to(PROJECT_ROOT)}\n")


if __name__ == "__main__":
    main()

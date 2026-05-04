#!/usr/bin/env python3
"""Build the render context for shablon."""

from __future__ import annotations

import json
import pathlib
import subprocess
import tomllib

help_text = subprocess.run(
    ["tq", "--help"],
    capture_output=True,
    text=True,
    check=True,
).stdout

edit_warning = "This file is managed by `shablon`. Do not edit directly. Instead, modify template in .shablon/templates/."

pyproject = tomllib.loads(pathlib.Path("pyproject.toml").read_text())
version = pyproject["project"]["version"]
assert isinstance(version, str), f"expected str version, got {type(version).__name__}"

print(json.dumps({"help_text": help_text, "version": version, "edit_warning": edit_warning}))

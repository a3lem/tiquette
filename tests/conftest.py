"""Shared fixtures for CLI tests.

Arg-parsing test classes call `run_tq` without setting TICKETS_DIR.
Since handlers now do real work, a valid tickets dir must exist.
This fixture creates one per test. Behavioral tests override
TICKETS_DIR via their own env dict, so they are unaffected.
"""

from __future__ import annotations

import os
import typing as T
from pathlib import Path

import pytest

from tiquette.store import Ticket, write_ticket


@pytest.fixture(autouse=True)
def default_tickets_dir(tmp_path: Path) -> T.Iterator[str]:
    tickets_path = tmp_path / "_fixture_tickets"
    tickets_path.mkdir()
    # Simple fixtures
    # [AI]
    # Context: cli-redesign-v1.2 -- ticket-edit / ticket-lifecycle requirement=create-ticket
    # Intent: v1.2 makes `create --dep` and `edit --dep` validate that the target
    #   ticket exists, so the dep-* / d-* / p-* IDs referenced by argparse-shape
    #   tests must be seeded here.
    for tid in (
        "t-001",
        "test-001",
        "test-0001",
        "child-001",
        "child-002",
        "parent-001",
        "show-001",
        "info-001",
        "dep-001",
        "dep-002",
        "d-001",
        "p-001",
    ):
        write_ticket(Ticket(id=tid, title="Fixture ticket"), tickets_path)
    # task-* fixtures with deps for undep arg tests
    write_ticket(
        Ticket(id="task-0001", title="Fixture", deps=["task-0002", "task-0003"]),
        tickets_path,
    )
    write_ticket(Ticket(id="task-0002", title="Fixture"), tickets_path)
    write_ticket(Ticket(id="task-0003", title="Fixture"), tickets_path)
    # link-* fixtures with links for unlink arg tests
    write_ticket(
        Ticket(id="link-0001", title="Fixture", links=["link-0002", "link-0003"]),
        tickets_path,
    )
    write_ticket(
        Ticket(id="link-0002", title="Fixture", links=["link-0001", "link-0003"]),
        tickets_path,
    )
    write_ticket(
        Ticket(id="link-0003", title="Fixture", links=["link-0001", "link-0002"]),
        tickets_path,
    )
    old = os.environ.get("TICKETS_DIR")
    os.environ["TICKETS_DIR"] = str(tickets_path)
    yield str(tickets_path)
    if old is None:
        os.environ.pop("TICKETS_DIR", None)
    else:
        os.environ["TICKETS_DIR"] = old

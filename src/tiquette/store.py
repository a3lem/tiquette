from __future__ import annotations

import dataclasses
import os
import secrets
import typing as T
from datetime import datetime, timezone
from pathlib import Path

TICKETS_DIR_NAME = ".tickets"

# -- Frontmatter field order (controls serialization order) --
_FIELD_ORDER = [
    "id", "status", "type", "priority", "assignee",
    "deps", "links", "parent", "tags", "xref", "resolution", "created",
]

# -- List-typed fields (serialized as YAML flow style) --
_LIST_FIELDS = {"deps", "links", "tags"}

# -- Nullable scalar fields (serialized as "null" when None) --
_NULLABLE_FIELDS = {"assignee", "parent", "xref", "resolution"}


# ── Exceptions ──────────────────────────────────────────────


class TicketsNotFoundError(Exception):
    """Raised when no .tickets/ directory can be located."""
    pass


class TicketNotFoundError(Exception):
    """Raised when a specific ticket file does not exist."""
    pass


class AmbiguousIDError(ValueError):
    """Raised when a partial ID matches multiple tickets."""
    pass


# ── Data model ──────────────────────────────────────────────


# [AI]
# Context: ticket-store requirement=ticket-file-format
# Intent: single dataclass holding all frontmatter fields plus optional body
@dataclasses.dataclass
class Ticket:
    id: str
    title: str
    status: str = "open"
    type: str = "task"
    priority: int = 2
    assignee: str | None = None
    deps: list[str] = dataclasses.field(default_factory=list)
    links: list[str] = dataclasses.field(default_factory=list)
    parent: str | None = None
    tags: list[str] = dataclasses.field(default_factory=list)
    xref: str | None = None
    resolution: str | None = None
    created: str = dataclasses.field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    description: str | None = None


# ── Directory walking ───────────────────────────────────────


# [AI]
# Context: ticket-store requirement=directory-walking
# Intent: find .tickets/ by walking up, with TICKETS_DIR env override
def find_tickets_dir() -> Path:
    env_override = os.environ.get("TICKETS_DIR")
    if env_override is not None:
        return Path(env_override)

    current = Path.cwd().resolve()
    while True:
        candidate = current / TICKETS_DIR_NAME
        if candidate.is_dir():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise TicketsNotFoundError("no .tickets directory found")


# ── ID generation ───────────────────────────────────────────


# [AI]
# Context: ticket-store requirement=id-generation
# Intent: <project-dir-name>-<4 hex chars>, retry on collision
def generate_id(tickets_dir: Path) -> str:
    prefix = tickets_dir.parent.name
    for _ in range(100):
        suffix = secrets.token_hex(2)  # 4 hex chars
        ticket_id = f"{prefix}-{suffix}"
        if not (tickets_dir / f"{ticket_id}.md").exists():
            return ticket_id
    raise RuntimeError("failed to generate unique ticket ID after 100 attempts")


# ── Serialization helpers ───────────────────────────────────


def _format_yaml_value(key: str, value: T.Any) -> str:
    """Format a single frontmatter value as a YAML string."""
    if key in _LIST_FIELDS:
        assert isinstance(value, list)
        if not value:
            return "[]"
        return "[" + ", ".join(str(v) for v in value) + "]"
    if key in _NULLABLE_FIELDS and value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return str(value)


def _serialize_frontmatter(ticket: Ticket) -> str:
    """Produce YAML frontmatter string (without delimiters)."""
    lines: list[str] = []
    for key in _FIELD_ORDER:
        value = getattr(ticket, key)
        lines.append(f"{key}: {_format_yaml_value(key, value)}")
    return "\n".join(lines) + "\n"


def _parse_yaml_value(key: str, raw: str) -> T.Any:
    """Parse a single YAML value back into Python."""
    raw = raw.strip()
    if key in _LIST_FIELDS:
        if raw == "[]":
            return []
        # Strip brackets, split on comma
        inner = raw.lstrip("[").rstrip("]")
        return [item.strip() for item in inner.split(",") if item.strip()]
    if key in _NULLABLE_FIELDS and raw == "null":
        return None
    if key == "priority":
        return int(raw)
    return raw


def _parse_frontmatter(text: str) -> dict[str, T.Any]:
    """Parse YAML frontmatter from between --- delimiters."""
    result: dict[str, T.Any] = {}
    for line in text.strip().splitlines():
        if ": " in line:
            key, _, value = line.partition(": ")
            key = key.strip()
            if key in _FIELD_ORDER:
                result[key] = _parse_yaml_value(key, value)
    return result


# ── File I/O ────────────────────────────────────────────────


# [AI]
# Context: ticket-store requirement=ticket-file-format
# Intent: write ticket as YAML frontmatter + markdown body
def write_ticket(ticket: Ticket, tickets_dir: Path) -> Path:
    frontmatter = _serialize_frontmatter(ticket)
    parts = [f"---\n{frontmatter}---\n", f"# {ticket.title}\n"]
    if ticket.description is not None:
        parts.append(f"\n## Description\n\n{ticket.description}\n")

    file_path = tickets_dir / f"{ticket.id}.md"
    file_path.write_text("".join(parts))
    return file_path


# [AI]
# Context: ticket-store requirement=ticket-file-format
# Intent: read and parse a ticket file back into a Ticket
def read_ticket(ticket_id: str, tickets_dir: Path) -> Ticket:
    file_path = tickets_dir / f"{ticket_id}.md"
    if not file_path.exists():
        raise TicketNotFoundError(f"ticket not found: {ticket_id}")

    content = file_path.read_text()

    # Split on --- delimiters
    parts = content.split("---\n")
    assert len(parts) >= 3, f"malformed ticket file: {file_path}"
    fm_raw = parts[1]
    body = "---\n".join(parts[2:])  # rejoin in case body contains ---

    fields = _parse_frontmatter(fm_raw)

    # Extract title from first # heading in body
    title = "Untitled"
    description: str | None = None
    for line in body.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Extract description section
    if "## Description" in body:
        desc_start = body.index("## Description") + len("## Description")
        desc_text = body[desc_start:].strip()
        if desc_text:
            description = desc_text

    return Ticket(
        title=title,
        description=description,
        **fields,
    )


# ── Listing ─────────────────────────────────────────────────


def list_ticket_ids(tickets_dir: Path) -> list[str]:
    """Return all ticket IDs in the directory."""
    return sorted(p.stem for p in tickets_dir.glob("*.md"))


# ── ID resolution ──────────────────────────────────────────


# [AI]
# Context: id-resolution requirement=partial-id-matching
# Intent: resolve partial IDs by exact match first, then unique substring
def resolve_id(partial: str, tickets_dir: Path) -> str:
    all_ids = sorted(p.stem for p in tickets_dir.glob("*.md"))

    # Exact match takes precedence unconditionally
    if partial in all_ids:
        return partial

    # Substring match
    matches = [tid for tid in all_ids if partial in tid]

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        raise TicketNotFoundError(f"ticket '{partial}' not found")

    assert len(matches) > 1
    raise AmbiguousIDError(
        f"ambiguous ID '{partial}' matches multiple tickets: {matches}"
    )

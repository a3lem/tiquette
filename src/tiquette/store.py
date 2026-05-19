from __future__ import annotations

import dataclasses
import enum
import os
import secrets
import sys
import typing as T
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path

TICKETS_DIR_NAME = ".tickets"

# -- Frontmatter field order (controls serialization order) --
_FIELD_ORDER = [
    "id",
    "status",
    "type",
    "priority",
    "assignee",
    "deps",
    "links",
    "parent",
    "tags",
    "xref",
    "created",
]

# -- List-typed fields (serialized as YAML flow style) --
_LIST_FIELDS = {"deps", "links", "tags"}

# -- Nullable scalar fields (serialized as "null" when None) --
_NULLABLE_FIELDS = {"assignee", "parent", "xref"}


# [AI]
# Context: cli-redesign-v1.2 -- ticket-store requirement=ticket-file-format
# Intent: single source of truth for status vocabulary. v1.2 renames the
#   terminal `completed` → `closed` so the stored value matches the verb (`close`).
class Status(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELED = "canceled"


# Non-member class-level constant: statuses from which no lifecycle transition is expected.
Status.TERMINAL = frozenset({Status.CLOSED, Status.CANCELED})  # type: ignore[attr-defined]

# -- Terminal statuses (no further lifecycle transitions expected) --
TERMINAL_STATUSES: frozenset[Status] = Status.TERMINAL  # type: ignore[attr-defined]


def is_terminal(status: Status) -> bool:
    return status in Status.TERMINAL  # type: ignore[attr-defined]


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


class TicketParseError(ValueError):
    """Raised when a ticket file cannot be parsed (malformed content)."""

    pass


# ── Data model ──────────────────────────────────────────────


# [AI]
# Context: ticket-store requirement=ticket-file-format
# Intent: single dataclass holding all frontmatter fields plus optional body
# [AI]
# Context: cli-redesign-v1.2 -- ticket-edit
# Intent: single shape carrying the field-changes from one `create` or `edit`
#   invocation. Both surfaces parse argparse into this, then call
#   `apply_field_changes`. Single dispatch path = one round of validation.
@dataclasses.dataclass
class FieldChanges:
    title: str | None = None
    description: str | None = None
    type: str | None = None
    priority: int | None = None
    assignee: str | None = None
    xref: str | None = None
    parent: str | None = None
    add_tags: list[str] = dataclasses.field(default_factory=list)
    remove_tags: list[str] = dataclasses.field(default_factory=list)
    add_deps: list[str] = dataclasses.field(default_factory=list)
    remove_deps: list[str] = dataclasses.field(default_factory=list)
    add_links: list[str] = dataclasses.field(default_factory=list)
    remove_links: list[str] = dataclasses.field(default_factory=list)
    notes: list[str] = dataclasses.field(default_factory=list)
    unset_fields: set[str] = dataclasses.field(default_factory=set)

    def is_empty(self) -> bool:
        """True if no actual change was requested."""
        return (
            self.title is None
            and self.description is None
            and self.type is None
            and self.priority is None
            and self.assignee is None
            and self.xref is None
            and self.parent is None
            and not self.add_tags
            and not self.remove_tags
            and not self.add_deps
            and not self.remove_deps
            and not self.add_links
            and not self.remove_links
            and not self.notes
            and not self.unset_fields
        )

    def conflicting_set_and_unset(self) -> list[str]:
        """Fields that are both set and listed in `unset_fields`."""
        conflicts: list[str] = []
        for field in self.unset_fields:
            if field == "parent" and self.parent is not None:
                conflicts.append("parent")
            elif field == "xref" and self.xref is not None:
                conflicts.append("xref")
            elif field == "assignee" and self.assignee is not None:
                conflicts.append("assignee")
        return conflicts


@dataclasses.dataclass
class Ticket:
    id: str
    title: str
    status: Status = Status.OPEN
    type: str = "task"
    priority: int = 2
    assignee: str | None = None
    deps: list[str] = dataclasses.field(default_factory=list)
    links: list[str] = dataclasses.field(default_factory=list)
    parent: str | None = None
    tags: list[str] = dataclasses.field(default_factory=list)
    xref: str | None = None
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


_VOWELS = frozenset("aeiou")


def _is_vowel(c: str) -> bool:
    return c.lower() in _VOWELS


# [AI]
# Context: user request -- abbreviate prefix to max 4 chars; prefer consonant ending
# Intent: tokenize project root on - and _, take first letter of each token.
#   If <4 chars from word starts, fill with last chars of last token.
#   Single-token names take first 4 chars.
#   If the resulting 4th char is a vowel, scan additional chars for a
#   consonant; if none found, fall back to a 3-char prefix iff char 3 is
#   itself a consonant, otherwise accept the vowel.
def _abbreviate(name: str) -> str:
    tokens = [t for t in name.replace("_", "-").split("-") if t]
    if not tokens:
        return name[:4].lower()

    if len(tokens) == 1:
        word = tokens[0].lower()
        base = word[:4]
        # extra chars to scan when char 4 is a vowel: rest of the word
        scan = word[4:]
    else:
        initials = "".join(t[0] for t in tokens)[:4].lower()
        if len(initials) >= 4:
            base = initials
            scan = ""
        else:
            last = tokens[-1].lower()
            needed = 4 - len(initials)
            tail = last[-needed:] if len(last) >= needed else last
            base = initials + tail
            # scan chars of last token before the tail, closest-to-tail first
            scan = last[:-needed][::-1] if len(last) > needed else ""

    if len(base) < 4:
        return base
    if not _is_vowel(base[3]):
        return base
    for c in scan:
        if not _is_vowel(c):
            return base[:3] + c
    if not _is_vowel(base[2]):
        return base[:3]
    return base


# [AI]
# Context: ticket-store requirement=id-generation
# Intent: <abbreviated-project-prefix>-<4 hex chars>, retry on collision
def generate_id(tickets_dir: Path) -> str:
    prefix = _abbreviate(tickets_dir.parent.name)
    for _ in range(100):
        suffix = secrets.token_hex(2)  # 4 hex chars
        ticket_id = f"{prefix}-{suffix}"
        if not (tickets_dir / f"{ticket_id}.md").exists():
            return ticket_id
    raise RuntimeError("failed to generate unique ticket ID after 100 attempts")


# ── Serialization helpers ───────────────────────────────────

# Union of all types that can appear as a parsed frontmatter value.
_FrontmatterValue = Status | str | int | list[str] | None


def _format_yaml_value(key: str, value: _FrontmatterValue) -> str:
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
        # [AI]
        # Context: fix-cli-output-gaps -- ticket-store requirement=ticket-file-format
        # Intent: omit nullable fields entirely when null so the file stays clean
        if key in _NULLABLE_FIELDS and value is None:
            continue
        lines.append(f"{key}: {_format_yaml_value(key, value)}")
    return "\n".join(lines) + "\n"


def _parse_yaml_value(key: str, raw: str) -> _FrontmatterValue:
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
    if key == "status":
        return Status(raw)
    return raw


def _parse_frontmatter(text: str) -> dict[str, _FrontmatterValue]:
    """Parse YAML frontmatter from between --- delimiters."""
    result: dict[str, _FrontmatterValue] = {}
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
    if len(parts) < 3:
        raise TicketParseError(
            f"malformed ticket file (missing frontmatter delimiters): {file_path}"
        )
    fm_raw = parts[1]
    body = "---\n".join(parts[2:])  # rejoin in case body contains ---

    fields = _parse_frontmatter(fm_raw)

    # Cross-check: frontmatter id must match the filename.
    fm_id = fields.get("id")
    if fm_id is not None and fm_id != ticket_id:
        raise TicketParseError(
            f"frontmatter id {fm_id!r} does not match filename {ticket_id!r}: {file_path}"
        )

    # Coerce and validate each known field.
    raw_status = fields.get("status", Status.OPEN)
    if not isinstance(raw_status, Status):
        try:
            raw_status = Status(str(raw_status))
        except ValueError:
            raise TicketParseError(f"invalid status {raw_status!r} in {file_path}")
    raw_priority = fields.get("priority", 2)
    if not isinstance(raw_priority, int):
        try:
            raw_priority = int(str(raw_priority))
        except ValueError:
            raise TicketParseError(f"invalid priority {raw_priority!r} in {file_path}")
    raw_assignee = fields.get("assignee")
    if raw_assignee is not None and not isinstance(raw_assignee, str):
        raise TicketParseError(f"invalid assignee {raw_assignee!r} in {file_path}")
    raw_parent = fields.get("parent")
    if raw_parent is not None and not isinstance(raw_parent, str):
        raise TicketParseError(f"invalid parent {raw_parent!r} in {file_path}")
    raw_xref = fields.get("xref")
    if raw_xref is not None and not isinstance(raw_xref, str):
        raise TicketParseError(f"invalid xref {raw_xref!r} in {file_path}")
    raw_type = fields.get("type", "task")
    if not isinstance(raw_type, str):
        raise TicketParseError(f"invalid type {raw_type!r} in {file_path}")
    raw_created = fields.get("created", "")
    if not isinstance(raw_created, str):
        raise TicketParseError(f"invalid created {raw_created!r} in {file_path}")
    raw_deps = fields.get("deps", [])
    if not isinstance(raw_deps, list):
        raise TicketParseError(f"invalid deps {raw_deps!r} in {file_path}")
    raw_links = fields.get("links", [])
    if not isinstance(raw_links, list):
        raise TicketParseError(f"invalid links {raw_links!r} in {file_path}")
    raw_tags = fields.get("tags", [])
    if not isinstance(raw_tags, list):
        raise TicketParseError(f"invalid tags {raw_tags!r} in {file_path}")

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

    # Filter self-references from links and deps.
    if ticket_id in raw_links:
        sys.stderr.write(f"warning: {file_path}: self-link removed from links list\n")
        raw_links = [lid for lid in raw_links if lid != ticket_id]
    if ticket_id in raw_deps:
        sys.stderr.write(
            f"warning: {file_path}: self-reference removed from deps list\n"
        )
        raw_deps = [did for did in raw_deps if did != ticket_id]

    return Ticket(
        id=ticket_id,
        title=title,
        description=description,
        status=raw_status,
        type=raw_type,
        priority=raw_priority,
        assignee=raw_assignee,
        deps=raw_deps,
        links=raw_links,
        parent=raw_parent,
        tags=raw_tags,
        xref=raw_xref,
        created=raw_created,
    )


# ── Listing ─────────────────────────────────────────────────


TicketSource = T.Literal["active", "archived", "all"]


# [AI]
# Context: ls-archived-flags -- ticket-query requirement=list-source-axis
# Intent: enumerate either active, archived, or both ticket sets
def list_ticket_ids(
    tickets_dir: Path,
    source: TicketSource = "active",
) -> list[str]:
    """Return ticket IDs in the directory.

    `source="active"` lists top-level tickets only (default).
    `source="archived"` lists tickets under `archive/`.
    `source="all"` lists both, deduped (active wins on collision).
    """
    if source == "active":
        return sorted(p.stem for p in tickets_dir.glob("*.md"))
    if source == "archived":
        return sorted(p.stem for p in (tickets_dir / "archive").glob("*.md"))
    active = {p.stem for p in tickets_dir.glob("*.md")}
    archived = {p.stem for p in (tickets_dir / "archive").glob("*.md")}
    return sorted(active | archived)


# ── Cycle detection ─────────────────────────────────────────


# [AI]
# Context: cli-redesign-v1.2 -- ticket-relationships requirement=cycle-detection
# Intent: dependency cycle detection. Lifted from the old `relationships`
#   command module so `edit --dep` / `create --dep` can use it.
def build_dep_graph(tickets_dir: Path) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for path in tickets_dir.glob("*.md"):
        tid = path.stem
        t = read_ticket(tid, tickets_dir)
        graph[tid] = list(t.deps)
    return graph


def has_dep_cycle(
    graph: Mapping[str, list[str]],
    extra_edges: Mapping[str, Iterable[str]],
) -> bool:
    """Return True if adding extra_edges to graph introduces a cycle.

    Pure predicate: does not mutate graph or extra_edges. Walk the virtual
    union of graph + extra_edges via DFS for each source node in extra_edges.
    """

    def _neighbours(node: str) -> list[str]:
        base = list(graph.get(node, []))
        extra = list(extra_edges.get(node, []))
        return list(set(base + extra))

    for source in extra_edges:
        # Only the newly-added edges are the entry points for cycle detection.
        seed_deps = list(extra_edges[source])
        visited: set[str] = set()
        stack: list[str] = seed_deps[:]
        while stack:
            node = stack.pop()
            if node == source:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(_neighbours(node))
    return False


# [AI]
# Context: cli-redesign-v1.2 -- ticket-relationships requirement=cycle-detection
# Intent: parent cycle detection. Walk from `new_parent` up via `.parent`;
#   if we ever land on `child_id` (or back on `new_parent` itself via a
#   pre-existing cycle), it's a cycle.
def has_parent_cycle(
    child_id: str,
    new_parent: str,
    tickets_dir: Path,
) -> bool:
    if child_id == new_parent:
        return True
    visited: set[str] = set()
    cursor: str | None = new_parent
    while cursor is not None:
        if cursor == child_id:
            return True
        if cursor in visited:
            return False  # pre-existing cycle in ancestors, not ours
        visited.add(cursor)
        try:
            t = read_ticket(cursor, tickets_dir)
        except TicketNotFoundError:
            return False
        cursor = t.parent
    return False


# ── Field-change application ────────────────────────────────


class FieldChangeError(ValueError):
    """Raised when `apply_field_changes` rejects the requested changes."""

    pass


def _append_note(ticket: Ticket, text: str, timestamp: str) -> None:
    """Append a timestamped note to the ticket's body."""
    note_line = f"- {timestamp}: {text}"
    if ticket.description is None:
        ticket.description = ""
    body = ticket.description
    if "## Notes" in body:
        ticket.description = body.rstrip() + "\n" + note_line + "\n"
    else:
        sep = "\n\n" if body.strip() else ""
        ticket.description = body.rstrip() + sep + "## Notes\n\n" + note_line + "\n"


# [AI]
# Context: cli-redesign-v1.2 -- ticket-edit
# Intent: apply a FieldChanges to an in-memory Ticket. Validates cycles,
#   resolves dep/link/parent targets exist, handles symmetric link writes.
#   Returns a list of (ticket, dir) writes the caller must perform; the
#   caller writes them atomically (all-or-nothing).
def apply_field_changes(
    ticket: Ticket,
    changes: FieldChanges,
    tickets_dir: Path,
    *,
    note_timestamp: str | None = None,
) -> list[Ticket]:
    """Mutate `ticket` per `changes`. Return additional tickets that must
    also be written (for symmetric link/unlink). Raises FieldChangeError
    on validation failure; on failure no ticket has been mutated yet.
    """
    # Validate first (no mutation) — atomicity
    conflicts = changes.conflicting_set_and_unset()
    if conflicts:
        raise FieldChangeError(
            f"cannot both set and unset {', '.join(repr(f) for f in conflicts)} in one call"
        )

    # [AI]
    # Context: id-resolution requirement=id-resolution-across-commands
    # Intent: callers pass partial IDs for --dep/--link/--parent/--undep/--unlink
    #   values. Resolve them to full IDs here so the rest of this function (and
    #   the on-disk representation) sees canonical IDs only.
    def _resolve(partial: str) -> str:
        try:
            return resolve_id(partial, tickets_dir)
        except (TicketNotFoundError, AmbiguousIDError) as exc:
            raise FieldChangeError(str(exc)) from exc

    # Removal targets stay as-is if not resolvable; they're filtered against
    # the ticket's actual deps/links downstream, so an unknown ID is a no-op.
    def _resolve_optional(partial: str) -> str:
        try:
            return resolve_id(partial, tickets_dir)
        except (TicketNotFoundError, AmbiguousIDError):
            return partial

    changes.add_deps = [_resolve(d) for d in changes.add_deps]
    changes.remove_deps = [_resolve_optional(d) for d in changes.remove_deps]
    changes.add_links = [_resolve(link) for link in changes.add_links]
    changes.remove_links = [_resolve_optional(link) for link in changes.remove_links]
    if changes.parent is not None:
        changes.parent = _resolve(changes.parent)

    # Load link targets (existence already proven by resolve)
    link_targets: dict[str, Ticket] = {}
    for link_id in changes.add_links:
        if link_id == ticket.id:
            continue
        link_targets[link_id] = read_ticket(link_id, tickets_dir)
    unlink_targets: dict[str, Ticket] = {}
    for link_id in changes.remove_links:
        if link_id == ticket.id:
            continue
        unlink_targets[link_id] = read_ticket(link_id, tickets_dir)

    # Parent cycle check (existence already proven by resolve)
    if changes.parent is not None:
        if has_parent_cycle(ticket.id, changes.parent, tickets_dir):
            raise FieldChangeError(
                f"setting parent of '{ticket.id}' to '{changes.parent}' would create a cycle"
            )

    # Dep cycle check
    new_deps_set = [d for d in changes.add_deps if d not in ticket.deps]
    if new_deps_set:
        graph = build_dep_graph(tickets_dir)
        if has_dep_cycle(graph, {ticket.id: new_deps_set}):
            raise FieldChangeError(
                f"adding dependency to '{ticket.id}' would create a cycle"
            )

    # ── Mutations (validation passed) ──
    if changes.title is not None:
        ticket.title = changes.title
    if changes.description is not None:
        ticket.description = changes.description
    if changes.type is not None:
        ticket.type = changes.type
    if changes.priority is not None:
        ticket.priority = changes.priority
    if changes.assignee is not None:
        ticket.assignee = changes.assignee
    if changes.xref is not None:
        ticket.xref = changes.xref
    if changes.parent is not None:
        ticket.parent = changes.parent

    # Tag add/remove
    existing_tags = set(ticket.tags)
    for tag in changes.add_tags:
        if tag not in existing_tags:
            ticket.tags.append(tag)
            existing_tags.add(tag)
    if changes.remove_tags:
        to_remove = set(changes.remove_tags)
        ticket.tags = [t for t in ticket.tags if t not in to_remove]

    # Dep add/remove
    existing_deps = set(ticket.deps)
    for dep in changes.add_deps:
        if dep not in existing_deps:
            ticket.deps.append(dep)
            existing_deps.add(dep)
    if changes.remove_deps:
        to_remove = set(changes.remove_deps)
        ticket.deps = [d for d in ticket.deps if d not in to_remove]

    # Link add/remove (symmetric)
    extra_writes: list[Ticket] = []
    existing_links = set(ticket.links)
    for link_id, target in link_targets.items():
        if link_id not in existing_links:
            ticket.links.append(link_id)
            existing_links.add(link_id)
        if ticket.id not in target.links:
            target.links.append(ticket.id)
            extra_writes.append(target)
    if changes.remove_links:
        to_remove = set(changes.remove_links)
        ticket.links = [link for link in ticket.links if link not in to_remove]
        for link_id, target in unlink_targets.items():
            if ticket.id in target.links:
                target.links.remove(ticket.id)
                if target not in extra_writes:
                    extra_writes.append(target)

    # Unset
    if "parent" in changes.unset_fields:
        ticket.parent = None
    if "xref" in changes.unset_fields:
        ticket.xref = None
    if "assignee" in changes.unset_fields:
        ticket.assignee = None

    # Notes
    if changes.notes:
        ts = note_timestamp or datetime.now(timezone.utc).isoformat()
        for note in changes.notes:
            _append_note(ticket, note, ts)

    return extra_writes


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

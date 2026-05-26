from __future__ import annotations

import dataclasses
import enum
import os
import secrets
import sys
import typing as T
from collections.abc import Iterable, Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path

from tiquette.timestamps import now_iso

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

# -- Fields clearable via `tq edit --unset`. Ordered for stable diagnostics. --
UNSET_TARGETS: tuple[str, ...] = ("parent", "xref", "assignee")

# -- All frontmatter keys that read_ticket recognises. Any other key is an error. --
_KNOWN_FRONTMATTER_KEYS: frozenset[str] = frozenset(
    {"id", "status", "type", "priority", "assignee", "deps", "links", "parent", "tags", "xref", "created"}
)


# [AI]
# Context: cli-redesign-v1.2 -- ticket-store requirement=ticket-file-format
# Intent: single source of truth for status vocabulary. v1.2 renames the
#   terminal `completed` → `closed` so the stored value matches the verb (`close`).
class Status(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELED = "canceled"


# -- Terminal statuses (no further lifecycle transitions expected) --
TERMINAL_STATUSES: frozenset[Status] = frozenset({Status.CLOSED, Status.CANCELED})


def is_terminal(status: Status) -> bool:
    return status in TERMINAL_STATUSES


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
        return [
            field
            for field in UNSET_TARGETS
            if field in self.unset_fields and getattr(self, field) is not None
        ]


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
    created: str = dataclasses.field(default_factory=lambda: now_iso())
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
def abbreviate(name: str) -> str:
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
    prefix = abbreviate(tickets_dir.parent.name)
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
    # [AI]
    # Context: tiqt-280e -- status validation belongs in read_ticket, not in
    #   _parse_yaml_value. Returning the raw string lets read_ticket wrap the
    #   coercion failure in TicketParseError (with file path) instead of letting
    #   a bare ValueError escape through validate/show/ls.
    return raw


def _parse_frontmatter(text: str, file_path: Path | None = None) -> dict[str, _FrontmatterValue]:
    """Parse YAML frontmatter from between --- delimiters.

    Raises TicketParseError for malformed lines or unknown keys.
    """
    result: dict[str, _FrontmatterValue] = {}
    location = f" in {file_path}" if file_path else ""
    for line in text.strip().splitlines():
        if not line:
            continue
        if ": " not in line and not line.endswith(":"):
            raise TicketParseError(f"malformed frontmatter line: {line!r}{location}")
        key, _, value = line.partition(": ")
        key = key.strip()
        if key not in _KNOWN_FRONTMATTER_KEYS:
            raise TicketParseError(f"unknown frontmatter key {key!r}{location}")
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
# Context: tiqt-6893 -- collapse repeated isinstance dance in read_ticket.
# Intent: every typed-field extractor raises TicketParseError uniformly when
#   the YAML value is the wrong shape; defaults apply only when the key is
#   absent. Centralizing this means every required field treats "missing" the
#   same way, eliminating the previous quirk where `created` defaulted to "".
def _required_str(
    fields: Mapping[str, _FrontmatterValue], key: str, default: str, file_path: Path
) -> str:
    value = fields.get(key, default)
    if not isinstance(value, str):
        raise TicketParseError(f"invalid {key} {value!r} in {file_path}")
    return value


def _optional_str(
    fields: Mapping[str, _FrontmatterValue], key: str, file_path: Path
) -> str | None:
    value = fields.get(key)
    if value is not None and not isinstance(value, str):
        raise TicketParseError(f"invalid {key} {value!r} in {file_path}")
    return value


def _required_list(
    fields: Mapping[str, _FrontmatterValue], key: str, file_path: Path
) -> list[str]:
    value = fields.get(key, [])
    if not isinstance(value, list):
        raise TicketParseError(f"invalid {key} {value!r} in {file_path}")
    return value


# [AI]
# Context: ticket-store requirement=ticket-file-format
# Intent: read and parse a ticket file back into a Ticket
def read_ticket(ticket_id: str, tickets_dir: Path) -> Ticket:
    return _read_ticket_and_body(ticket_id, tickets_dir)[0]


def read_ticket_with_body(ticket_id: str, tickets_dir: Path) -> tuple[Ticket, str]:
    return _read_ticket_and_body(ticket_id, tickets_dir)


def _read_ticket_and_body(ticket_id: str, tickets_dir: Path) -> tuple[Ticket, str]:
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
    body = "---\n".join(parts[2:]).strip() if len(parts) >= 3 else ""

    fields = _parse_frontmatter(fm_raw, file_path)

    # Cross-check: frontmatter id must match the filename.
    fm_id = fields.get("id")
    if fm_id is not None and fm_id != ticket_id:
        raise TicketParseError(
            f"frontmatter id {fm_id!r} does not match filename {ticket_id!r}: {file_path}"
        )

    # Status accepts coercion from string (legacy YAML); priority from int.
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

    raw_assignee = _optional_str(fields, "assignee", file_path)
    raw_parent = _optional_str(fields, "parent", file_path)
    raw_xref = _optional_str(fields, "xref", file_path)
    raw_type = _required_str(fields, "type", "task", file_path)
    raw_created = _required_str(fields, "created", "", file_path)
    raw_deps = _required_list(fields, "deps", file_path)
    raw_links = _required_list(fields, "links", file_path)
    raw_tags = _required_list(fields, "tags", file_path)

    # Title: first non-empty line after the closing ---. Strip leading "# " if present.
    title = "Untitled"
    description: str | None = None
    body_lines = body.splitlines()
    title_idx = -1
    for i, line in enumerate(body_lines):
        if line.strip():
            title = line[2:].strip() if line.startswith("# ") else line.strip()
            title_idx = i
            break

    # Description: everything after the first line whose stripped form is exactly
    # "## Description". Substring matches inside paragraphs are intentionally ignored.
    desc_marker_idx = -1
    for i, line in enumerate(body_lines):
        if line.strip() == "## Description":
            desc_marker_idx = i
            desc_text = "\n".join(body_lines[i + 1:]).strip()
            if desc_text:
                description = desc_text
            break

    # [AI] tiqt-0896: fall back to capturing the full post-title body when no
    # `## Description` marker is present. Without this fallback, hand-edited
    # tickets carrying only a `## Notes` section (no Description header) lose
    # their Notes on round-trip through write_ticket -- the very bug that bit
    # `tq autofix`'s prefix-rename. On the next write the body normalises into
    # the standard `## Description\n\n<content>` layout.
    if description is None and desc_marker_idx == -1 and title_idx != -1:
        tail = "\n".join(body_lines[title_idx + 1:]).strip()
        if tail:
            description = tail

    # Filter self-references from links and deps.
    if ticket_id in raw_links:
        sys.stderr.write(f"warning: {file_path}: self-link removed from links list\n")
        raw_links = [lid for lid in raw_links if lid != ticket_id]
    if ticket_id in raw_deps:
        sys.stderr.write(
            f"warning: {file_path}: self-reference removed from deps list\n"
        )
        raw_deps = [did for did in raw_deps if did != ticket_id]

    ticket = Ticket(
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

    return (ticket, body)


# ── Listing ─────────────────────────────────────────────────


TicketSource = T.Literal["active", "archived", "all"]


def iter_tickets(
    tickets_dir: Path,
    *,
    source: TicketSource = "active",
    include_archive: bool = False,
) -> Iterator[Ticket]:
    """Yield every ticket in `tickets_dir` for the requested source.

    `source="active"` (default) yields only top-level tickets.
    `source="archived"` yields only archived tickets.
    `source="all"` yields active tickets first, then archived.

    `include_archive` is a deprecated alias for `source="all"`.
    """
    if include_archive and source == "active":
        source = "all"
    archive_dir = tickets_dir / "archive"
    if source in ("active", "all"):
        for path in sorted(tickets_dir.glob("*.md")):
            yield read_ticket(path.stem, tickets_dir)
    if source in ("archived", "all"):
        if archive_dir.is_dir():
            for path in sorted(archive_dir.glob("*.md")):
                yield read_ticket(path.stem, archive_dir)


def load_all_tickets(
    tickets_dir: Path,
    source: TicketSource = "active",
) -> dict[str, Ticket]:
    """Load all tickets from the requested source(s) into a dict keyed by ID.

    `source="active"` (default) loads only top-level tickets.
    `source="archived"` loads only archived tickets.
    `source="all"` loads both; on ID collision active wins (active is yielded
    first by iter_tickets, so later archived entries do not overwrite them).
    """
    if source == "all":
        # Active tickets are yielded first; archived entries must not overwrite.
        result: dict[str, Ticket] = {}
        for t in iter_tickets(tickets_dir, source="all"):
            result.setdefault(t.id, t)
        return result
    return {t.id: t for t in iter_tickets(tickets_dir, source=source)}


# ── Cycle detection ─────────────────────────────────────────


# [AI]
# Context: cli-redesign-v1.2 -- ticket-relationships requirement=cycle-detection
# Intent: dependency cycle detection. Lifted from the old `relationships`
#   command module so `edit --dep` / `create --dep` can use it.
def build_dep_graph(tickets_dir: Path) -> dict[str, list[str]]:
    return {t.id: list(t.deps) for t in iter_tickets(tickets_dir)}


def has_dep_cycle(
    graph: Mapping[str, list[str]],
    source: str,
    new_deps: Iterable[str],
) -> bool:
    """Return True if adding new_deps from source introduces a cycle.

    Pure predicate: does not mutate graph. Walks the virtual union of
    graph + {source: new_deps} via DFS from source.
    """
    seed = list(new_deps)
    extra = set(seed)

    def _neighbours(node: str) -> list[str]:
        base = list(graph.get(node, []))
        if node == source:
            return list(set(base) | extra)
        return base

    visited: set[str] = set()
    stack: list[str] = seed[:]
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
    *,
    tickets: dict[str, Ticket] | None = None,
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
        if tickets is not None:
            t = tickets.get(cursor)
            if t is None:
                return False
            cursor = t.parent
        else:
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


def _append_note(
    ticket: Ticket, text: str, timestamp: str, tag: str | None = None
) -> None:
    """Append a timestamped note to the ticket's body.

    When `tag` is supplied, the entry is prefixed with `[<tag>]:` after the
    timestamp; otherwise the entry is the existing `- <timestamp>: <text>` form.
    """
    if tag is not None:
        note_line = f"- {timestamp} [{tag}]: {text}"
    else:
        note_line = f"- {timestamp}: {text}"
    if ticket.description is None:
        ticket.description = ""
    body = ticket.description
    if "## Notes" in body:
        ticket.description = body.rstrip() + "\n" + note_line + "\n"
    else:
        sep = "\n\n" if body.strip() else ""
        ticket.description = body.rstrip() + sep + "## Notes\n\n" + note_line + "\n"


@dataclasses.dataclass
class _ValidatedChanges:
    """Resolved, cycle-checked data produced by _validate_changes."""

    changes: FieldChanges  # mutations in original form (notes, unset_fields, etc.)
    resolved_add_deps: list[str]
    resolved_remove_deps: list[str]
    resolved_add_links: list[str]
    resolved_remove_links: list[str]
    resolved_parent: str | None  # None means "no change", not "unset"
    link_targets: dict[str, Ticket]
    unlink_targets: dict[str, Ticket]


def _validate_changes(
    ticket: Ticket,
    changes: FieldChanges,
    tickets_dir: Path,
) -> _ValidatedChanges:
    """Validate and resolve all IDs in `changes` for `ticket`.

    Raises FieldChangeError on any conflict, resolution failure, or cycle.
    Does not mutate `ticket`.
    """
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
            return resolve_id_in_dir(partial, tickets_dir)
        except (TicketNotFoundError, AmbiguousIDError) as exc:
            raise FieldChangeError(str(exc)) from exc

    # Removal targets: a non-existent ID is a no-op (filtered downstream),
    # but an ambiguous ID is always an error so the user sees it.
    def _resolve_optional(partial: str) -> str:
        try:
            return resolve_id_in_dir(partial, tickets_dir)
        except AmbiguousIDError as exc:
            raise FieldChangeError(str(exc)) from exc
        except TicketNotFoundError:
            return partial

    resolved_add_deps = [_resolve(d) for d in changes.add_deps]
    resolved_remove_deps = [_resolve_optional(d) for d in changes.remove_deps]
    resolved_add_links = [_resolve(link) for link in changes.add_links]
    resolved_remove_links = [_resolve_optional(link) for link in changes.remove_links]
    resolved_parent = _resolve(changes.parent) if changes.parent is not None else None

    # Load link targets (existence already proven by resolve)
    link_targets: dict[str, Ticket] = {}
    for link_id in resolved_add_links:
        if link_id == ticket.id:
            continue
        link_targets[link_id] = read_ticket(link_id, tickets_dir)
    unlink_targets: dict[str, Ticket] = {}
    for link_id in resolved_remove_links:
        if link_id == ticket.id:
            continue
        unlink_targets[link_id] = read_ticket(link_id, tickets_dir)

    # Build ticket map once when needed for cycle checks.
    tickets_map: dict[str, Ticket] | None = None

    def _tickets_map() -> dict[str, Ticket]:
        nonlocal tickets_map
        if tickets_map is None:
            tickets_map = load_all_tickets(tickets_dir)
        return tickets_map

    # Parent cycle check (existence already proven by resolve)
    if resolved_parent is not None:
        if has_parent_cycle(
            ticket.id, resolved_parent, tickets_dir, tickets=_tickets_map()
        ):
            raise FieldChangeError(
                f"setting parent of '{ticket.id}' to '{resolved_parent}' would create a cycle"
            )

    # Dep cycle check
    new_deps = [d for d in resolved_add_deps if d not in ticket.deps]
    if new_deps:
        graph = {t.id: list(t.deps) for t in _tickets_map().values()}
        if has_dep_cycle(graph, ticket.id, new_deps):
            raise FieldChangeError(
                f"adding dependency to '{ticket.id}' would create a cycle"
            )

    return _ValidatedChanges(
        changes=changes,
        resolved_add_deps=resolved_add_deps,
        resolved_remove_deps=resolved_remove_deps,
        resolved_add_links=resolved_add_links,
        resolved_remove_links=resolved_remove_links,
        resolved_parent=resolved_parent,
        link_targets=link_targets,
        unlink_targets=unlink_targets,
    )


def _merge_unique(
    existing: list[str], additions: Iterable[str], removals: Iterable[str]
) -> list[str]:
    """Return `existing` with `additions` appended (deduped) and `removals` filtered out."""
    seen = set(existing)
    result = list(existing)
    for item in additions:
        if item not in seen:
            result.append(item)
            seen.add(item)
    to_remove = set(removals)
    if to_remove:
        result = [item for item in result if item not in to_remove]
    return result


def _apply_validated(
    ticket: Ticket,
    validated: _ValidatedChanges,
    *,
    note_timestamp: str | None = None,
) -> list[Ticket]:
    """Apply pre-validated changes to `ticket`. Only mutates; no validation."""
    changes = validated.changes

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
    if validated.resolved_parent is not None:
        ticket.parent = validated.resolved_parent

    ticket.tags = _merge_unique(ticket.tags, changes.add_tags, changes.remove_tags)
    ticket.deps = _merge_unique(
        ticket.deps, validated.resolved_add_deps, validated.resolved_remove_deps
    )

    # Links: same merge for the local side, plus symmetric back-writes to targets.
    extra_writes: list[Ticket] = []
    ticket.links = _merge_unique(
        ticket.links, validated.link_targets.keys(), validated.resolved_remove_links
    )
    for target in validated.link_targets.values():
        if ticket.id not in target.links:
            target.links.append(ticket.id)
            extra_writes.append(target)
    for target in validated.unlink_targets.values():
        if ticket.id in target.links:
            target.links.remove(ticket.id)
            if target not in extra_writes:
                extra_writes.append(target)

    for field in UNSET_TARGETS:
        if field in changes.unset_fields:
            setattr(ticket, field, None)

    # Notes
    if changes.notes:
        ts = note_timestamp or now_iso()
        for note in changes.notes:
            _append_note(ticket, note, ts)

    return extra_writes


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
    """Validate `changes` then mutate `ticket`. Return additional tickets that
    must also be written (for symmetric link/unlink). Raises FieldChangeError
    on validation failure; on failure no ticket has been mutated yet.
    """
    validated = _validate_changes(ticket, changes, tickets_dir)
    return _apply_validated(ticket, validated, note_timestamp=note_timestamp)


# ── ID resolution ──────────────────────────────────────────


# [AI]
# Context: id-resolution requirement=partial-id-matching
# Intent: resolve partial IDs by exact match first, then unique substring.
#   Accepts any iterable of candidate IDs so callers can scope to a pre-loaded
#   set (e.g. archived+active combined) without another filesystem scan.
def resolve_id(partial: str, candidates: Iterable[str]) -> str:
    all_ids = sorted(candidates)

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


def resolve_id_in_dir(partial: str, tickets_dir: Path) -> str:
    """Resolve a partial ticket ID against .md files in `tickets_dir`."""
    return resolve_id(partial, (p.stem for p in tickets_dir.glob("*.md")))

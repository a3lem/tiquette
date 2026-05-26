from __future__ import annotations

from datetime import datetime, timezone

# [AI] Single home for ticket timestamp formatting. Centralised so the
# write format cannot drift across call sites (store/lifecycle/edit all
# import from here).

_WRITE_FMT = "%Y-%m-%dT%H:%MZ"


def to_iso(dt: datetime) -> str:
    # [AI] Formats any datetime in the current write format. UTC-naive datetimes
    # are assumed UTC; aware datetimes are converted to UTC before formatting.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime(_WRITE_FMT)


def now_iso() -> str:
    # [AI] Minute precision, Zulu suffix. Used for `created` and Notes entries.
    return to_iso(datetime.now(timezone.utc))


def parse_iso(s: str) -> datetime:
    # [AI] Accepts the current write format (`...HH:MMZ`) and the legacy
    # microsecond+offset format (`...HH:MM:SS.ffffff+00:00`). Python 3.11+
    # fromisoformat handles `Z` natively, but normalising here keeps the
    # parse path explicit and one-stop for future format variants.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)

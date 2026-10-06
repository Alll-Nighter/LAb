"""Analytics module for the LLM Service.

Extracts violation records and computes summary KPIs (totals, breakdowns by
type/zone/hour, top entities, peak hour, repeat violators) to feed into prompt
templates. Never sends raw records directly to the LLM.
"""

from collections import Counter
from datetime import datetime
from typing import Any

# Default label for missing or unknown fields
UNKNOWN_LABEL: str = "UNKNOWN"


def extract_violations(data: Any) -> list[dict]:
    """Extract a list of violation dictionaries from various payload shapes.

    Accepts:
        - A list of dicts (e.g. ``[{"camera_id": 0, ...}, ...]``)
        - A dict containing a ``"violations"`` key with a list of dicts
          (e.g. ``{"violations": [...]}``)

    Returns:
        A list of violation dicts, or ``[]`` if input is invalid or empty.
    """
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        violations = data.get("violations")
        if isinstance(violations, list):
            return [item for item in violations if isinstance(item, dict)]
    return []


def _parse_hour(timestamp_raw: Any) -> str:
    """Parse hour ("00" - "23") from an ISO-like timestamp string.

    Handles ISO formats like "2026-10-01T11:42:10", "2026-10-01 11:42:10",
    trailing 'Z' (e.g. "2026-10-01T11:42:10Z"), and sub-second precision.
    Returns UNKNOWN_LABEL if parsing fails.
    """
    if not isinstance(timestamp_raw, str) or not timestamp_raw.strip():
        return UNKNOWN_LABEL

    ts = timestamp_raw.strip()
    if ts.endswith(("Z", "z")):
        ts = ts[:-1]

    # Try ISO parsing first
    try:
        dt = datetime.fromisoformat(ts)
        return f"{dt.hour:02d}"
    except (ValueError, TypeError):
        pass

    # Fallback to manual string slicing if format has HH:MM:SS
    # Look for 'T' or space separator
    for sep in ("T", " "):
        if sep in ts:
            time_part = ts.split(sep)[1]
            hour_str = time_part.split(":")[0]
            if hour_str.isdigit() and 0 <= int(hour_str) <= 23:
                return f"{int(hour_str):02d}"

    return UNKNOWN_LABEL


def _stable_top(counts: dict[str, int]) -> str | None:
    """Find the top entity with deterministic tie-breaking.

    Ties broken alphabetically by key. Returns None if counts is empty.
    """
    if not counts:
        return None
    # Sort by (-count, key)
    sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return sorted_items[0][0]


def _format_peak_hour(hour_str: str | None) -> str | None:
    """Format an hour string "HH" to "HH:00-(HH+1):00".

    Example: "11" -> "11:00-12:00", "23" -> "23:00-00:00".
    """
    if not hour_str or hour_str == UNKNOWN_LABEL:
        return None
    try:
        start_h = int(hour_str)
        end_h = (start_h + 1) % 24
        return f"{start_h:02d}:00-{end_h:02d}:00"
    except ValueError:
        return None


def compute_kpis(violations: list[dict]) -> dict:
    """Compute aggregated KPIs from a list of violation records.

    Tolerates missing fields and extra fields. Missing fields are treated as "UNKNOWN".

    Args:
        violations: List of violation dictionaries.

    Returns:
        A dictionary containing:
            - total (int): Total number of violations.
            - by_type (dict[str, int]): Count per violation type.
            - by_zone (dict[str, int]): Count per zone.
            - by_hour (dict[str, int]): Count for each hour ("00" to "23").
            - top_type (str | None): Most common violation type (tie-break alphabetically).
            - top_zone (str | None): Most violated zone (tie-break alphabetically).
            - peak_hour (str | None): Formatted peak hour window, e.g. "11:00-12:00".
            - repeat_violators (list[dict]): List of ``{"track_id": int | str, "count": int}``
              for tracks with count > 1, sorted by count descending then track_id.
    """
    # Initialize 24-hour distribution
    by_hour: dict[str, int] = {f"{h:02d}": 0 for h in range(24)}
    by_type: dict[str, int] = {}
    by_zone: dict[str, int] = {}
    track_counts: Counter = Counter()

    total = len(violations)

    for item in violations:
        # Extract fields with safe defaults
        v_type = item.get("violation_type")
        v_type_str = (
            str(v_type).strip()
            if v_type is not None and str(v_type).strip()
            else UNKNOWN_LABEL
        )
        by_type[v_type_str] = by_type.get(v_type_str, 0) + 1

        zone = item.get("zone")
        zone_str = (
            str(zone).strip()
            if zone is not None and str(zone).strip()
            else UNKNOWN_LABEL
        )
        by_zone[zone_str] = by_zone.get(zone_str, 0) + 1

        hour = _parse_hour(item.get("timestamp"))
        if hour in by_hour:
            by_hour[hour] += 1

        track_id = item.get("track_id")
        if track_id is not None:
            track_counts[track_id] += 1

    # Top type & zone
    top_type = _stable_top(by_type)
    top_zone = _stable_top(by_zone)

    # Peak hour (only consider hours with count > 0; tie-break by earlier hour)
    active_hours = {h: cnt for h, cnt in by_hour.items() if cnt > 0}
    peak_hour_str = _stable_top(active_hours)
    peak_hour = _format_peak_hour(peak_hour_str)

    # Repeat violators: track_id with > 1 violation
    # Sort by count desc, then str(track_id) asc for stable ordering
    repeat_violators = [
        {"track_id": tid, "count": cnt}
        for tid, cnt in sorted(
            track_counts.items(),
            key=lambda item: (-item[1], str(item[0])),
        )
        if cnt > 1
    ]

    return {
        "total": total,
        "by_type": by_type,
        "by_zone": by_zone,
        "by_hour": by_hour,
        "top_type": top_type,
        "top_zone": top_zone,
        "peak_hour": peak_hour,
        "repeat_violators": repeat_violators,
    }

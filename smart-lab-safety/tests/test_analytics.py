"""Unit tests for the analytics module (llm_service.analytics).

Tests compute_kpis and extract_violations covering normal data, empty inputs,
repeat violators, missing fields, timestamp variations (ISO, trailing Z),
deterministic tie-breaking, and malformed inputs.
"""

from llm_service.analytics import (
    UNKNOWN_LABEL,
    compute_kpis,
    extract_violations,
)


def test_compute_kpis_normal_data() -> None:
    """Test KPI computation with standard valid violation records."""
    # Arrange
    violations = [
        {
            "camera_id": 0,
            "zone": "Workbench-1",
            "track_id": 1,
            "violation_type": "NO_HELMET",
            "timestamp": "2026-10-01T09:15:00",
            "confidence": 0.90,
        },
        {
            "camera_id": 0,
            "zone": "Workbench-1",
            "track_id": 2,
            "violation_type": "NO_HELMET",
            "timestamp": "2026-10-01T09:45:00",
            "confidence": 0.85,
        },
        {
            "camera_id": 1,
            "zone": "Storage-Area",
            "track_id": 3,
            "violation_type": "NO_VEST",
            "timestamp": "2026-10-01T14:20:00",
            "confidence": 0.92,
        },
    ]

    # Act
    kpis = compute_kpis(violations)

    # Assert
    assert kpis["total"] == 3
    assert kpis["by_type"] == {"NO_HELMET": 2, "NO_VEST": 1}
    assert kpis["by_zone"] == {"Workbench-1": 2, "Storage-Area": 1}
    assert kpis["by_hour"]["09"] == 2
    assert kpis["by_hour"]["14"] == 1
    assert kpis["by_hour"]["00"] == 0
    assert len(kpis["by_hour"]) == 24
    assert kpis["top_type"] == "NO_HELMET"
    assert kpis["top_zone"] == "Workbench-1"
    assert kpis["peak_hour"] == "09:00-10:00"
    assert kpis["repeat_violators"] == []


def test_compute_kpis_empty_list() -> None:
    """Test KPI computation when given an empty list of violations."""
    # Arrange
    violations: list[dict] = []

    # Act
    kpis = compute_kpis(violations)

    # Assert
    assert kpis["total"] == 0
    assert kpis["by_type"] == {}
    assert kpis["by_zone"] == {}
    assert len(kpis["by_hour"]) == 24
    assert all(count == 0 for count in kpis["by_hour"].values())
    assert kpis["top_type"] is None
    assert kpis["top_zone"] is None
    assert kpis["peak_hour"] is None
    assert kpis["repeat_violators"] == []


def test_compute_kpis_repeat_violators() -> None:
    """Test tracking repeat violators (track_ids with > 1 violation)."""
    # Arrange
    violations = [
        {
            "track_id": 10,
            "zone": "Zone-A",
            "violation_type": "NO_HELMET",
            "timestamp": "2026-10-01T10:00:00",
        },
        {
            "track_id": 20,
            "zone": "Zone-A",
            "violation_type": "NO_HELMET",
            "timestamp": "2026-10-01T10:05:00",
        },
        {
            "track_id": 10,
            "zone": "Zone-B",
            "violation_type": "NO_VEST",
            "timestamp": "2026-10-01T11:00:00",
        },
        {
            "track_id": 30,
            "zone": "Zone-B",
            "violation_type": "NO_HELMET",
            "timestamp": "2026-10-01T11:10:00",
        },
        {
            "track_id": 10,
            "zone": "Zone-A",
            "violation_type": "NO_GOGGLES",
            "timestamp": "2026-10-01T12:00:00",
        },
        {
            "track_id": 20,
            "zone": "Zone-C",
            "violation_type": "NO_VEST",
            "timestamp": "2026-10-01T12:30:00",
        },
    ]

    # Act
    kpis = compute_kpis(violations)

    # Assert
    assert kpis["total"] == 6
    # Track 10 has 3 violations, Track 20 has 2 violations, Track 30 has 1 violation (excluded)
    assert kpis["repeat_violators"] == [
        {"track_id": 10, "count": 3},
        {"track_id": 20, "count": 2},
    ]


def test_compute_kpis_missing_fields() -> None:
    """Test handling of records missing optional/required fields."""
    # Arrange
    violations = [
        {"camera_id": 0},  # all main fields missing
        {"zone": None, "violation_type": "", "timestamp": None, "track_id": None},
        {"zone": "Zone-A", "violation_type": "NO_HELMET", "timestamp": "invalid-time"},
    ]

    # Act
    kpis = compute_kpis(violations)

    # Assert
    assert kpis["total"] == 3
    assert UNKNOWN_LABEL in kpis["by_type"]
    assert kpis["by_type"][UNKNOWN_LABEL] == 2
    assert kpis["by_type"]["NO_HELMET"] == 1
    assert UNKNOWN_LABEL in kpis["by_zone"]
    assert kpis["by_zone"][UNKNOWN_LABEL] == 2
    assert kpis["by_zone"]["Zone-A"] == 1
    assert kpis["repeat_violators"] == []


def test_compute_kpis_timestamp_formats_and_z() -> None:
    """Test timestamp parsing with trailing Z, space separator, and standard ISO."""
    # Arrange
    violations = [
        {
            "timestamp": "2026-10-01T11:42:10Z",
            "violation_type": "NO_HELMET",
            "zone": "Z1",
        },
        {
            "timestamp": "2026-10-01T11:55:00z",
            "violation_type": "NO_HELMET",
            "zone": "Z1",
        },
        {
            "timestamp": "2026-10-01 11:30:00",
            "violation_type": "NO_HELMET",
            "zone": "Z1",
        },
        {"timestamp": "2026-10-01T23:15:00", "violation_type": "NO_VEST", "zone": "Z2"},
    ]

    # Act
    kpis = compute_kpis(violations)

    # Assert
    assert kpis["by_hour"]["11"] == 3
    assert kpis["by_hour"]["23"] == 1
    assert kpis["peak_hour"] == "11:00-12:00"


def test_compute_kpis_tie_breaking() -> None:
    """Test stable alphabetical tie-breaking for top_type, top_zone, and peak_hour."""
    # Arrange: NO_HELMET vs NO_VEST (both count 2), Zone-B vs Zone-A (both count 2), hour 08 vs 14 (both count 2)
    violations = [
        {
            "violation_type": "NO_VEST",
            "zone": "Zone-B",
            "timestamp": "2026-10-01T14:00:00",
        },
        {
            "violation_type": "NO_VEST",
            "zone": "Zone-B",
            "timestamp": "2026-10-01T14:30:00",
        },
        {
            "violation_type": "NO_HELMET",
            "zone": "Zone-A",
            "timestamp": "2026-10-01T08:00:00",
        },
        {
            "violation_type": "NO_HELMET",
            "zone": "Zone-A",
            "timestamp": "2026-10-01T08:30:00",
        },
    ]

    # Act
    kpis = compute_kpis(violations)

    # Assert
    # NO_HELMET < NO_VEST alphabetically
    assert kpis["top_type"] == "NO_HELMET"
    # Zone-A < Zone-B alphabetically
    assert kpis["top_zone"] == "Zone-A"
    # "08" < "14" alphabetically / chronologically
    assert kpis["peak_hour"] == "08:00-09:00"


def test_extract_violations_list_input() -> None:
    """Test extract_violations with a plain list of violation dicts."""
    # Arrange
    raw = [
        {"zone": "Z1", "violation_type": "NO_HELMET"},
        {"zone": "Z2", "violation_type": "NO_VEST"},
        "not-a-dict",
    ]

    # Act
    result = extract_violations(raw)

    # Assert
    assert len(result) == 2
    assert result[0]["zone"] == "Z1"
    assert result[1]["zone"] == "Z2"


def test_extract_violations_dict_input() -> None:
    """Test extract_violations with a wrapped dict containing 'violations' key."""
    # Arrange
    raw = {
        "violations": [
            {"zone": "Workbench", "violation_type": "NO_HELMET"},
        ]
    }

    # Act
    result = extract_violations(raw)

    # Assert
    assert len(result) == 1
    assert result[0]["zone"] == "Workbench"


def test_extract_violations_bad_inputs() -> None:
    """Test extract_violations returns empty list for invalid or malformed data."""
    # Assert
    assert extract_violations(None) == []
    assert extract_violations("not json") == []
    assert extract_violations(123) == []
    assert extract_violations({}) == []
    assert extract_violations({"other_key": [1, 2, 3]}) == []
    assert extract_violations({"violations": "not-a-list"}) == []

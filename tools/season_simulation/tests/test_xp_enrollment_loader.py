"""Regression: Perfect XP loader must use Enrollment Record ID, not ARRAYJOIN."""

from __future__ import annotations

import unittest
from typing import Any
from unittest import mock

from season_simulation.business_reconciliation import (
    actual_xp_buckets_from_events,
    list_xp_events_for_enrollment,
    sum_active_xp_points,
    try_load_enrollment_xp_for_reconcile,
)
from season_simulation.downstream_settlement import (
    STREAK_XP_PREFIX,
    classify_streak_settlement,
)


class _FakeClient:
    def __init__(self, rows: list[dict[str, Any]], enrollment: dict[str, Any] | None = None):
        self.rows = rows
        self.enrollment = enrollment or {}
        self.calls: list[dict[str, Any]] = []

    def list_records(self, table: str, **kwargs: Any) -> list[dict[str, Any]]:
        self.calls.append({"table": table, **kwargs})
        formula = str(kwargs.get("formula") or "")
        if "ARRAYJOIN" in formula:
            return []
        if "Status" in (kwargs.get("fields") or []):
            raise RuntimeError('422 Unknown field name: "Status"')
        if "Enrollment Record ID" in formula:
            return list(self.rows)
        return list(self.rows)

    def get_record(self, table: str, record_id: str) -> dict[str, Any]:
        return {"id": record_id, "fields": dict(self.enrollment)}


def _xp(
    *,
    rid: str,
    source_key: str,
    pts: int,
    enrollment: str = "recrQNLC7wX3oqbmm",
) -> dict[str, Any]:
    return {
        "id": rid,
        "fields": {
            "Source Key": source_key,
            "XP Points": pts,
            "Active XP Points": pts,
            "Active?": True,
            "Enrollment": [enrollment],
            "Enrollment Record ID": [enrollment],
        },
    }


class ListXpEventsForEnrollmentTests(unittest.TestCase):
    def test_prefers_enrollment_record_id_formula(self):
        rows = [
            _xp(rid="rec1", source_key="SUBMISSION_XP|recS1", pts=20),
            _xp(rid="rec2", source_key="STREAK_XP|recrQNLC7wX3oqbmm|recX|2027-04-27", pts=10),
        ]
        client = _FakeClient(rows)
        out = list_xp_events_for_enrollment(client, "recrQNLC7wX3oqbmm")
        self.assertEqual(len(out), 2)
        self.assertTrue(
            any("Enrollment Record ID" in str(c.get("formula") or "") for c in client.calls)
        )
        self.assertFalse(
            any("ARRAYJOIN" in str(c.get("formula") or "") for c in client.calls)
        )

    def test_never_requests_status_field(self):
        client = _FakeClient([_xp(rid="rec1", source_key="HOMEWORK_XP|recH1", pts=35)])
        list_xp_events_for_enrollment(client, "recrQNLC7wX3oqbmm")
        for call in client.calls:
            fields = call.get("fields") or []
            self.assertNotIn("Status", fields)

    def test_falls_back_when_formula_returns_empty(self):
        rows = [_xp(rid="rec1", source_key="VIDEO_SUBMISSION|recV1", pts=25)]

        class EmptyThenAll(_FakeClient):
            def list_records(self, table: str, **kwargs: Any) -> list[dict[str, Any]]:
                self.calls.append({"table": table, **kwargs})
                if kwargs.get("formula"):
                    return []
                return list(self.rows)

        client = EmptyThenAll(rows)
        out = list_xp_events_for_enrollment(client, "recrQNLC7wX3oqbmm")
        self.assertEqual(len(out), 1)

    def test_try_load_uses_public_level_and_sums_active_xp(self):
        rows = [
            _xp(rid="recA", source_key="SUBMISSION_XP|a", pts=20),
            _xp(rid="recB", source_key="WEEKLY_THRESHOLD|e|w|100", pts=10),
        ]
        client = _FakeClient(
            rows,
            enrollment={
                "Lifetime XP Earned": 30,
                "Current Level": ["recLEVEL"],
                "Current Level - Public Facing Display": "G.O.A.T.",
            },
        )
        live = try_load_enrollment_xp_for_reconcile(client, "recrQNLC7wX3oqbmm")
        self.assertEqual(live["lifetime_xp"], 30)
        self.assertEqual(live["level"], "G.O.A.T.")
        self.assertEqual(sum_active_xp_points(live["events"]), 30)
        buckets = actual_xp_buckets_from_events(live["events"])
        self.assertEqual(buckets["Submission XP"], 20)
        self.assertEqual(buckets["Weekly Threshold XP"], 10)


class StreakSettlementPrefixTests(unittest.TestCase):
    def test_streak_prefix_is_streak_xp(self):
        self.assertEqual(STREAK_XP_PREFIX, "STREAK_XP|")

    def test_classify_streak_requires_occurrence_and_xp(self):
        checks = classify_streak_settlement(
            enrollment_fields={"Current Shooting Streak": 60, "Longest Shooting Streak": 60},
            expected_thresholds=[3, 5],
            occurrence_by_threshold={3: ["recOcc3"], 5: ["recOcc5"]},
            xp_by_threshold={3: ["recXp3"], 5: ["recXp5"]},
        )
        self.assertTrue(all(c.ok for c in checks))


if __name__ == "__main__":
    unittest.main()

"""Tests for shared active-XP Source Key integrity gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_PARENT))

from season_simulation.active_xp_source_key_integrity import (  # noqa: E402
    validate_active_xp_source_keys,
)
from season_simulation.business_reconciliation import (  # noqa: E402
    reconcile_business_success,
)
from season_simulation.expectations_matrix import AthleteExpectationMatrix  # noqa: E402
from season_simulation.reconciliation_checker import (  # noqa: E402
    build_enrollment_reconciliation,
)


def _ev(eid: str, source_key: Any, *, active: bool = True) -> dict:
    return {
        "id": eid,
        "fields": {
            "Source Key": source_key,
            "XP Points": 35,
            "Active?": active,
        },
    }


def _empty_matrix(**kwargs) -> AthleteExpectationMatrix:
    base = dict(
        profile="t",
        athlete_name="Test",
        season_goal=14400,
        total_planned_shots=0,
        submit_days=0,
        miss_days=0,
        weekly_rows=[],
        expected_perfect_week_count=0,
        expected_streak_achievements=[],
        expected_shot_milestones=[],
        expected_weekly_threshold_awards=[],
        expected_xp_by_category={
            "SUBMISSION_XP": 0,
            "HOMEWORK_XP": 0,
            "VIDEO_SUBMISSION": 0,
            "STREAK_XP": 0,
            "PERFECT_WEEK": 0,
            "SHOT_MILESTONE": 0,
            "ZOOM_ATTEND_BASE": 0,
            "ZOOM_RECORDING_CREDIT": 0,
        },
        expected_level_note="Beginner",
        expected_goal_met_date="",
        expected_goal_met_cumulative_shots=None,
        expected_email_handoffs={},
    )
    base.update(kwargs)
    return AthleteExpectationMatrix(**base)


class TestActiveXpSourceKeyIntegrity(unittest.TestCase):
    def test_active_blank_source_key_fails(self):
        result = validate_active_xp_source_keys([_ev("recBlank", "", active=True)])
        self.assertFalse(result.ok)
        self.assertTrue(any(i.code == "blank_or_whitespace_source_key" for i in result.issues))
        self.assertIn("recBlank", result.errors[0])

    def test_active_whitespace_source_key_fails(self):
        result = validate_active_xp_source_keys([_ev("recWs", "   \t  ", active=True)])
        self.assertFalse(result.ok)
        issue = next(i for i in result.issues if i.code == "blank_or_whitespace_source_key")
        self.assertEqual(issue.event_ids, ["recWs"])
        self.assertIn("whitespace", issue.evidence)

    def test_exact_duplicate_active_source_key_fails(self):
        events = [
            _ev("recA", "SUBMISSION_XP|recSub1", active=True),
            _ev("recB", "SUBMISSION_XP|recSub1", active=True),
        ]
        result = validate_active_xp_source_keys(events)
        self.assertFalse(result.ok)
        issue = next(i for i in result.issues if i.code == "duplicate_source_key")
        self.assertEqual(issue.source_key, "SUBMISSION_XP|recSub1")
        self.assertEqual(set(issue.event_ids), {"recA", "recB"})

    def test_legacy_plus_canonical_homework_fails(self):
        hc = "recHwComp1"
        events = [
            _ev("recCanon", f"HOMEWORK_XP|{hc}", active=True),
            _ev("recLegacy", f"HOMEWORK_COMPLETION|{hc}", active=True),
        ]
        result = validate_active_xp_source_keys(events)
        self.assertFalse(result.ok)
        issue = next(i for i in result.issues if i.code == "homework_legacy_plus_canonical")
        self.assertEqual(set(issue.event_ids), {"recCanon", "recLegacy"})
        self.assertIn(hc, issue.evidence)

    def test_inactive_blank_source_key_does_not_fail(self):
        result = validate_active_xp_source_keys(
            [
                _ev("recInactiveBlank", "", active=False),
                _ev("recInactiveWs", "  ", active=False),
                _ev("recOk", "HOMEWORK_XP|recHw1", active=True),
            ]
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.issues, [])

    def test_valid_canonical_only_homework_for_distinct_completions_passes(self):
        events = [
            _ev("rec1", "HOMEWORK_XP|recHcAAA", active=True),
            _ev("rec2", "HOMEWORK_XP|recHcBBB", active=True),
            # inactive legacy twin must not fail
            _ev("recLegacyOff", "HOMEWORK_COMPLETION|recHcAAA", active=False),
        ]
        result = validate_active_xp_source_keys(events)
        self.assertTrue(result.ok)

    def test_business_reconciliation_routes_through_shared_validator(self):
        matrix = _empty_matrix(
            expected_xp_by_category={
                "SUBMISSION_XP": 0,
                "HOMEWORK_XP": 0,
                "VIDEO_SUBMISSION": 0,
                "STREAK_XP": 0,
                "PERFECT_WEEK": 0,
                "SHOT_MILESTONE": 0,
                "ZOOM_ATTEND_BASE": 0,
                "ZOOM_RECORDING_CREDIT": 0,
            }
        )
        result = reconcile_business_success(
            profile="t",
            matrix=matrix,
            actual_events=[_ev("recBlankBiz", None, active=True)],
            actual_lifetime_xp=0,
            actual_level="Beginner",
        )
        self.assertFalse(result.pass_)
        self.assertTrue(
            any("blank_or_whitespace_source_key" in e for e in result.errors)
        )

    def test_reconciliation_checker_routes_through_shared_validator(self):
        matrix = _empty_matrix(
            expected_xp_by_category={
                "SUBMISSION_XP": 0,
                "HOMEWORK_XP": 1,
                "VIDEO_SUBMISSION": 0,
                "STREAK_XP": 0,
                "PERFECT_WEEK": 0,
                "SHOT_MILESTONE": 0,
                "ZOOM_ATTEND_BASE": 0,
                "ZOOM_RECORDING_CREDIT": 0,
            }
        )
        hc = "recSameHc"
        report = build_enrollment_reconciliation(
            enrollment_id="recEnr",
            profile="t",
            matrix=matrix,
            all_events=[
                _ev("recC", f"HOMEWORK_XP|{hc}", active=True),
                _ev("recL", f"HOMEWORK_COMPLETION|{hc}", active=True),
            ],
            lifetime_xp_earned=70,
        )
        self.assertFalse(report.pass_)
        hw_row = next(
            r
            for r in report.rows
            if r.check == "Homework XP canonical-only (no legacy dual-key)"
        )
        self.assertEqual(hw_row.pass_fail, "FAIL")


if __name__ == "__main__":
    unittest.main()

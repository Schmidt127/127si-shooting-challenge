"""Unit tests for read-only enrollment reconciliation checker."""

from __future__ import annotations

from tools.season_simulation.expectations_matrix import AthleteExpectationMatrix
from tools.season_simulation.reconciliation_checker import build_enrollment_reconciliation


def _matrix(**kwargs):
    base = dict(
        profile="athlete1-perfect",
        athlete_name="Test",
        season_goal=14400,
        total_planned_shots=100,
        submit_days=2,
        miss_days=0,
        weekly_rows=[],
        expected_perfect_week_count=0,
        expected_streak_achievements=[],
        expected_shot_milestones=[],
        expected_weekly_threshold_awards=[],
        expected_xp_by_category={
            "SUBMISSION_XP": 2,
            "HOMEWORK_XP": 1,
            "VIDEO_SUBMISSION": 1,
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


def test_reconciliation_table_pass_on_matching_active_events():
    events = [
        {"fields": {"Source Key": "SUBMISSION_XP|a", "XP Points": 20, "Active?": True}},
        {"fields": {"Source Key": "SUBMISSION_XP|b", "XP Points": 20, "Active?": True}},
        {"fields": {"Source Key": "HOMEWORK_XP|c", "XP Points": 35, "Active?": True}},
        {"fields": {"Source Key": "VIDEO_SUBMISSION|d", "XP Points": 25, "Active?": True}},
        {"fields": {"Source Key": "SUBMISSION_XP|dup", "XP Points": 20, "Active?": False}},
    ]
    # expected: 40 + 35 + 25 = 100
    report = build_enrollment_reconciliation(
        enrollment_id="recTest",
        profile="athlete1-perfect",
        matrix=_matrix(),
        all_events=events,
        lifetime_xp_earned=100,
        actual_level="Beginner",
        level_gate_ok=True,
    )
    assert report.pass_ is True
    md = report.to_markdown()
    assert "Pass/Fail" in md
    assert "Lifetime XP Earned" in md
    checks = {r.check for r in report.rows}
    assert "Submission XP" in checks
    assert "Duplicate Source Key prevention (active)" in checks


def test_inactive_events_excluded_from_active_sum():
    events = [
        {"fields": {"Source Key": "SUBMISSION_XP|a", "XP Points": 20, "Active?": True}},
        {"fields": {"Source Key": "SUBMISSION_XP|b", "XP Points": 20, "Active?": False}},
    ]
    report = build_enrollment_reconciliation(
        enrollment_id="recTest2",
        profile="t",
        matrix=_matrix(
            expected_xp_by_category={
                "SUBMISSION_XP": 1,
                "HOMEWORK_XP": 0,
                "VIDEO_SUBMISSION": 0,
                "STREAK_XP": 0,
                "PERFECT_WEEK": 0,
                "SHOT_MILESTONE": 0,
                "ZOOM_ATTEND_BASE": 0,
                "ZOOM_RECORDING_CREDIT": 0,
            }
        ),
        all_events=events,
        lifetime_xp_earned=20,
    )
    sub = next(r for r in report.rows if r.check == "Submission XP")
    assert sub.actual == 20
    assert sub.pass_fail == "PASS"

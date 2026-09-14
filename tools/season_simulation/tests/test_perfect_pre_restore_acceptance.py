"""Regression tests for Perfect pre-restore acceptance + restore/cleanup gates."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

TOOLS = Path(__file__).resolve().parents[2]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from season_simulation.business_reconciliation import STREAK  # noqa: E402
from season_simulation.cleanup import run_cleanup  # noqa: E402
from season_simulation.confirmation import (  # noqa: E402
    ConfirmationError,
    require_incomplete_cleanup_force,
)
from season_simulation.constants import (  # noqa: E402
    CONFIRM_CLEANUP_TOKEN,
    CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN,
    CONFIRM_TOKEN,
)
from season_simulation.perfect_pre_restore_acceptance import (  # noqa: E402
    EXPECTED_PERFECT_ACTIVE_XP,
    EXPECTED_STREAK_EVENTS,
    EXPECTED_STREAK_XP,
    EXPECTED_WEEKLY_THRESHOLD_EVENTS,
    EXPECTED_WEEKLY_THRESHOLD_XP,
    evaluate_pre_restore_acceptance,
    may_restore_production_formulas,
    restored_formulas_cannot_repair_failed_acceptance,
)
from season_simulation.reference_data import WeekInfo  # noqa: E402
from season_simulation.scenarios import _week_id_to_label  # noqa: E402
from season_simulation.run_registry import RunRegistry, save_registry  # noqa: E402


def _ev(eid: str, key: str, pts: int, *, active: bool = True) -> dict:
    return {
        "id": eid,
        "fields": {
            "Source Key": key,
            "XP Points": pts,
            "Active XP Points": pts if active else 0,
            "Active?": True if active else False,
        },
    }


def _perfect_events_minus_one_150() -> list[dict]:
    """Build a near-perfect set: 4950 active XP (missing one 150% WT = 30)."""
    events: list[dict] = []
    # Weekly threshold: 10×100 + 10×125 + 5×150 = 25 events / 450 XP (need 26/480)
    n = 0
    for _ in range(10):
        n += 1
        events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|recE|recW{n}|100", 10))
    for _ in range(10):
        n += 1
        events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|recE|recW{n}|125", 20))
    for _ in range(5):
        n += 1
        events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|recE|recW{n}|150", 30))
    # 9 active streaks / 455
    for i, thr in enumerate(STREAK.keys()):
        events.append(
            _ev(
                f"recST{i}",
                f"STREAK_XP|recE|recOcc{i}|2027-05-{i+1:02d}",
                STREAK[thr],
                active=True,
            )
        )
    # Pad remaining buckets to land at 4950 total active.
    # WT 450 + Streak 455 = 905; need 4045 more → use Submission 20-pt events.
    for i in range(202):  # 4040
        events.append(_ev(f"recSUB{i}", f"SUBMISSION_XP|recSub{i}", 20))
    events.append(_ev("recSUBPAD", "SUBMISSION_XP|recSubPad", 5))
    return events


class TestWeekInfoPerfectPath(unittest.TestCase):
    def test_weekinfo_usable_by_perfect_label_path(self):
        weeks = [
            WeekInfo(
                record_id="recWeek1",
                name="Week 1",
                start=None,
                end=None,
            )
        ]
        labels = _week_id_to_label(weeks)
        self.assertEqual(labels["recWeek1"], "Week 1")


class TestPreRestoreAcceptance(unittest.TestCase):
    def test_missing_150_blocks_acceptance_before_restore(self):
        events = _perfect_events_minus_one_150()
        result = evaluate_pre_restore_acceptance(events=events)
        self.assertFalse(result.ok)
        self.assertEqual(result.active_xp, 4950)
        self.assertNotEqual(result.active_xp, EXPECTED_PERFECT_ACTIVE_XP)
        self.assertEqual(result.weekly_threshold_events, 25)
        self.assertLess(result.weekly_threshold_events, EXPECTED_WEEKLY_THRESHOLD_EVENTS)
        self.assertEqual(result.streak_events, EXPECTED_STREAK_EVENTS)
        self.assertEqual(result.buckets.get("Streak XP"), EXPECTED_STREAK_XP)
        allowed, reason = may_restore_production_formulas(
            settlement_complete=True,
            business_pass=False,
            acceptance=result,
        )
        self.assertFalse(allowed)
        self.assertIn(reason, {"business_reconciliation_failed", "pre_restore_acceptance_failed"})

    def test_nine_streak_awards_must_be_active_at_gate(self):
        events = _perfect_events_minus_one_150()
        # Deactivate all streaks (simulates post-restore NOW() side effect wrongly
        # used as acceptance input — gate must require 9 active).
        for ev in events:
            key = str((ev.get("fields") or {}).get("Source Key") or "")
            if key.startswith("STREAK"):
                ev["fields"]["Active?"] = False
                ev["fields"]["Active XP Points"] = 0
        result = evaluate_pre_restore_acceptance(events=events)
        self.assertFalse(result.ok)
        self.assertEqual(result.streak_events, 0)
        self.assertTrue(any("streak active events=0" in e for e in result.errors))

    def test_target_is_4980_active_xp_not_raw_total(self):
        self.assertEqual(EXPECTED_PERFECT_ACTIVE_XP, 4980)
        # Inactive events must not inflate acceptance.
        events = [
            _ev("recA", "SUBMISSION_XP|1", 4980, active=False),
            _ev("recB", "SUBMISSION_XP|2", 100, active=True),
        ]
        result = evaluate_pre_restore_acceptance(events=events)
        self.assertEqual(result.active_xp, 100)
        self.assertFalse(result.ok)

    def test_formula_restore_blocked_when_reconciliation_failing(self):
        acceptance = evaluate_pre_restore_acceptance(events=[])
        allowed, reason = may_restore_production_formulas(
            settlement_complete=True,
            business_pass=False,
            acceptance=acceptance,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "business_reconciliation_failed")

    def test_restored_formulas_cannot_falsely_repair_failed_sim(self):
        # Pre-restore failed at 4950; post-restore live active fell to 4495.
        self.assertTrue(
            restored_formulas_cannot_repair_failed_acceptance(
                pre_restore_active_xp=4950,
                post_restore_active_xp=4495,
            )
        )
        self.assertFalse(
            restored_formulas_cannot_repair_failed_acceptance(
                pre_restore_active_xp=4980,
                post_restore_active_xp=4495,
            )
        )

    def test_passing_gate_allows_restore(self):
        # Minimal synthetic pass: exact targets only (other buckets 0 OK for this unit).
        events: list[dict] = []
        n = 0
        for _ in range(10):
            n += 1
            events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|e|w{n}|100", 10))
        for _ in range(10):
            n += 1
            events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|e|w{n}|125", 20))
        for _ in range(6):
            n += 1
            events.append(_ev(f"recWT{n}", f"WEEKLY_THRESHOLD|e|w{n}|150", 30))
        for i, thr in enumerate(STREAK.keys()):
            events.append(
                _ev(f"recST{i}", f"STREAK_XP|e|o{i}|2027-05-{i+1:02d}", STREAK[thr])
            )
        # Pad to 4980: WT 480 + Streak 455 = 935; need 4045
        for i in range(202):
            events.append(_ev(f"recS{i}", f"SUBMISSION_XP|{i}", 20))
        events.append(_ev("recSp", "SUBMISSION_XP|pad", 5))
        result = evaluate_pre_restore_acceptance(events=events)
        self.assertEqual(result.active_xp, EXPECTED_PERFECT_ACTIVE_XP)
        self.assertEqual(result.weekly_threshold_events, EXPECTED_WEEKLY_THRESHOLD_EVENTS)
        self.assertEqual(result.buckets.get("Weekly Threshold XP"), EXPECTED_WEEKLY_THRESHOLD_XP)
        self.assertTrue(result.ok, result.errors)
        allowed, reason = may_restore_production_formulas(
            settlement_complete=True,
            business_pass=True,
            acceptance=result,
        )
        self.assertTrue(allowed)
        self.assertEqual(reason, "accepted")


class TestCleanupNotAutomatic(unittest.TestCase):
    def test_incomplete_cleanup_requires_force_token(self):
        with self.assertRaises(ConfirmationError):
            require_incomplete_cleanup_force(
                registry_status="paused",
                confirm_force_incomplete=None,
            )
        require_incomplete_cleanup_force(
            registry_status="paused",
            confirm_force_incomplete=CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN,
        )
        # Complete registries do not need the force token.
        require_incomplete_cleanup_force(
            registry_status="complete",
            confirm_force_incomplete=None,
        )

    def test_run_cleanup_refuses_paused_without_force(self):
        tmp = Path(tempfile.mkdtemp())
        run_id = "SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt"
        reg = RunRegistry(
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            status="paused",
            enrollment_id="recEnrollTest",
            athlete_id="recAthleteTest",
        )
        reg.add("Enrollments", "recEnrollTest")
        save_registry(reg, tmp)
        result = run_cleanup(
            run_id=run_id,
            registry_dir=tmp,
            execute=True,
            confirm=CONFIRM_TOKEN,
            confirm_cleanup=CONFIRM_CLEANUP_TOKEN,
            confirm_force_incomplete_cleanup=None,
            client=MagicMock(),
            out_dir=tmp,
        )
        self.assertTrue(result.dry_run)
        self.assertTrue(any("FORCE-CLEANUP-INCOMPLETE" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()

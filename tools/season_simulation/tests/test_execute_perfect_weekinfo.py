"""Regression: execute-perfect must accept live WeekInfo reference objects.

Failed launch 2026-09-14T161612Z:
  AttributeError: 'WeekInfo' object has no attribute 'get'
  at scenarios._week_id_to_label (scenarios.py) via execute_perfect scenario build.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

TOOLS = Path(__file__).resolve().parents[2]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from season_simulation.execute_perfect import (  # noqa: E402
    build_mike_schmidt_perfect_scenario,
    run_execute_perfect,
)
from season_simulation.reference_data import (  # noqa: E402
    GradeBandInfo,
    HomeworkAssignmentInfo,
    TargetGoalInfo,
    WeekInfo,
    ZoomMeetingInfo,
)
from season_simulation.scenarios import (  # noqa: E402
    _week_id_to_label,
    group_phas_by_homework_week,
)


def _week_infos() -> list[WeekInfo]:
    labels = ("Early Bird",) + tuple(f"Week {i}" for i in range(1, 10))
    out: list[WeekInfo] = []
    cursor = date(2027, 4, 25)
    for i, label in enumerate(labels):
        start = cursor
        end = date.fromordinal(start.toordinal() + 6)
        out.append(
            WeekInfo(
                record_id=f"recWEEK{i:02d}",
                name=label,
                start=start,
                end=end,
                program_instance_id="recPI",
            )
        )
        cursor = date.fromordinal(end.toordinal() + 1)
    return out


def _homework_for_weeks(weeks: list[WeekInfo]) -> list[dict]:
    hw: list[dict] = []
    for i, w in enumerate(weeks):
        for slot_i, slot in enumerate(("HW1", "HW2")):
            n = i * 2 + slot_i + 1
            hw.append(
                {
                    "record_id": f"recHW{n:02d}",
                    "slot": slot,
                    "library_id": f"recLIB{n:02d}",
                    "display": f"PHA | {w.name} | {slot}",
                    "week_id": w.record_id,
                }
            )
    return hw


class WeekInfoLabelTests(unittest.TestCase):
    def test_week_id_to_label_accepts_weekinfo_objects(self):
        weeks = _week_infos()
        labels = _week_id_to_label(weeks)
        self.assertEqual(labels["recWEEK00"], "Early Bird")
        self.assertEqual(labels["recWEEK01"], "Week 1")
        self.assertEqual(labels["recWEEK09"], "Week 9")

    def test_week_id_to_label_still_accepts_dicts(self):
        labels = _week_id_to_label(
            [
                {"record_id": "recA", "name": "Week 1"},
                {"record_id": "recB", "display": "Early Bird"},
            ]
        )
        self.assertEqual(labels["recA"], "Week 1")
        self.assertEqual(labels["recB"], "Early Bird")

    def test_group_phas_with_weekinfo_does_not_raise(self):
        weeks = _week_infos()
        hw = _homework_for_weeks(weeks)
        by_label = group_phas_by_homework_week(hw, weeks)
        self.assertEqual(len(by_label["Early Bird"]), 2)
        self.assertEqual(len(by_label["Week 9"]), 2)


class ExecutePerfectWeekInfoRegression(unittest.TestCase):
    def test_build_scenario_with_weekinfo_objects_does_not_raise(self):
        """Direct reproduction of the failed-launch call shape."""
        weeks = _week_infos()
        scenario = build_mike_schmidt_perfect_scenario(
            run_id="SEASON-SIM-PERFECT-20260914T161612Z-mike-schmidt",
            grade_band_id="recGB",
            goal_record_id="recGOAL",
            goal_total_shots=12000,
            homework=_homework_for_weeks(weeks),
            zoom_meetings=[
                {"record_id": "recZ1", "display": "Live"},
                {"record_id": "recZ2", "display": "Rec"},
            ],
            weeks=weeks,  # WeekInfo objects — previously crashed in _week_id_to_label
        )
        self.assertEqual(scenario.athlete.get("display_name"), "Mike Schmidt")
        self.assertEqual(
            scenario.athlete.get("parent_email"),
            "schmidt@fairfieldbasketballclub.com",
        )

    def test_execute_perfect_converts_reference_dataclasses_before_scenario(self):
        weeks = _week_infos()
        snap = MagicMock()
        snap.errors = []
        snap.grade_band = GradeBandInfo(
            record_id="recGB",
            name="9-12",
            min_grade=9,
            max_grade=12,
            active=True,
        )
        snap.highest_goal = TargetGoalInfo(
            record_id="recGOAL",
            label="12000",
            total_shot_target=12000,
            grade_band_id="recGB",
            active=True,
            program_instance_ids=["recPI"],
        )
        snap.homework = [
            HomeworkAssignmentInfo(
                record_id=h["record_id"],
                display=h["display"],
                week_id=h["week_id"],
                grade_band_id="recGB",
                slot=h["slot"],
                library_id=h["library_id"],
                active=True,
                program_instance_id="recPI",
            )
            for h in _homework_for_weeks(weeks)
        ]
        snap.zoom_meetings = [
            ZoomMeetingInfo(
                record_id="recZ1",
                display="Live",
                meeting_name="Live",
                start_time="",
                week_id=weeks[0].record_id,
                status="Scheduled",
            ),
            ZoomMeetingInfo(
                record_id="recZ2",
                display="Rec",
                meeting_name="Rec",
                start_time="",
                week_id=weeks[-1].record_id,
                status="Scheduled",
            ),
        ]
        snap.weeks_covering_window = weeks

        real_build = build_mike_schmidt_perfect_scenario

        def _spy_build(**kwargs):
            for w in kwargs.get("weeks") or []:
                self.assertIsInstance(w, dict)
                self.assertIn("record_id", w)
            for h in kwargs.get("homework") or []:
                self.assertIsInstance(h, dict)
            for z in kwargs.get("zoom_meetings") or []:
                self.assertIsInstance(z, dict)
            return real_build(**kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch(
                "season_simulation.execute_perfect.load_reference_snapshot",
                return_value=snap,
            ), patch(
                "season_simulation.execute_perfect.build_mike_schmidt_perfect_scenario",
                side_effect=_spy_build,
            ) as build_spy, patch(
                "season_simulation.execute_perfect._run_profile_writer",
                return_value={
                    "mode": "dry-plan",
                    "created_records": [],
                    "intended_write_count": 0,
                },
            ), patch(
                "season_simulation.execute_perfect.stage_h_post_cascade_hooks",
                return_value={
                    "stage": "H_post_cascade_hooks",
                    "status": "ok",
                    "errors": [],
                },
            ), patch(
                "season_simulation.execute_perfect.stage_d_settlement_hook",
                return_value={"complete": False, "status": "planned"},
            ), patch(
                "season_simulation.execute_perfect.stage_e_reconcile_hook",
                return_value={"complete": False, "status": "planned"},
            ), patch(
                "season_simulation.execute_perfect.stage_e2_business_success_hook",
                return_value={"pass": False, "status": "planned"},
            ), patch(
                "season_simulation.execute_perfect.stage_f_formula_verify_hook",
                return_value={"status": "planned"},
            ), patch(
                "season_simulation.execute_perfect.build_athlete_expectation_matrix",
                return_value=MagicMock(
                    expected_perfect_week_count=0,
                    expected_weekly_threshold_awards=[],
                    expected_streak_achievements=[],
                ),
            ):
                result = run_execute_perfect(
                    run_id="SEASON-SIM-PERFECT-20260914T161612Z-mike-schmidt",
                    execute=False,
                    registry_dir=root / "reg",
                    out_dir=root / "out",
                    client=MagicMock(),
                    allow_writes=False,
                )
        self.assertEqual(result.get("errors"), [])
        self.assertEqual(result["athlete"]["display_name"], "Mike Schmidt")
        build_spy.assert_called_once()
        call_kwargs = build_spy.call_args.kwargs
        self.assertTrue(all(isinstance(w, dict) for w in call_kwargs["weeks"]))
        self.assertEqual(call_kwargs["weeks"][0]["name"], "Early Bird")
        self.assertEqual(call_kwargs["weeks"][0]["record_id"], "recWEEK00")


if __name__ == "__main__":
    unittest.main()

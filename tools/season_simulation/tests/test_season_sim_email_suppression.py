#!/usr/bin/env python3
"""Offline contract tests for season-sim email suppression."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PACKAGE_PARENT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE_PARENT))

from season_simulation.season_sim_email_suppression import (  # noqa: E402
    is_season_sim_coach_feedback_marker,
    is_season_sim_enrollment_welcome_candidate,
    is_season_sim_notes_marker,
    is_season_sim_submission,
    should_suppress_season_sim_email_for_homework,
    should_suppress_season_sim_email_for_submission,
    should_suppress_season_sim_email_for_video_feedback,
)


class TestSeasonSimEmailSuppression(unittest.TestCase):
    def test_submission_dual_gate_requires_both(self):
        self.assertFalse(
            is_season_sim_submission(
                season_sim_test_record=True,
                video_upload_note="plain note",
            )
        )
        self.assertFalse(
            is_season_sim_submission(
                season_sim_test_record=False,
                video_upload_note="SEASON-SIM|run|A1",
            )
        )
        self.assertTrue(
            is_season_sim_submission(
                season_sim_test_record=True,
                video_upload_note="SEASON-SIM|SEASON-SIM-2027-20260913T010724Z-threeathlete",
            )
        )

    def test_homework_and_vf_markers(self):
        self.assertTrue(is_season_sim_notes_marker("SEASON-SIM|run|notes"))
        self.assertTrue(is_season_sim_coach_feedback_marker("SEASON-SIM|run|vf"))
        self.assertFalse(is_season_sim_notes_marker("production homework"))

    def test_enrollment_welcome_names_only_sim_scenarios(self):
        self.assertTrue(
            is_season_sim_enrollment_welcome_candidate(athlete_display_name="Sim Recovery")
        )
        self.assertTrue(
            is_season_sim_enrollment_welcome_candidate(
                athlete_display_name="",
                athlete_first_name="Sim",
                athlete_last_name="Edge",
            )
        )
        self.assertFalse(
            is_season_sim_enrollment_welcome_candidate(athlete_display_name="Real Athlete")
        )

    def test_field_dict_helpers(self):
        self.assertTrue(
            should_suppress_season_sim_email_for_submission(
                {
                    "Season Sim Test Record?": True,
                    "Video Upload Note": "SEASON-SIM|x",
                }
            )
        )
        self.assertFalse(
            should_suppress_season_sim_email_for_submission(
                {
                    "Season Sim Test Record?": True,
                    "Video Upload Note": "production",
                }
            )
        )
        self.assertTrue(
            should_suppress_season_sim_email_for_homework({"Notes": "SEASON-SIM|x"})
        )
        self.assertTrue(
            should_suppress_season_sim_email_for_video_feedback(
                {"Coach Feedback": "SEASON-SIM|x"}
            )
        )


if __name__ == "__main__":
    unittest.main()

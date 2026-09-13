"""SC-SEASON-SIM-001 — dual-gated email suppression for disposable simulation rows.

Airtable automation scripts cannot import this module; helpers are inlined in
071/073/074/076/078A/117/079. This module is the offline contract + unit-test
source of truth (mirrors season_sim_date_gate.py pattern).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .constants import RUN_MARKER_PREFIX

SEASON_SIM_MARKER = f"{RUN_MARKER_PREFIX}|"
SEASON_SIM_TEST_RECORD_FIELD = "Season Sim Test Record?"
VIDEO_UPLOAD_NOTE_FIELD = "Video Upload Note"

# Disposable Athlete 1–3 scenario display names (enrollment welcome guard only).
SIM_SCENARIO_ATHLETE_NAMES = frozenset(
    {
        "Sim Perfect",
        "Sim Recovery",
        "Sim Edge",
    }
)


def is_season_sim_submission(*, season_sim_test_record: bool, video_upload_note: str | None) -> bool:
    """Dual gate: test-record checkbox AND SEASON-SIM| marker in Video Upload Note."""
    if not season_sim_test_record:
        return False
    return SEASON_SIM_MARKER in str(video_upload_note or "")


def is_season_sim_notes_marker(notes: str | None) -> bool:
    return SEASON_SIM_MARKER in str(notes or "")


def is_season_sim_coach_feedback_marker(coach_feedback: str | None) -> bool:
    return SEASON_SIM_MARKER in str(coach_feedback or "")


def is_season_sim_enrollment_welcome_candidate(
    *,
    athlete_display_name: str | None,
    athlete_first_name: str | None = None,
    athlete_last_name: str | None = None,
) -> bool:
    """Narrow enrollment-only guard when submission marker fields are unavailable."""
    name = str(athlete_display_name or "").strip()
    if name in SIM_SCENARIO_ATHLETE_NAMES:
        return True
    first = str(athlete_first_name or "").strip()
    last = str(athlete_last_name or "").strip()
    if first == "Sim" and last in {"Perfect", "Recovery", "Edge"}:
        return True
    return False


def should_suppress_season_sim_email_for_submission(fields: dict[str, Any]) -> bool:
    return is_season_sim_submission(
        season_sim_test_record=bool(fields.get(SEASON_SIM_TEST_RECORD_FIELD)),
        video_upload_note=str(fields.get(VIDEO_UPLOAD_NOTE_FIELD) or ""),
    )


def should_suppress_season_sim_email_for_homework(fields: dict[str, Any]) -> bool:
    return is_season_sim_notes_marker(str(fields.get("Notes") or ""))


def should_suppress_season_sim_email_for_video_feedback(fields: dict[str, Any]) -> bool:
    return is_season_sim_coach_feedback_marker(str(fields.get("Coach Feedback") or ""))


@dataclass(frozen=True)
class HandoffBaseline:
    run_id: str
    total_queue_rows: int
    run_attributable_rows: int
    captured_at: str
    row_ids: frozenset[str]

    def delta(self, *, current_ids: set[str]) -> set[str]:
        return current_ids - set(self.row_ids)


def handoff_row_is_run_attributable(fields: dict[str, Any], run_id: str) -> bool:
    blob = str(fields)
    marker = f"SEASON-SIM|{run_id}"
    if marker in blob:
        return True
    if run_id in blob:
        return True
    # Profile-scoped markers under shared three-athlete run_id.
    for slug in ("A1-PERFECT", "A2-RECOVERY", "A3-EDGE"):
        if f"{marker}|{slug}" in blob:
            return True
    return False

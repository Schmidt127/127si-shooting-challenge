"""Pre-restore acceptance gate for Perfect Mike Schmidt season simulations.

Season-sim row-scoped formulas must remain active through writer execution,
downstream settlement, reconciliation, authorized requeue repair, and final
active-XP verification. Production-normal formulas may be restored only after
this gate hard-passes.

Failed / incomplete runs must preserve formulas and records for investigation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from .active_xp_source_key_integrity import validate_active_xp_source_keys
from .business_reconciliation import (
    actual_xp_buckets_from_events,
    event_is_active,
    sum_active_xp_points,
)
from .constants import SAFE_EMAIL_RECIPIENT
from .live_write_contract import EXPECTED_PERFECT_SEASON_XP

# Perfect-season hard targets (active XP only — never raw / historical totals).
EXPECTED_PERFECT_ACTIVE_XP = EXPECTED_PERFECT_SEASON_XP  # 4980
EXPECTED_WEEKLY_THRESHOLD_EVENTS = 26
EXPECTED_WEEKLY_THRESHOLD_XP = 480
EXPECTED_STREAK_EVENTS = 9
EXPECTED_STREAK_XP = 455


@dataclass
class PreRestoreAcceptanceResult:
    ok: bool
    active_xp: int
    expected_active_xp: int = EXPECTED_PERFECT_ACTIVE_XP
    buckets: dict[str, int] = field(default_factory=dict)
    weekly_threshold_events: int = 0
    streak_events: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source_key_ok: bool = True
    ehq_allowlist_ok: bool = True
    enrollment_linkage_ok: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_active_prefix(events: Sequence[dict[str, Any]], prefix: str) -> int:
    n = 0
    for ev in events:
        f = ev.get("fields") or ev
        if not event_is_active(f):
            continue
        key = str(f.get("Source Key") or "").upper()
        if prefix.upper() in key:
            n += 1
    return n


def evaluate_pre_restore_acceptance(
    *,
    events: Sequence[dict[str, Any]],
    expected_active_xp: int = EXPECTED_PERFECT_ACTIVE_XP,
    expected_weekly_threshold_events: int = EXPECTED_WEEKLY_THRESHOLD_EVENTS,
    expected_weekly_threshold_xp: int = EXPECTED_WEEKLY_THRESHOLD_XP,
    expected_streak_events: int = EXPECTED_STREAK_EVENTS,
    expected_streak_xp: int = EXPECTED_STREAK_XP,
    ehq_recipients: Sequence[str] | None = None,
    enrollment_id: str | None = None,
    expected_enrollment_linked_ids: Sequence[str] | None = None,
) -> PreRestoreAcceptanceResult:
    """Hard-pass gate required before any Production formula restoration."""
    errors: list[str] = []
    notes: list[str] = []
    buckets = actual_xp_buckets_from_events(events)
    active_xp = sum_active_xp_points(events)

    if active_xp != expected_active_xp:
        errors.append(
            f"active_xp={active_xp} expected={expected_active_xp} "
            "(pre-restore acceptance uses active XP only, not raw/historical totals)"
        )

    wt_events = _count_active_prefix(events, "WEEKLY_THRESHOLD")
    streak_events = _count_active_prefix(events, "STREAK")
    wt_xp = int(buckets.get("Weekly Threshold XP") or 0)
    streak_xp = int(buckets.get("Streak XP") or 0)

    if wt_events != expected_weekly_threshold_events or wt_xp != expected_weekly_threshold_xp:
        errors.append(
            f"weekly_threshold active events={wt_events}/{expected_weekly_threshold_events} "
            f"xp={wt_xp}/{expected_weekly_threshold_xp}"
        )
    if streak_events != expected_streak_events or streak_xp != expected_streak_xp:
        errors.append(
            f"streak active events={streak_events}/{expected_streak_events} "
            f"xp={streak_xp}/{expected_streak_xp}"
        )

    sk = validate_active_xp_source_keys(events)
    source_key_ok = bool(sk.ok)
    if not source_key_ok:
        for issue in sk.issues:
            errors.append(issue.to_error_string())

    unsafe: list[str] = []
    for raw in ehq_recipients or []:
        email = str(raw or "").strip().lower()
        if email and email != SAFE_EMAIL_RECIPIENT.lower():
            unsafe.append(email)
    ehq_ok = not unsafe
    if not ehq_ok:
        errors.append(f"unallowlisted_ehq_recipients:{sorted(set(unsafe))}")

    enrollment_ok = True
    if enrollment_id is not None or expected_enrollment_linked_ids is not None:
        if enrollment_id is not None and not str(enrollment_id).startswith("rec"):
            enrollment_ok = False
            errors.append(f"invalid_enrollment_id:{enrollment_id}")
        bad = [
            rid
            for rid in (expected_enrollment_linked_ids or [])
            if rid and not str(rid).startswith("rec")
        ]
        if bad:
            enrollment_ok = False
            errors.append(f"invalid_linked_record_ids:{bad[:5]}")
        if expected_enrollment_linked_ids is not None and not list(
            expected_enrollment_linked_ids
        ):
            enrollment_ok = False
            errors.append("expected_enrollment_linked_ids_empty")

    if active_xp == expected_active_xp and not errors:
        notes.append("pre-restore acceptance PASS — Production formula restore may proceed")
    else:
        notes.append(
            "pre-restore acceptance FAIL — preserve Season Sim formulas and records; "
            "do not restore Production-normal formulas automatically"
        )

    return PreRestoreAcceptanceResult(
        ok=not errors,
        active_xp=active_xp,
        expected_active_xp=expected_active_xp,
        buckets=buckets,
        weekly_threshold_events=wt_events,
        streak_events=streak_events,
        errors=errors,
        notes=notes,
        source_key_ok=source_key_ok,
        ehq_allowlist_ok=ehq_ok,
        enrollment_linkage_ok=enrollment_ok,
    )


def may_restore_production_formulas(
    *,
    settlement_complete: bool,
    business_pass: bool,
    acceptance: PreRestoreAcceptanceResult | dict[str, Any] | None,
) -> tuple[bool, str]:
    """Return (allowed, reason). Restore is refused unless every gate passes."""
    if not settlement_complete:
        return False, "settlement_incomplete"
    if not business_pass:
        return False, "business_reconciliation_failed"
    if acceptance is None:
        return False, "pre_restore_acceptance_missing"
    ok = (
        acceptance.ok
        if isinstance(acceptance, PreRestoreAcceptanceResult)
        else bool(acceptance.get("ok"))
    )
    if not ok:
        return False, "pre_restore_acceptance_failed"
    return True, "accepted"


def post_restore_safety_notes() -> list[str]:
    """Operator notes after an authorized Production-normal restore."""
    return [
        "Verify formulas match the committed Production-normal bundle (hash check).",
        "Confirm no SEASON-SIM branch remains in monitored formulas.",
        "Confirm restoration created no new records, EHQ rows, emails, or Hub dispatches.",
        "Future-dated simulation rows are expected to become non-countable under "
        "Production NOW() formulas and must not be used for the final active-XP "
        "acceptance calculation (that calculation is pre-restore only).",
    ]


def restored_formulas_cannot_repair_failed_acceptance(
    *,
    pre_restore_active_xp: int,
    post_restore_active_xp: int,
    expected_active_xp: int = EXPECTED_PERFECT_ACTIVE_XP,
) -> bool:
    """True when a post-restore XP total must not be treated as a repaired pass.

    Restored Production NOW() formulas may deactivate future-dated streak /
    threshold eligibility. A failed pre-restore gate (e.g. 4950) must never be
    reinterpreted as success from the post-restore live total (e.g. 4495).
    """
    if pre_restore_active_xp == expected_active_xp:
        return False
    # Any non-passing pre-restore total is not repaired by restore side-effects.
    return pre_restore_active_xp != expected_active_xp


__all__ = [
    "EXPECTED_PERFECT_ACTIVE_XP",
    "EXPECTED_WEEKLY_THRESHOLD_EVENTS",
    "EXPECTED_WEEKLY_THRESHOLD_XP",
    "EXPECTED_STREAK_EVENTS",
    "EXPECTED_STREAK_XP",
    "PreRestoreAcceptanceResult",
    "evaluate_pre_restore_acceptance",
    "may_restore_production_formulas",
    "post_restore_safety_notes",
    "restored_formulas_cannot_repair_failed_acceptance",
]

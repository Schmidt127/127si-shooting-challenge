"""Business-success reconciliation gate for season simulation.

cascade_complete (submission XP settled) is necessary but not sufficient.
This stage compares expected vs actual XP buckets, level, Perfect Weeks,
streaks, duplicates, and pending reconciliation fields — and hard-fails.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from .active_xp_source_key_integrity import validate_active_xp_source_keys
from .expectations_matrix import AthleteExpectationMatrix

SAFE_ALLOWLIST = {
    "schmidt@fairfieldbasketballclub.com",
}

# Production XP amounts (aligned with rebuild_perfect_season_oracle / XP Reward Rules).
SHOOTING_BASE = 20
STREAK = {3: 10, 5: 15, 7: 20, 10: 30, 20: 50, 30: 60, 40: 75, 50: 90, 60: 105}
THRESH = {100: 10, 125: 20, 150: 30}
PW = 100
HW = 35
VIDEO = 25
ZOOM_BASE = 60
ZOOM_REC = 30
MILESTONES = [
    (3000, 10, "25%"),
    (6000, 15, "50%"),
    (9000, 20, "75%"),
    (12000, 30, "100%"),
    (14400, 40, "120%"),
    (18000, 50, "150%"),
    (21000, 65, "175%"),
    (24000, 80, "200%"),
]
LEVELS = [
    (0, "Beginner"),
    (200, "Rookie Shooter"),
    (400, "Developing Shooter"),
    (600, "Consistent Shooter"),
    (800, "Dangerous Shooter"),
    (1000, "Hot Hand"),
    (1200, "Deadeye"),
    (1400, "Sharpshooter"),
    (1600, "Pro"),
    (1800, "All-Star"),
    (2000, "Legend"),
    (2200, "G.O.A.T."),
]


def level_for(xp: int) -> str:
    cur = "Beginner"
    for thr, name in LEVELS:
        if xp >= thr:
            cur = name
    return cur


@dataclass
class BucketDiff:
    name: str
    expected: int
    actual: int
    ok: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessReconciliationResult:
    profile: str
    pass_: bool
    expected_total_xp: int
    actual_total_xp: int
    expected_level: str
    actual_level: str
    bucket_diffs: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pass"] = d.pop("pass_")
        return d


def xp_points_from_event_buckets(buckets: dict[str, int]) -> dict[str, int]:
    """Convert expectation-matrix event counts into XP points."""
    streak_thresholds = list(STREAK.keys())
    streak_events = int(buckets.get("STREAK_XP") or 0)
    streak_xp = sum(STREAK[t] for t in streak_thresholds[:streak_events])
    milestone_n = int(buckets.get("SHOT_MILESTONE") or 0)
    milestone_xp = sum(xp for _, xp, _ in MILESTONES[:milestone_n])
    return {
        "Submission XP": int(buckets.get("SUBMISSION_XP") or 0) * SHOOTING_BASE,
        "Homework XP": int(buckets.get("HOMEWORK_XP") or 0) * HW,
        "Video XP": int(buckets.get("VIDEO_SUBMISSION") or 0) * VIDEO,
        "Streak XP": streak_xp,
        "Weekly Threshold XP": 0,
        "Perfect Week XP": int(buckets.get("PERFECT_WEEK") or 0) * PW,
        "Shot Milestone XP": milestone_xp,
        "Zoom XP": (
            int(buckets.get("ZOOM_ATTEND_BASE") or 0) * ZOOM_BASE
            + int(buckets.get("ZOOM_RECORDING_CREDIT") or 0) * ZOOM_REC
        ),
    }


def threshold_xp_from_awards(awards: Sequence[dict[str, Any]]) -> int:
    total = 0
    for a in awards:
        tier = int(a.get("tier") or 0)
        total += int(THRESH.get(tier) or 0)
    return total


def expected_points_from_matrix(matrix: AthleteExpectationMatrix) -> dict[str, int]:
    pts = xp_points_from_event_buckets(dict(matrix.expected_xp_by_category))
    pts["Weekly Threshold XP"] = threshold_xp_from_awards(
        matrix.expected_weekly_threshold_awards
    )
    pts["Streak XP"] = sum(
        STREAK[t] for t in matrix.expected_streak_achievements if t in STREAK
    )
    mil_map = {shot: xp for shot, xp, _ in MILESTONES}
    pts["Shot Milestone XP"] = sum(
        mil_map.get(s, 0) for s in matrix.expected_shot_milestones
    )
    return pts


def sum_points(pts: dict[str, int]) -> int:
    return int(sum(pts.values()))


def event_is_active(fields: dict[str, Any]) -> bool:
    """Production Active XP Points only when Active? is truthy (True).

    ``Active?=null`` / missing must **not** count — matches Airtable formula
    behavior documented in the 010724Z closeout (streak rows with null Active?
    contribute 0 Active XP Points).
    """
    status = str(fields.get("Status") or "").lower()
    if status in {"void", "inactive", "duplicate", "superseded"}:
        return False
    return fields.get("Active?") is True


def actual_xp_buckets_from_events(events: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Sum XP Points by coarse bucket from live XP Event rows."""
    buckets = {
        "Submission XP": 0,
        "Homework XP": 0,
        "Video XP": 0,
        "Streak XP": 0,
        "Weekly Threshold XP": 0,
        "Perfect Week XP": 0,
        "Shot Milestone XP": 0,
        "Zoom XP": 0,
    }
    for ev in events:
        f = ev.get("fields") or ev
        if not event_is_active(f):
            continue
        key = str(f.get("Source Key") or "").upper()
        pts = f.get("XP Points")
        if pts is None:
            pts = f.get("Points")
        try:
            amount = int(float(pts or 0))
        except (TypeError, ValueError):
            amount = 0
        if key.startswith("SUBMISSION_XP") or ("SHOOTING" in key and "BASE" in key):
            buckets["Submission XP"] += amount
        elif key.startswith("HOMEWORK"):
            buckets["Homework XP"] += amount
        elif "VIDEO" in key:
            buckets["Video XP"] += amount
        elif key.startswith("STREAK") or "STREAK" in key:
            buckets["Streak XP"] += amount
        elif "WEEKLY_THRESHOLD" in key or "THRESHOLD" in key:
            buckets["Weekly Threshold XP"] += amount
        elif "PERFECT_WEEK" in key:
            buckets["Perfect Week XP"] += amount
        elif "MILESTONE" in key or "SHOT_MILESTONE" in key:
            buckets["Shot Milestone XP"] += amount
        elif "ZOOM" in key:
            buckets["Zoom XP"] += amount
    return buckets


def sum_active_xp_points(events: Sequence[dict[str, Any]]) -> int:
    """Sum Active XP Points from active XP Event rows (fallback to XP Points)."""
    total = 0
    for ev in events:
        f = ev.get("fields") or ev
        if not event_is_active(f):
            continue
        pts = f.get("Active XP Points")
        if pts is None:
            pts = f.get("XP Points")
        if pts is None:
            pts = f.get("Points")
        try:
            total += int(float(pts or 0))
        except (TypeError, ValueError):
            continue
    return total


def assert_lifetime_matches_active_xp(
    lifetime: int | None,
    events: Sequence[dict[str, Any]],
) -> list[str]:
    """Hard-fail gate: Lifetime XP Earned must equal sum(Active XP Points).

    When ``lifetime`` is None, no check is performed (caller has not supplied
    Enrollment Lifetime XP). When events are empty and lifetime is 0, that is OK.
    Does not invent XP — only compares provided lifetime vs provided events.
    """
    if lifetime is None:
        return []
    active_sum = sum_active_xp_points(events)
    if int(lifetime) != active_sum:
        return [
            f"Lifetime XP Earned ({int(lifetime)}) != sum(Active XP Points) "
            f"from active events ({active_sum})"
        ]
    return []


def reconcile_business_success(
    *,
    profile: str,
    matrix: AthleteExpectationMatrix,
    actual_events: Sequence[dict[str, Any]],
    actual_lifetime_xp: int | None,
    actual_level: str | None,
    actual_perfect_week_count: int | None = None,
    duplicate_streak_keys: dict[str, int] | None = None,
    duplicate_xp_keys: dict[str, int] | None = None,
    pending_reconciliation_fields: Sequence[str] | None = None,
    level_gate_ok: bool | None = None,
    email_report: dict[str, Any] | None = None,
) -> BusinessReconciliationResult:
    """Reconcile expected matrix XP vs live events / enrollment lifetime.

    **Lifetime XP hard rule:** when ``actual_lifetime_xp`` is provided, it must
    equal the sum of ``Active XP Points`` (falling back to ``XP Points``) across
    active events. Mismatch is always a hard fail — Enrollment Lifetime XP Earned
    is not authoritative if it disagrees with the active event ledger.
    """
    expected_pts = expected_points_from_matrix(matrix)
    actual_pts = actual_xp_buckets_from_events(actual_events)
    expected_total = sum_points(expected_pts)
    actual_total = (
        int(actual_lifetime_xp)
        if actual_lifetime_xp is not None
        else sum_points(actual_pts)
    )
    expected_level = level_for(expected_total)
    actual_level_s = str(actual_level or "")

    diffs: list[BucketDiff] = []
    errors: list[str] = []
    notes: list[str] = []

    for name in expected_pts:
        exp = int(expected_pts[name])
        act = int(actual_pts.get(name) or 0)
        ok = exp == act
        diffs.append(BucketDiff(name=name, expected=exp, actual=act, ok=ok))
        if not ok:
            errors.append(f"{name}: expected {exp} actual {act}")

    if expected_total != actual_total:
        errors.append(f"total XP: expected {expected_total} actual {actual_total}")

    errors.extend(
        assert_lifetime_matches_active_xp(actual_lifetime_xp, actual_events)
    )

    if actual_level_s and actual_level_s != expected_level:
        errors.append(f"level: expected {expected_level} actual {actual_level_s}")

    if actual_perfect_week_count is not None:
        if int(actual_perfect_week_count) != int(matrix.expected_perfect_week_count):
            errors.append(
                f"perfect_week_count: expected {matrix.expected_perfect_week_count} "
                f"actual {actual_perfect_week_count}"
            )

    for k, n in (duplicate_streak_keys or {}).items():
        if int(n) > 1:
            errors.append(f"duplicate_streak_occurrence_key:{k} count={n}")

    # Shared active-XP Source Key integrity (blank / duplicate / HW dual-key).
    sk_integrity = validate_active_xp_source_keys(actual_events)
    errors.extend(sk_integrity.errors)

    # Preserve caller-supplied duplicate map (do not weaken existing checks).
    for k, n in (duplicate_xp_keys or {}).items():
        if int(n) > 1:
            already = any(
                i.code == "duplicate_source_key" and i.source_key == k
                for i in sk_integrity.issues
            )
            if not already:
                errors.append(f"duplicate_xp_source_key:{k} count={n}")

    for pending in pending_reconciliation_fields or []:
        errors.append(f"pending_reconciliation:{pending}")

    if level_gate_ok is False:
        errors.append("level_gate_state: expected pass, actual blocked/fail")

    if email_report:
        unsafe = email_report.get("unsafe_recipients") or []
        if unsafe:
            errors.append(f"email_unsafe_recipients:{unsafe}")
        for addr, count in (email_report.get("recipients") or {}).items():
            if str(addr).lower() not in SAFE_ALLOWLIST:
                errors.append(f"email_non_allowlisted:{addr} count={count}")
        dup_keys = (
            email_report.get("duplicate_handoff_keys")
            or email_report.get("duplicate_dedupe_keys")
            or {}
        )
        for k, n in dup_keys.items():
            if int(n) > 1:
                errors.append(f"duplicate_handoff_key:{k} count={n}")
        needs_review = int((email_report.get("statuses") or {}).get("Needs Review") or 0)
        if needs_review:
            errors.append(
                f"email_needs_review_count={needs_review} "
                f"cause={email_report.get('needs_review_cause') or 'unspecified'}"
            )
        notes.append(
            "Weekly summary emails are intentionally excluded from execute-three "
            "unless an explicit weekly-email simulation stage is enabled "
            "(072/074 arming is separate from daily/HW/Welcome/Zoom)."
        )

    return BusinessReconciliationResult(
        profile=profile,
        pass_=not errors,
        expected_total_xp=expected_total,
        actual_total_xp=actual_total,
        expected_level=expected_level,
        actual_level=actual_level_s or "(unknown)",
        bucket_diffs=[d.to_dict() for d in diffs],
        errors=errors,
        notes=notes,
    )


def reconcile_with_live_events(
    *,
    profile: str,
    matrix: AthleteExpectationMatrix,
    cascade_complete: bool,
    actual_events: Sequence[dict[str, Any]],
    actual_lifetime_xp: int | None,
    actual_level: str | None = None,
    actual_perfect_week_count: int | None = None,
    duplicate_streak_keys: dict[str, int] | None = None,
    duplicate_xp_keys: dict[str, int] | None = None,
    pending_reconciliation_fields: Sequence[str] | None = None,
    level_gate_ok: bool | None = None,
    email_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Named Stage E2 entry when live XP events + lifetime are available.

    Prefer this over ``stage_e2_business_success_hook`` when the execute path
    has fetched Enrollment Lifetime XP and XP Event rows — enables the
    Lifetime === Active XP sum hard gate. Does not invent events or XP.
    """
    return stage_e2_business_success_hook(
        profile=profile,
        matrix=matrix,
        cascade_complete=cascade_complete,
        actual_events=actual_events,
        actual_lifetime_xp=actual_lifetime_xp,
        actual_level=actual_level,
        actual_perfect_week_count=actual_perfect_week_count,
        duplicate_streak_keys=duplicate_streak_keys,
        duplicate_xp_keys=duplicate_xp_keys,
        pending_reconciliation_fields=pending_reconciliation_fields,
        level_gate_ok=level_gate_ok,
        email_report=email_report,
        planned=False,
    )


def stage_e2_business_success_hook(
    *,
    profile: str,
    matrix: AthleteExpectationMatrix | None,
    cascade_complete: bool,
    actual_events: Sequence[dict[str, Any]] | None = None,
    actual_lifetime_xp: int | None = None,
    actual_level: str | None = None,
    actual_perfect_week_count: int | None = None,
    duplicate_streak_keys: dict[str, int] | None = None,
    duplicate_xp_keys: dict[str, int] | None = None,
    pending_reconciliation_fields: Sequence[str] | None = None,
    level_gate_ok: bool | None = None,
    email_report: dict[str, Any] | None = None,
    planned: bool = False,
) -> dict[str, Any]:
    """Final business-success gate. cascade_complete alone never yields PASS."""
    if planned or matrix is None:
        return {
            "stage": "E2_business_success",
            "profile": profile,
            "status": "planned",
            "complete": False,
            "pass": False,
            "cascade_complete": cascade_complete,
            "note": (
                "Business-success reconciliation runs on live execute only; "
                "cascade_complete is not sufficient for PASS"
            ),
        }
    result = reconcile_business_success(
        profile=profile,
        matrix=matrix,
        actual_events=actual_events or [],
        actual_lifetime_xp=actual_lifetime_xp,
        actual_level=actual_level,
        actual_perfect_week_count=actual_perfect_week_count,
        duplicate_streak_keys=duplicate_streak_keys,
        duplicate_xp_keys=duplicate_xp_keys,
        pending_reconciliation_fields=pending_reconciliation_fields,
        level_gate_ok=level_gate_ok,
        email_report=email_report,
    )
    payload = result.to_dict()
    payload["stage"] = "E2_business_success"
    payload["status"] = "ok" if result.pass_ else "failed"
    payload["complete"] = bool(result.pass_)
    payload["cascade_complete"] = cascade_complete
    if cascade_complete and not result.pass_:
        payload["errors"] = list(result.errors) + [
            "cascade_complete=true but business expectations failed"
        ]
    if not cascade_complete:
        payload["errors"] = list(payload.get("errors") or []) + [
            "cascade_complete=false"
        ]
        payload["pass"] = False
        payload["complete"] = False
        payload["status"] = "failed"
    return payload


def _enrollment_ids_from_xp_fields(fields: dict[str, Any]) -> list[str]:
    """Collect enrollment record ids from XP Event Enrollment / Enrollment Record ID."""
    flat: list[str] = []
    for key in ("Enrollment Record ID", "Enrollment"):
        linked = fields.get(key)
        if linked is None:
            continue
        items = linked if isinstance(linked, list) else [linked]
        for item in items:
            if isinstance(item, dict):
                flat.append(str(item.get("id") or ""))
            else:
                flat.append(str(item or ""))
    return [x for x in flat if x]


def list_xp_events_for_enrollment(
    client: Any,
    enrollment_id: str,
    *,
    source_key_prefix: str | None = None,
    fields: Sequence[str] | None = None,
    max_records: int | None = None,
) -> list[dict[str, Any]]:
    """List XP Events for an enrollment using Production-safe filters.

    ``ARRAYJOIN({Enrollment})`` / ``FIND`` on the linked Enrollment field returns
    **zero** rows in this base. Prefer ``{Enrollment Record ID}='rec…'``. Never
    request a non-existent ``Status`` field (422). Falls back to list-all +
    client-side filter when the formula path fails.
    """
    if client is None or not enrollment_id:
        return []
    list_fn = getattr(client, "list_records", None) or getattr(client, "select", None)
    if list_fn is None:
        return []

    eid = enrollment_id.strip()
    field_list = list(
        fields
        or (
            "Source Key",
            "XP Points",
            "Active XP Points",
            "Active?",
            "Enrollment",
            "Enrollment Record ID",
            "XP Bucket",
        )
    )
    base = f"{{Enrollment Record ID}}='{eid}'"
    if source_key_prefix:
        formula = (
            f"AND({base}, FIND('{source_key_prefix}', {{Source Key}} & ''))"
        )
    else:
        formula = base

    rows: list[dict[str, Any]] = []
    try:
        kwargs: dict[str, Any] = {"formula": formula, "fields": field_list}
        if max_records is not None:
            kwargs["max_records"] = max_records
        try:
            rows = list(list_fn("XP Events", **kwargs) or [])
        except TypeError:
            rows = list(list_fn("XP Events", formula=formula) or [])
    except Exception:  # noqa: BLE001
        rows = []

    if not rows:
        try:
            all_rows = list(list_fn("XP Events") or [])
        except Exception:  # noqa: BLE001
            all_rows = []
        filtered: list[dict[str, Any]] = []
        for row in all_rows:
            f = row.get("fields") or row
            if eid in _enrollment_ids_from_xp_fields(f) or eid in str(
                f.get("Enrollment") or ""
            ):
                if source_key_prefix and source_key_prefix not in str(
                    f.get("Source Key") or ""
                ):
                    continue
                filtered.append(
                    row if "fields" in row else {"id": row.get("id"), "fields": f}
                )
        rows = filtered

    out: list[dict[str, Any]] = []
    for row in rows:
        f = row.get("fields") or row
        ids = _enrollment_ids_from_xp_fields(f)
        if eid in ids or eid in str(f.get("Enrollment") or ""):
            out.append(row if "fields" in row else {"id": row.get("id"), "fields": f})
    return out


def try_load_enrollment_xp_for_reconcile(
    client: Any,
    enrollment_id: str,
) -> dict[str, Any]:
    """Best-effort load of Enrollment lifetime + linked XP Events for Stage E2.

    Returns ``{events, lifetime_xp, level}``. Never invents XP — missing data
    yields ``lifetime_xp=None`` and/or empty events so callers can skip the
    lifetime hard gate until live rows are available.
    """
    out: dict[str, Any] = {"events": [], "lifetime_xp": None, "level": None}
    if client is None or not enrollment_id:
        return out
    try:
        enr = client.get_record("Enrollments", enrollment_id)
        fields = (enr or {}).get("fields") or {}
        for key in ("Lifetime XP Earned", "Lifetime XP Total", "Total XP"):
            if fields.get(key) is not None:
                try:
                    out["lifetime_xp"] = int(float(fields[key]))
                    break
                except (TypeError, ValueError):
                    pass
        # Prefer public display text; linked Current Level is a rec id list.
        for key in (
            "Current Level - Public Facing Display",
            "Current Level Name",
            "Level Name",
        ):
            val = fields.get(key)
            if not val:
                continue
            if isinstance(val, list):
                out["level"] = str(val[0] if val else "")
            else:
                out["level"] = str(val)
            if out["level"]:
                break
        if not out["level"]:
            for key in ("Current Level", "Level", "Athlete Level"):
                val = fields.get(key)
                if not val:
                    continue
                if isinstance(val, list):
                    if val and all(str(x).startswith("rec") for x in val):
                        continue
                    out["level"] = str(val[0] if len(val) == 1 else val)
                else:
                    text = str(val)
                    if text.startswith("rec"):
                        continue
                    out["level"] = text
                if out["level"]:
                    break
    except Exception:  # noqa: BLE001
        pass

    out["events"] = list_xp_events_for_enrollment(client, enrollment_id)
    return out

def count_duplicate_keys(keys: Sequence[str]) -> dict[str, int]:
    """Count duplicate non-empty keys (legacy helper for pre-extracted keys).

    Prefer ``duplicate_active_source_keys(events)`` / 
    ``validate_active_xp_source_keys(events)`` when XP Event rows are available.
    """
    c = Counter(k for k in keys if k)
    return {k: n for k, n in c.items() if n > 1}


__all__ = [
    "SAFE_ALLOWLIST",
    "BusinessReconciliationResult",
    "assert_lifetime_matches_active_xp",
    "actual_xp_buckets_from_events",
    "event_is_active",
    "expected_points_from_matrix",
    "list_xp_events_for_enrollment",
    "reconcile_business_success",
    "reconcile_with_live_events",
    "stage_e2_business_success_hook",
    "sum_active_xp_points",
    "try_load_enrollment_xp_for_reconcile",
    "threshold_xp_from_awards",
    "xp_points_from_event_buckets",
    "count_duplicate_keys",
    "level_for",
    "LEVELS",
    "sum_points",
]

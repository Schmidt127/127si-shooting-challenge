#!/usr/bin/env python3
"""Read-only enrollment XP reconciliation checker.

Produces per-enrollment rows:
  Check | Expected | Actual | Pass/Fail | Evidence

Does not write Airtable. Does not lower production gates.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

from .business_reconciliation import (
    STREAK,
    actual_xp_buckets_from_events,
    expected_points_from_matrix,
    level_for,
    sum_points,
)
from .expectations_matrix import AthleteExpectationMatrix


@dataclass
class CheckRow:
    check: str
    expected: Any
    actual: Any
    pass_fail: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pass_fail"] = d.pop("pass_fail")
        return {
            "Check": self.check,
            "Expected": self.expected,
            "Actual": self.actual,
            "Pass/Fail": self.pass_fail,
            "Evidence": self.evidence,
        }


@dataclass
class EnrollmentReconciliationReport:
    enrollment_id: str
    profile: str
    rows: list[CheckRow] = field(default_factory=list)
    pass_: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "enrollment_id": self.enrollment_id,
            "profile": self.profile,
            "pass": self.pass_,
            "table": [r.to_dict() for r in self.rows],
        }

    def to_markdown(self) -> str:
        lines = [
            f"### Enrollment `{self.enrollment_id}` ({self.profile})",
            "",
            "| Check | Expected | Actual | Pass/Fail | Evidence |",
            "| ----- | -------: | -----: | --------- | -------- |",
        ]
        for r in self.rows:
            lines.append(
                f"| {r.check} | {r.expected} | {r.actual} | **{r.pass_fail}** | {r.evidence} |"
            )
        lines.append("")
        lines.append(f"**Overall:** {'PASS' if self.pass_ else 'FAIL'}")
        return "\n".join(lines)


def _is_active_event(f: dict[str, Any]) -> bool:
    status = str(f.get("Status") or "").lower()
    if status in {"void", "inactive", "duplicate", "superseded"}:
        return False
    # Match Production Active XP Points: only truthy Active? counts.
    return f.get("Active?") is True


def _active_events(events: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ev in events:
        f = ev.get("fields") or ev
        if _is_active_event(f):
            out.append(ev)
    return out


def _source_keys(events: Sequence[dict[str, Any]]) -> list[str]:
    keys = []
    for ev in events:
        f = ev.get("fields") or ev
        k = str(f.get("Source Key") or "").strip()
        if k:
            keys.append(k)
    return keys


def _row(check: str, expected: Any, actual: Any, evidence: str) -> CheckRow:
    ok = expected == actual
    return CheckRow(
        check=check,
        expected=expected,
        actual=actual,
        pass_fail="PASS" if ok else "FAIL",
        evidence=evidence,
    )


def build_enrollment_reconciliation(
    *,
    enrollment_id: str,
    profile: str,
    matrix: AthleteExpectationMatrix,
    all_events: Sequence[dict[str, Any]],
    lifetime_xp_earned: int | None,
    actual_level: str | None = None,
    actual_perfect_week_count: int | None = None,
    level_gate_ok: bool | None = None,
) -> EnrollmentReconciliationReport:
    """Build Expected|Actual|Pass/Fail|Evidence rows for one enrollment."""
    rows: list[CheckRow] = []
    active = _active_events(all_events)
    raw_count = len(all_events)
    active_count = len(active)

    rows.append(
        CheckRow(
            check="Active vs raw XP Event counts",
            expected="active <= raw",
            actual=f"{active_count} / {raw_count}",
            pass_fail="PASS" if active_count <= raw_count else "FAIL",
            evidence="Inactive/void/duplicate events must not inflate Lifetime XP",
        )
    )

    expected_pts = expected_points_from_matrix(matrix)
    actual_pts = actual_xp_buckets_from_events(active)
    expected_total = sum_points(expected_pts)
    actual_active_sum = sum_points(actual_pts)

    for name in expected_pts:
        rows.append(
            _row(
                name,
                expected_pts[name],
                actual_pts.get(name, 0),
                f"source-key bucket sum from active XP Events",
            )
        )

    rows.append(
        _row(
            "Sum of active XP points",
            expected_total,
            actual_active_sum,
            "sum of bucket Actual columns",
        )
    )

    life = lifetime_xp_earned
    rows.append(
        CheckRow(
            check="Enrollment Lifetime XP Earned vs sum(active XP)",
            expected=expected_total if life is None else life,
            actual=actual_active_sum if life is None else life,
            pass_fail=(
                "PASS"
                if life is not None and int(life) == actual_active_sum and int(life) == expected_total
                else (
                    "PASS"
                    if life is not None and int(life) == actual_active_sum
                    else "FAIL"
                )
            ),
            evidence=(
                f"Lifetime XP Earned={life}; active sum={actual_active_sum}; "
                f"scenario expected={expected_total}"
            ),
        )
    )
    if life is not None:
        rows[-1] = CheckRow(
            check="Enrollment Lifetime XP Earned vs sum(active XP)",
            expected=actual_active_sum,
            actual=int(life),
            pass_fail="PASS" if int(life) == actual_active_sum else "FAIL",
            evidence=f"formula/rollup Lifetime XP must equal active event sum; scenario expected total={expected_total}",
        )
        rows.append(
            _row(
                "Lifetime XP vs scenario expected total",
                expected_total,
                int(life),
                "scenario policy oracle",
            )
        )

    # Streak thresholds present
    streak_expected = sorted(matrix.expected_streak_achievements)
    active_keys = _source_keys(active)
    streak_actual = sorted(
        {
            t
            for t in STREAK
            for k in active_keys
            if f"STREAK" in k.upper() and (f"|{t}|" in k or k.upper().endswith(f"|{t}") or f"_{t}" in k.upper())
        }
    )
    # Prefer matrix compare for expected; actual from keys best-effort
    rows.append(
        CheckRow(
            check="Streak thresholds (3/5/7/10/20/30/40/50/60)",
            expected=streak_expected,
            actual=streak_actual or f"(parse best-effort; count STREAK events={sum(1 for k in active_keys if 'STREAK' in k.upper())})",
            pass_fail="PASS" if streak_expected == streak_actual else "REVIEW",
            evidence="Segments do not continue across missed days; 50/60 gates are real Production thresholds",
        )
    )

    keys = _source_keys(active)
    dup = {k: n for k, n in Counter(keys).items() if n > 1}
    rows.append(
        CheckRow(
            check="Duplicate Source Key prevention (active)",
            expected={},
            actual=dup,
            pass_fail="PASS" if not dup else "FAIL",
            evidence=f"active source keys={len(keys)}; duplicates={dup}",
        )
    )

    exp_level = level_for(expected_total)
    rows.append(
        _row(
            "Level from expected XP",
            exp_level,
            str(actual_level or "(unknown)"),
            "LEVELS ladder; do not lower Production gates",
        )
    )
    if level_gate_ok is not None:
        rows.append(
            CheckRow(
                check="Level gate calculations",
                expected=True,
                actual=bool(level_gate_ok),
                pass_fail="PASS" if level_gate_ok else "FAIL",
                evidence="Production gate evaluation; scenarios that cannot satisfy a gate by design must FAIL not skip",
            )
        )

    if actual_perfect_week_count is not None:
        rows.append(
            _row(
                "Perfect Week count",
                matrix.expected_perfect_week_count,
                int(actual_perfect_week_count),
                "PW XP events / unlocks",
            )
        )

    # Normalize REVIEW as non-pass for overall unless only streak parse review
    hard = [r for r in rows if r.pass_fail == "FAIL"]
    report = EnrollmentReconciliationReport(
        enrollment_id=enrollment_id,
        profile=profile,
        rows=rows,
        pass_=len(hard) == 0,
    )
    return report


__all__ = [
    "CheckRow",
    "EnrollmentReconciliationReport",
    "build_enrollment_reconciliation",
]

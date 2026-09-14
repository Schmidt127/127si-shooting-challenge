"""SC-SEASON-SIM-001 Perfect Mike Schmidt single-athlete execute path.

Runs ONLY the Perfect scenario with Mike Schmidt identity. Reuses
execute_three writer / settlement / cleanup gates for one profile.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .business_reconciliation import (
    reconcile_with_live_events,
    stage_e2_business_success_hook,
    try_load_enrollment_xp_for_reconcile,
)
from .cascade_settlement import stage_d_settlement_hook, stage_e_reconcile_hook
from .cleanup import stage_h_post_cascade_hooks
from .confirmation import ConfirmationError, require_execute_gates
from .constants import SAFE_EMAIL_RECIPIENT, SIM_START
from .downstream_settlement import stage_d_downstream_settlement_hook
from .execute_three import (
    DEFAULT_PROFILE_SETTLEMENT_POLL_S,
    DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
    _count_client_writes,
    _run_profile_writer,
    _stage_stub,
    profile_ownership_namespace,
    profile_registry_run_id,
)
from .expectations_matrix import build_athlete_expectation_matrix
from .formula_lifecycle import (
    restore_production_formulas,
    snapshot_formulas,
    stage_f_formula_verify_hook,
)
from .live_write_contract import (
    assert_live_write_contract_pass,
    build_contract_validation_for_client,
)
from .rearm_submission_xp import run_rearm_submission_xp
from .reference_data import load_reference_snapshot
from .run_registry import (
    load_registry,
    new_perfect_run_id,
    save_registry,
    validate_run_id,
)
from .scenarios_sc001 import build_athlete1_perfect_scenario
from .simulation_clock import SimulationClock
from .writer import build_execute_context_from_reference

PERFECT_PROFILE = "athlete1_perfect"
MIKE_FIRST = "Mike"
MIKE_LAST = "Schmidt"


def build_mike_schmidt_perfect_scenario(
    *,
    run_id: str,
    grade_band_id: str,
    goal_record_id: str,
    goal_total_shots: int,
    homework: list[dict[str, Any]],
    zoom_meetings: list[dict[str, Any]],
    weeks: list[dict[str, Any]] | None = None,
) -> Any:
    """Perfect SC-001 scenario with Mike Schmidt identity override."""
    return build_athlete1_perfect_scenario(
        run_id=run_id,
        grade_band_id=grade_band_id,
        goal_record_id=goal_record_id,
        goal_total_shots=goal_total_shots,
        homework=homework,
        zoom_meetings=zoom_meetings,
        weeks=weeks,
        athlete_first_name=MIKE_FIRST,
        athlete_last_name=MIKE_LAST,
    )


def _offline_homework_20() -> list[dict[str, Any]]:
    labels = ("Early Bird",) + tuple(f"Week {i}" for i in range(1, 10))
    out: list[dict[str, Any]] = []
    for i in range(20):
        label = labels[i // 2]
        out.append(
            {
                "record_id": f"recOFFHW{i + 1:02d}",
                "slot": "HW1" if i % 2 == 0 else "HW2",
                "library_id": f"recOFFLIB{i + 1:02d}",
                "display": f"PHA | {label} | HW{'1' if i % 2 == 0 else '2'}",
            }
        )
    return out


def run_execute_perfect(
    *,
    run_id: str | None = None,
    execute: bool = False,
    confirm: str | None = None,
    confirm_disposable: str | None = None,
    registry_dir: Path,
    out_dir: Path,
    client: Any | None = None,
    offline_fixture: bool = False,
    allow_writes: bool = False,
    enable_email_delivery: bool = False,
    acknowledge_clock_override: bool = False,
) -> dict[str, Any]:
    """Gated single-profile Perfect Mike Schmidt execute.

    Requires ``--execute``, confirm tokens, and ``--simulation-id``
    (prefer ``SEASON-SIM-PERFECT-<UTC>-mike-schmidt`` via ``new_perfect_run_id``).
    Marker format remains ``SEASON-SIM|<run_id>``.
    """
    rid = validate_run_id(run_id or new_perfect_run_id())
    writes_allowed = bool(execute and allow_writes)
    profile = PERFECT_PROFILE
    payload: dict[str, Any] = {
        "backlog_id": "SC-SEASON-SIM-001",
        "command": "execute-perfect",
        "run_id": rid,
        "profile": profile,
        "athlete": {
            "first_name": MIKE_FIRST,
            "last_name": MIKE_LAST,
            "display_name": f"{MIKE_FIRST} {MIKE_LAST}",
            "parent_email": SAFE_EMAIL_RECIPIENT,
        },
        "gates_passed": False,
        "errors": [],
        "stages": {},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if execute:
        try:
            require_execute_gates(
                execute=True,
                confirm=confirm,
                confirm_disposable=confirm_disposable,
                simulation_id=rid,
                action="perfect Mike Schmidt season simulation execute",
            )
            payload["gates_passed"] = True
        except ConfirmationError as exc:
            payload["errors"].append(str(exc))
            return payload

    snap = None
    if offline_fixture:
        scenario = build_mike_schmidt_perfect_scenario(
            run_id=rid,
            grade_band_id="recOFFGB",
            goal_record_id="recOFFGOAL",
            goal_total_shots=12000,
            homework=_offline_homework_20(),
            zoom_meetings=[
                {"record_id": "recZ1", "display": "Live"},
                {"record_id": "recZ2", "display": "Rec"},
            ],
            weeks=[],
        )
    else:
        if client is None:
            payload["errors"].append("client required when not --offline-fixture")
            return payload
        snap = load_reference_snapshot(client)
        if snap.errors or not snap.grade_band or not snap.highest_goal:
            payload["errors"].extend(snap.errors or ["missing grade band / goal"])
            return payload
        scenario = build_mike_schmidt_perfect_scenario(
            run_id=rid,
            grade_band_id=snap.grade_band.record_id,
            goal_record_id=snap.highest_goal.record_id,
            goal_total_shots=int(snap.highest_goal.total_shot_target or 0),
            homework=list(snap.homework or []),
            zoom_meetings=list(snap.zoom_meetings or []),
            weeks=list(snap.weeks_covering_window or []),
        )

    if scenario.athlete.get("display_name") != f"{MIKE_FIRST} {MIKE_LAST}":
        payload["errors"].append("athlete identity override failed")
        return payload
    if str(scenario.athlete.get("parent_email") or "") != SAFE_EMAIL_RECIPIENT:
        payload["errors"].append(f"parent email must be {SAFE_EMAIL_RECIPIENT}")
        return payload

    profile_payload: dict[str, Any] = {
        "profile": profile,
        "athlete": scenario.athlete,
        "ownership_namespace": profile_ownership_namespace(rid, profile),
        "intended_writes_summary": scenario.intended_writes_summary,
    }
    snapshot_result: dict[str, Any] | None = None
    clock = SimulationClock(enabled=True, current_date=SIM_START, run_id=rid)

    try:
        if writes_allowed and client is not None:
            snapshot_result = snapshot_formulas(client)
            profile_payload["A_formula_snapshot"] = snapshot_result
            contract = build_contract_validation_for_client(client)
            assert_live_write_contract_pass(contract)

        execute_context = None
        if snap is not None:
            execute_context = build_execute_context_from_reference(
                scenario=scenario,
                weeks=snap.weeks_covering_window,
                school_year="2026-2027",
            )

        writer_result = _run_profile_writer(
            scenario=scenario,
            clock=clock,
            run_id=rid,
            profile=profile,
            registry_dir=registry_dir,
            client=client,
            allow_writes=writes_allowed,
            execute=execute,
            confirm=confirm,
            confirm_disposable=confirm_disposable,
            enable_email_delivery=enable_email_delivery,
            acknowledge_clock_override=acknowledge_clock_override,
            execute_context=execute_context,
        )
        profile_payload["C_writer"] = writer_result

        reg = None
        try:
            reg = load_registry(registry_dir, profile_registry_run_id(rid, profile))
        except FileNotFoundError:
            reg = None

        if writes_allowed and execute and reg is not None:
            settlement = stage_d_settlement_hook(
                client,
                reg,
                run_id=rid,
                profile=profile,
                allow_writes=False,
                timeout_s=DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
                poll_interval_s=DEFAULT_PROFILE_SETTLEMENT_POLL_S,
            )
            stuck = ((settlement.get("result") or {}).get("stuck") or [])
            if stuck and not settlement.get("complete"):
                rearm = run_rearm_submission_xp(
                    run_id=profile_registry_run_id(rid, profile),
                    registry_dir=registry_dir,
                    client=client,
                    execute=True,
                    confirm=confirm,
                    confirm_disposable=confirm_disposable,
                    out_dir=out_dir,
                )
                settlement["rearm"] = rearm.to_dict()
                settlement = stage_d_settlement_hook(
                    client,
                    reg,
                    run_id=rid,
                    profile=profile,
                    allow_writes=False,
                    timeout_s=DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
                    poll_interval_s=DEFAULT_PROFILE_SETTLEMENT_POLL_S,
                )
                settlement["rearm_applied"] = True
            matrix = build_athlete_expectation_matrix(scenario)
            downstream = stage_d_downstream_settlement_hook(
                client,
                reg,
                run_id=rid,
                profile=profile,
                expected_perfect_weeks=matrix.expected_perfect_week_count,
                expected_threshold_events=len(matrix.expected_weekly_threshold_awards),
                expected_streak_thresholds=list(matrix.expected_streak_achievements),
                timeout_s=DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
                poll_interval_s=DEFAULT_PROFILE_SETTLEMENT_POLL_S,
            )
            settlement["downstream"] = downstream
            if not downstream.get("complete"):
                settlement["complete"] = False
                settlement["status"] = "failed"
                settlement.setdefault("errors", []).extend(
                    downstream.get("errors") or ["downstream settlement failed"]
                )
            profile_payload["D_settlement"] = settlement
        else:
            profile_payload["D_settlement"] = {
                "stage": "D_settlement",
                "profile": profile,
                "status": "planned",
                "complete": False,
            }

        created_n = len(writer_result.get("created_records") or [])
        reconcile = stage_e_reconcile_hook(
            profile_payload.get("D_settlement"),
            profile=profile,
            writer_created=created_n,
        )
        if not writes_allowed or not execute:
            reconcile = {
                **reconcile,
                "status": "planned",
                "complete": False,
                "errors": [],
            }
        profile_payload["E_reconcile"] = reconcile

        matrix_for_biz = build_athlete_expectation_matrix(scenario)
        if (
            writes_allowed
            and execute
            and client is not None
            and reg is not None
            and reg.enrollment_id
        ):
            live = try_load_enrollment_xp_for_reconcile(client, reg.enrollment_id)
            business = reconcile_with_live_events(
                profile=profile,
                matrix=matrix_for_biz,
                cascade_complete=bool(reconcile.get("complete")),
                actual_events=live.get("events") or [],
                actual_lifetime_xp=live.get("lifetime_xp"),
                actual_level=live.get("level"),
            )
        else:
            business = stage_e2_business_success_hook(
                profile=profile,
                matrix=matrix_for_biz,
                cascade_complete=bool(reconcile.get("complete")),
                planned=not (writes_allowed and execute),
            )
        profile_payload["E2_business_success"] = business

        profile_payload["F_formula_verify"] = stage_f_formula_verify_hook(
            client,
            expect_gated=acknowledge_clock_override,
            snapshot_bundle=(snapshot_result or {}).get("bundle") if snapshot_result else None,
        )
        profile_payload["H_post_cascade_hooks"] = stage_h_post_cascade_hooks(
            run_id=rid,
            registry_dir=registry_dir,
            client=client,
            profile=profile,
        )

        if writes_allowed and execute and reg is not None:
            if not reconcile.get("complete") or not business.get("pass"):
                reg.status = "paused"
                payload["errors"].append(
                    "reconciliation FAIL — "
                    + "; ".join(
                        list(reconcile.get("errors") or [])
                        + list(business.get("errors") or [])
                        or ["expectations unmet"]
                    )
                )
            else:
                reg.status = "complete"
            save_registry(reg, registry_dir)

    except Exception as exc:  # noqa: BLE001
        payload["errors"].append(f"execute-perfect failed: {exc}")
    finally:
        if writes_allowed and client is not None and snapshot_result:
            try:
                restore_production_formulas(client, snapshot_result.get("bundle"))
            except Exception as exc:  # noqa: BLE001
                payload["errors"].append(f"formula restore: {exc}")

    payload["profile_result"] = profile_payload
    payload["client_writes"] = _count_client_writes(client)
    payload["stages"]["Z_formula_restore"] = _stage_stub(
        "Z_formula_restore", allow_writes=writes_allowed, profile=profile
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"execute-perfect-{rid}.json"
    report_path.write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    payload["report_path"] = str(report_path)
    return payload


__all__ = [
    "MIKE_FIRST",
    "MIKE_LAST",
    "build_mike_schmidt_perfect_scenario",
    "run_execute_perfect",
]

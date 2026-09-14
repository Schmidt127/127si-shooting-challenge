"""Zero-write Perfect launch proof (no Airtable mutations)."""

from __future__ import annotations

import inspect
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .active_xp_source_key_integrity import validate_active_xp_source_keys
from .cleanup import stage_h_post_cascade_hooks
from .constants import SAFE_EMAIL_RECIPIENT
from .downstream_settlement import DEFAULT_TIMEOUT_S as DOWNSTREAM_TIMEOUT_S
from .email_producer_mode_config import build_email_producer_mode_report
from .execute_perfect import (
    PERFECT_PROFILE,
    build_mike_schmidt_perfect_scenario,
    run_execute_perfect,
)
from .execute_three import DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S
from .live_write_contract import (
    EXPECTED_PERFECT_SEASON_XP,
    build_contract_validation_for_client,
)
from .production_normal_formulas import load_production_normal_bundle
from .recipient_safety import assert_safe_recipient
from .reference_data import WeekInfo
from .run_registry import new_perfect_run_id
from .scenario_base import summarize_scenario
from .scenarios import _week_id_to_label, group_phas_by_homework_week
from .simulation_process_lock import (
    SimulationProcessLockError,
    acquire_simulation_lock,
    release_simulation_lock,
)


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def run_perfect_launch_proof(
    *,
    out_dir: Path,
    registry_dir: Path,
    client: Any | None = None,
) -> dict[str, Any]:
    """Plan-only Perfect launch proof. Never enables Airtable writes."""
    rid = new_perfect_run_id()
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    client_writes = 0
    by_label: dict[str, list] = {}

    weeks = [
        WeekInfo(
            record_id=f"recWEEK{i:02d}",
            name=label,
            start=None,
            end=None,
            program_instance_id="recPI",
        )
        for i, label in enumerate(
            ("Early Bird",) + tuple(f"Week {i}" for i in range(1, 10))
        )
    ]
    hw = []
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

    scenario = None
    try:
        labels = _week_id_to_label(weeks)
        by_label = group_phas_by_homework_week(hw, weeks)
        scenario = build_mike_schmidt_perfect_scenario(
            run_id=rid,
            grade_band_id="recGB",
            goal_record_id="recGOAL",
            goal_total_shots=12000,
            homework=hw,
            zoom_meetings=[
                {"record_id": "recZ1", "display": "Live"},
                {"record_id": "recZ2", "display": "Recording"},
            ],
            weeks=weeks,
        )
        ok = (
            labels.get("recWEEK00") == "Early Bird"
            and len(by_label["Week 9"]) == 2
            and scenario.athlete.get("display_name") == "Mike Schmidt"
            and scenario.athlete.get("parent_email") == SAFE_EMAIL_RECIPIENT
        )
        checks.append(
            _check(
                "weekinfo_perfect_scenario",
                ok,
                f"week9_hw={len(by_label['Week 9'])} "
                f"athlete={scenario.athlete.get('display_name')}",
            )
        )
        if not ok:
            errors.append("WeekInfo / Perfect scenario identity failed")
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("weekinfo_perfect_scenario", False, str(exc)))
        errors.append(f"WeekInfo scenario: {exc}")

    dry = run_execute_perfect(
        run_id=rid,
        execute=False,
        registry_dir=registry_dir,
        out_dir=out_dir,
        client=client,
        offline_fixture=True,
        allow_writes=False,
        enable_email_delivery=False,
    )
    client_writes += int(dry.get("client_writes") or 0)
    dry_ok = (
        not dry.get("errors")
        and dry.get("athlete", {}).get("parent_email") == SAFE_EMAIL_RECIPIENT
        and client_writes == 0
    )
    checks.append(
        _check(
            "execute_perfect_offline_dry",
            dry_ok,
            f"errors={dry.get('errors')} client_writes={client_writes}",
        )
    )
    if not dry_ok:
        errors.extend(list(dry.get("errors") or []) or ["dry execute-perfect failed"])

    h = stage_h_post_cascade_hooks(
        run_id=rid,
        registry_dir=registry_dir,
        client=None,
        profile=PERFECT_PROFILE,
    )
    h_ok = h.get("path") == "perfect_or_single" and h.get("status") == "ok"
    checks.append(
        _check(
            "stage_h_perfect_run_id",
            h_ok,
            f"path={h.get('path')} status={h.get('status')} errors={h.get('errors')}",
        )
    )
    if not h_ok:
        errors.append("Stage H did not accept PERFECT run id")

    lock_ok = False
    try:
        acquire_simulation_lock(registry_dir=registry_dir, run_id=rid)
        try:
            acquire_simulation_lock(
                registry_dir=registry_dir,
                run_id="SEASON-SIM-PERFECT-20990101T000000Z-mike-schmidt",
            )
            errors.append("second lock acquire should have failed")
        except SimulationProcessLockError:
            lock_ok = True
        finally:
            release_simulation_lock(registry_dir=registry_dir, run_id=rid)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"lock: {exc}")
    checks.append(_check("exclusive_process_lock", lock_ok, "second acquire blocked"))

    sk = validate_active_xp_source_keys([])
    checks.append(
        _check(
            "active_xp_source_key_integrity",
            sk.ok,
            f"issues={len(sk.issues)}",
        )
    )
    if not sk.ok:
        errors.extend(sk.errors)

    if scenario is not None:
        summary = summarize_scenario(scenario.days, profile=PERFECT_PROFILE)
        live = sum(
            1
            for d in scenario.days
            for m in d.zoom_modes
            if str(m).lower() == "live"
        )
        rec = sum(
            1
            for d in scenario.days
            for m in d.zoom_modes
            if "record" in str(m).lower()
        )
        checks.append(
            _check(
                "pha_week9_x2",
                summary["homework_completions"] == 20
                and len(by_label.get("Week 9", [])) == 2,
                f"hw={summary['homework_completions']} "
                f"week9={len(by_label.get('Week 9', []))}",
            )
        )
        checks.append(
            _check(
                "zoom_live_and_recording_plan",
                live >= 1 and rec >= 1,
                f"live={live} recording={rec}",
            )
        )
    else:
        checks.append(_check("pha_week9_x2", False, "no scenario"))
        checks.append(_check("zoom_live_and_recording_plan", False, "no scenario"))

    checks.append(
        _check(
            "active_xp_oracle_4980",
            EXPECTED_PERFECT_SEASON_XP == 4980,
            f"EXPECTED_PERFECT_SEASON_XP={EXPECTED_PERFECT_SEASON_XP}",
        )
    )

    settle_ok = (
        float(DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S) >= 900.0
        and float(DOWNSTREAM_TIMEOUT_S) >= 900.0
    )
    checks.append(
        _check(
            "settlement_timeout_900s",
            settle_ok,
            f"profile={DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S} "
            f"downstream={DOWNSTREAM_TIMEOUT_S}",
        )
    )

    try:
        bundle = load_production_normal_bundle()
        hashes = bundle.hashes()
        formula_ok = bool(hashes) and all(
            "SEASON-SIM" not in (fld.formula_text or "")
            for fld in bundle.fields
        )
        checks.append(
            _check(
                "production_normal_formula_bundle",
                formula_ok,
                f"fields={list(hashes.keys())}",
            )
        )
        if not formula_ok:
            errors.append("Production-normal bundle missing or contains SEASON-SIM")
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("production_normal_formula_bundle", False, str(exc)))
        errors.append(str(exc))

    recip_ok = True
    try:
        assert_safe_recipient(SAFE_EMAIL_RECIPIENT)
        try:
            assert_safe_recipient("other@example.com")
            recip_ok = False
            errors.append("recipient hard-stop did not fire")
        except ValueError:
            recip_ok = True
    except Exception as exc:  # noqa: BLE001
        recip_ok = False
        errors.append(str(exc))
    checks.append(
        _check("recipient_hard_stop", recip_ok, f"allowlist={SAFE_EMAIL_RECIPIENT}")
    )

    sig = inspect.signature(build_contract_validation_for_client)
    has_run_id = "run_id" in sig.parameters
    checks.append(
        _check(
            "contract_validation_requires_run_id",
            has_run_id,
            f"params={list(sig.parameters)}",
        )
    )

    email_modes = build_email_producer_mode_report().to_dict()

    ok = all(c["ok"] for c in checks) and client_writes == 0 and not errors
    payload = {
        "command": "prove-perfect-launch",
        "run_id": rid,
        "ok": ok,
        "client_writes": client_writes,
        "checks": checks,
        "errors": errors,
        "email_producer_modes": email_modes,
        "settlement_timeout_s": DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
        "expected_perfect_season_xp": EXPECTED_PERFECT_SEASON_XP,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"perfect-launch-proof-{rid}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["report_path"] = str(path)
    return payload


__all__ = ["run_perfect_launch_proof"]

#!/usr/bin/env python3
"""One-pass closeout for SEASON-SIM-2027-20260913T010724Z-threeathlete."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from season_simulation.airtable_client import AirtableClient  # noqa: E402
from season_simulation.constants import DEFAULT_BASE_ID  # noqa: E402
from season_simulation.confirmation import (  # noqa: E402
    CONFIRM_DISPOSABLE_TOKEN,
    CONFIRM_THREE_ATHLETE_TOKEN,
    CONFIRM_TOKEN,
    THREE_ATHLETE_AUTHORIZATION_PHRASE,
)
from typing import Any

from season_simulation.execute_three import run_execute_three  # noqa: E402
from season_simulation.formula_lifecycle import (  # noqa: E402
    FormulaFieldSnapshot,
    FormulaSnapshotBundle,
    restore_production_formulas,
    save_formula_snapshot,
    snapshot_formulas,
    verify_formula_state,
)
from season_simulation.production_formula_rollback import (  # noqa: E402
    PRODUCTION_FORMULA_ROLLBACK,
)
from season_simulation.handoff_monitor import (  # noqa: E402
    capture_handoff_baseline,
    verify_no_new_run_handoffs,
)
from season_simulation.registry_hydrate import hydrate_registry_from_execute_three_report  # noqa: E402

RUN_ID = "SEASON-SIM-2027-20260913T010724Z-threeathlete"
REPORT_PATH = (
    ROOT
    / "tools/season_simulation/reports/execute-three-SEASON-SIM-2027-20260913T010724Z-threeathlete.json"
)
REGISTRY_DIR = ROOT / "tools/season_simulation/run_registries"
OUT_DIR = ROOT / "tools/season_simulation/reports"
SNAPSHOT_PATH = OUT_DIR / f"formula-snapshot-{RUN_ID}.json"
CLOSEOUT_PATH = OUT_DIR / f"campaign-closeout-{RUN_ID}.json"

ATHLETE1_ENROLLMENT = "recFcH7qLPzzso9s3"


def _preflight(client: AirtableClient, *, baseline: Any) -> dict:
    errors: list[str] = []
    meta = client.meta_tables()
    verify = verify_formula_state(
        meta,
        expect_production_normal=False,
        expect_gated=True,
    )
    if not verify.gated_detected:
        errors.append("Season Sim formula gates not detected live")
    # Profile absent = no *complete* enrollment+submissions for this run's profile marker.
    for profile, last in (("athlete2_recovery", "Recovery"), ("athlete3_edge", "Edge")):
        reg_path = REGISTRY_DIR / f"SEASON-SIM-2027-20260913T010724Z-threeathlete__{profile.replace('_', '-')}.json"
        if reg_path.exists():
            reg_data = json.loads(reg_path.read_text(encoding="utf-8"))
            if str(reg_data.get("status")) == "complete":
                errors.append(f"{profile} registry already complete — unexpected for resume")
            continue
        enrs = client.list_records(
            "Enrollments",
            formula=f"AND({{Athlete First Name}}='Sim', {{Athlete Last Name}}='{last}')",
            max_records=5,
        )
        if not enrs:
            continue
        for enr in enrs:
            subs = client.list_records(
                "Submissions",
                formula=(
                    f"AND(FIND('{RUN_ID}', {{Video Upload Note}}), "
                    f"FIND('athlete{last.lower()}', {{Video Upload Note}}))"
                ),
                max_records=100,
            )
            if len(subs) > 50:
                errors.append(
                    f"{profile}: partial/live progress ({len(subs)} submissions) "
                    f"without complete registry — hydrate before execute"
                )
    try:
        enr = client.get_record("Enrollments", ATHLETE1_ENROLLMENT)
        xp_n = len((enr.get("fields") or {}).get("XP Events") or [])
        if xp_n != 168:
            errors.append(f"Athlete 1 XP Events link count changed: {xp_n} (expected 168)")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Athlete 1 enrollment check failed: {exc}")
    handoff = verify_no_new_run_handoffs(
        client, baseline=baseline, run_id=RUN_ID, strict_any_new_row=True
    )
    return {
        "ok": not errors,
        "errors": errors,
        "formula_verify": verify.to_dict(),
        "handoff_preflight": handoff.to_dict(),
    }


def main() -> int:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    client = AirtableClient(base_id=DEFAULT_BASE_ID, allow_writes=True)
    closeout: dict[str, Any] = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phases": {},
        "verdict": "BLOCKED",
    }

    # Phase 0 — hydrate Athlete 1 registry for resume/idempotency
    if REPORT_PATH.exists():
        hydrate_registry_from_execute_three_report(
            report_path=REPORT_PATH,
            profile="athlete1_perfect",
            registry_dir=REGISTRY_DIR,
            run_id=RUN_ID,
        )
        closeout["phases"]["registry_hydrate"] = {"athlete1_perfect": "ok"}

    baseline = capture_handoff_baseline(client, run_id=RUN_ID)
    closeout["phases"]["handoff_baseline"] = {
        "total_queue_rows": baseline.total_queue_rows,
        "run_attributable_rows": baseline.run_attributable_rows,
        "captured_at": baseline.captured_at,
    }

    # Production rollback bundle (Stage Z) — never snapshot gated formulas as restore target.
    captured_at = datetime.now(timezone.utc).isoformat()
    prod_snapshots = [
        FormulaFieldSnapshot(
            table=table,
            field_name=field,
            field_id="",
            formula_text=formula,
            captured_at=captured_at,
        )
        for table, field, formula in PRODUCTION_FORMULA_ROLLBACK
    ]
    prod_bundle = FormulaSnapshotBundle(
        snapshots=prod_snapshots,
        base_id=DEFAULT_BASE_ID,
        run_id=RUN_ID,
        notes=["production rollback texts from production_formula_rollback.py"],
    )
    save_formula_snapshot(prod_bundle, SNAPSHOT_PATH)
    bundle = prod_bundle.to_dict()
    closeout["phases"]["formula_snapshot"] = {
        "path": str(SNAPSHOT_PATH),
        "status": "ok",
        "source": "production_formula_rollback",
    }

    preflight = _preflight(client, baseline=baseline)
    closeout["phases"]["preflight"] = preflight
    if not preflight["ok"]:
        CLOSEOUT_PATH.write_text(json.dumps(closeout, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(closeout, indent=2))
        return 2

    # Phase 2 — execute Athlete 2 + 3 (Athlete 1 resume-skip)
    exec_result = run_execute_three(
        run_id=RUN_ID,
        execute=True,
        confirm=CONFIRM_TOKEN,
        confirm_disposable=CONFIRM_DISPOSABLE_TOKEN,
        confirm_three_athlete=CONFIRM_THREE_ATHLETE_TOKEN,
        authorization_phrase=THREE_ATHLETE_AUTHORIZATION_PHRASE,
        registry_dir=REGISTRY_DIR,
        out_dir=OUT_DIR,
        client=client,
        allow_writes=True,
        enable_email_delivery=False,
        suppress_simulation_email=True,
        acknowledge_clock_override=True,
        defer_formula_restore=True,
        resume_complete_profiles=True,
        continue_on_business_fail=True,
        handoff_baseline=baseline,
        confirm_for_formula=CONFIRM_TOKEN,
    )
    closeout["phases"]["execute_three"] = {
        "errors": exec_result.get("errors"),
        "profile_results_keys": list((exec_result.get("profile_results") or {}).keys()),
        "handoff_monitor": exec_result.get("handoff_monitor"),
        "report_path": exec_result.get("report_path"),
    }

    final_handoff = verify_no_new_run_handoffs(
        client,
        baseline=baseline,
        run_id=RUN_ID,
        strict_any_new_row=True,
    )
    closeout["phases"]["handoff_final"] = final_handoff.to_dict()
    if not final_handoff.ok:
        closeout["verdict"] = "BLOCKED"
        closeout["block_reason"] = "email_handoff_leak"
        CLOSEOUT_PATH.write_text(json.dumps(closeout, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(closeout, indent=2))
        return 3

    # Phase 4 — restore Production formulas
    restore = restore_production_formulas(
        client,
        allow_writes=True,
        confirm=CONFIRM_TOKEN,
        snapshot_bundle=bundle,
        reason="campaign_stage_z_closeout",
    )
    closeout["phases"]["formula_restore"] = restore
    meta_after = client.meta_tables()
    post_verify = verify_formula_state(
        meta_after,
        expect_production_normal=True,
        expect_gated=False,
    )
    closeout["phases"]["formula_post_verify"] = post_verify.to_dict()
    if post_verify.gated_detected:
        closeout["verdict"] = "BLOCKED"
        closeout["block_reason"] = "formula_restore_incomplete"
    elif exec_result.get("errors"):
        closeout["verdict"] = "COMPLETE WITH DOCUMENTED FINDINGS"
    else:
        closeout["verdict"] = "COMPLETE"

    CLOSEOUT_PATH.write_text(json.dumps(closeout, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(closeout, indent=2))
    return 0 if closeout["verdict"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Post-cleanup verification for Perfect run 202231Z."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token
from season_simulation.clock_override import formula_text_has_season_sim_gate
from season_simulation.production_normal_formulas import (
    formula_sha256,
    load_production_normal_bundle,
)
from season_simulation.simulation_process_lock import default_lock_path, read_lock

RUN = "SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt"
ENR = "recrQNLC7wX3oqbmm"
ATHLETE = "recmTBFNWWGtCTsCx"
SC = "appn84sqPw03zEbTT"
CURR = "appnrW8pPpzq8Nhov"
COMMS = "appYG1t5DBRimHBCT"
CATALOG_ZOOM = {"recMFP2x5LDqea9ax", "recb9EjQIJVzaRpZa"}
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "audits" / "readiness-20260914"
REGISTRY_DIR = REPO / "tools" / "season_simulation" / "run_registries"


def main() -> int:
    sc = AirtableClient(token=load_token(), base_id=SC, allow_writes=False)
    curr = AirtableClient(token=load_token(), base_id=CURR, allow_writes=False)
    comms = AirtableClient(token=load_token(), base_id=COMMS, allow_writes=False)

    def counts(client, tables):
        out = {}
        for t in tables:
            try:
                out[t] = len(client.list_records(t))
            except Exception as exc:  # noqa: BLE001
                out[t] = f"ERR:{exc}"
        return out

    sc_counts = counts(
        sc,
        [
            "Athletes",
            "Enrollments",
            "Submissions",
            "Submission Assets",
            "Homework Completions",
            "Video Feedback",
            "XP Events",
            "Athlete Achievement Unlocks",
            "Streak Occurrences",
            "Weekly Athlete Summary",
            "Zoom Attendance",
            "Email Handoff Queue",
        ],
    )
    curr_counts = counts(
        curr,
        ["Submission Outbox", "Homework Draft Responses", "Homework Draft Attempts"],
    )
    comms_counts = counts(
        comms,
        [
            "Delivery Attempts",
            "Audit Events",
            "Deliveries",
            "Delivery Keys",
            "Messages",
            "Integration Events",
            "Contact Methods",
            "Communication Identities",
        ],
    )

    zoom_ids = [r["id"] for r in sc.list_records("Zoom Meetings")]
    pha = [
        r
        for r in sc.list_records("Program Homework Assignments")
        if (r.get("fields") or {}).get("Active?") is True
    ]
    week9 = 0
    for r in pha:
        blob = json.dumps(r.get("fields") or {}, default=str).lower()
        if "week 9" in blob or "week9" in blob:
            week9 += 1

    # residual probes
    residuals = {}
    for table, formula in (
        ("XP Events", f"FIND('{ENR}', {{Source Key}} & '')"),
        ("Email Handoff Queue", f"{{Enrollment Record ID}}='{ENR}'"),
        ("Submissions", f"FIND('{RUN}', {{Video Upload Note}} & '')"),
    ):
        try:
            residuals[table] = len(sc.list_records(table, formula=formula))
        except Exception as exc:  # noqa: BLE001
            residuals[table] = f"ERR:{exc}"
    for table, rid in (("Enrollments", ENR), ("Athletes", ATHLETE)):
        try:
            sc.get_record(table, rid)
            residuals[f"{table}_exists"] = True
        except Exception:
            residuals[f"{table}_exists"] = False

    bundle = load_production_normal_bundle()
    meta = sc.meta_tables()
    subs = next(t for t in meta if t.get("name") == "Submissions")
    by = {f.get("name"): f for f in (subs.get("fields") or [])}
    formulas = {}
    for bf in bundle.fields:
        text = (by[bf.field_name].get("options") or {}).get("formula") or ""
        formulas[bf.field_name] = {
            "matches_bundle": formula_sha256(text) == bf.sha256,
            "has_season_sim_text": "SEASON-SIM" in text,
            "gated": formula_text_has_season_sim_gate(text),
            "sha256": formula_sha256(text),
        }

    lock = read_lock(default_lock_path(REGISTRY_DIR))

    ok = (
        all(v == 0 for v in sc_counts.values())
        and all(v == 0 for v in curr_counts.values())
        and all(v == 0 for v in comms_counts.values())
        and set(zoom_ids) == CATALOG_ZOOM
        and len(pha) == 20
        and week9 >= 2
        and all(v is False or v == 0 for k, v in residuals.items())
        and all(f["matches_bundle"] and not f["has_season_sim_text"] for f in formulas.values())
        and lock is None
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": RUN,
        "verdict": (
            "SIMULATION CLOSED — READY FOR REAL-SEASON OPERATION"
            if ok
            else "CLOSEOUT INCOMPLETE"
        ),
        "ok": ok,
        "sc_transactional_counts": sc_counts,
        "curriculum_transactional_counts": curr_counts,
        "comms_transactional_counts": comms_counts,
        "zoom_meeting_ids": zoom_ids,
        "zoom_catalog_only": set(zoom_ids) == CATALOG_ZOOM,
        "active_pha_count": len(pha),
        "week9_pha_hits": week9,
        "residuals": residuals,
        "formulas": formulas,
        "simulation_lock": None if lock is None else lock.__dict__,
        "no_new_ehq": sc_counts.get("Email Handoff Queue") == 0,
        "no_new_hub_deliveries": all(
            comms_counts.get(t) == 0
            for t in ("Deliveries", "Delivery Attempts", "Messages")
        ),
    }
    path = OUT / f"cleanup-verify-{RUN}.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    print("Wrote", path)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

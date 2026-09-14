"""Execute exact-ID cleanup for Perfect run 183404Z from validated manifest.

Requires ownership_pass=true. Deletes only manifest IDs. Preserves catalog Zoom.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token
from season_simulation.clock_override import formula_text_has_season_sim_gate
from season_simulation.constants import (
    CONFIRM_CLEANUP_TOKEN,
    CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN,
    CONFIRM_TOKEN,
)
from season_simulation.confirmation import (
    require_cleanup_gates,
    require_incomplete_cleanup_force,
)
from season_simulation.production_normal_formulas import (
    formula_sha256,
    load_production_normal_bundle,
)

RUN = "SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt"
SC_BASE = "appn84sqPw03zEbTT"
CURR_HUB = "appnrW8pPpzq8Nhov"
COMMS_HUB = "appYG1t5DBRimHBCT"
CATALOG_ZOOM = {"recMFP2x5LDqea9ax", "recb9EjQIJVzaRpZa"}
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "audits" / "readiness-20260914"
MANIFEST = OUT / f"cleanup-manifest-{RUN}.json"
OWNERSHIP = OUT / f"cleanup-ownership-{RUN}.json"


def resolve_client_table(key: str) -> tuple[str, str]:
    if key.startswith("Hub::"):
        return CURR_HUB, key.split("::", 1)[1]
    if key.startswith("Comms::"):
        return COMMS_HUB, key.split("::", 1)[1]
    return SC_BASE, key


def main() -> int:
    if "--execute" not in sys.argv:
        print("Dry-run only. Pass --execute to delete.", file=sys.stderr)
        execute = False
    else:
        execute = True

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    own = json.loads(OWNERSHIP.read_text(encoding="utf-8"))
    if not man.get("ownership_pass") or not own.get("pass"):
        print("Ownership validation failed — refusing cleanup", file=sys.stderr)
        return 2
    if man.get("blockers") or own.get("unsafe_recipients"):
        print("Blockers/unsafe recipients present — refusing", file=sys.stderr)
        return 2

    if execute:
        require_cleanup_gates(
            execute=True,
            confirm=CONFIRM_TOKEN,
            confirm_cleanup=CONFIRM_CLEANUP_TOKEN,
            simulation_id=RUN,
            action="exact-ID cleanup of failed Perfect run 183404Z",
        )
        require_incomplete_cleanup_force(
            registry_status="paused",
            confirm_force_incomplete=CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN,
            action="exact-ID cleanup of failed Perfect run 183404Z",
        )

    clients = {
        SC_BASE: AirtableClient(
            token=load_token(), base_id=SC_BASE, allow_writes=execute
        ),
        CURR_HUB: AirtableClient(
            token=load_token(), base_id=CURR_HUB, allow_writes=execute
        ),
        COMMS_HUB: AirtableClient(
            token=load_token(), base_id=COMMS_HUB, allow_writes=execute
        ),
    }

    deleted: dict[str, list[str]] = {}
    errors: list[str] = []
    skipped: list[dict] = []

    order = man.get("delete_order") or []
    # Append any manifest tables not in order
    for table in man.get("manifest_ids") or {}:
        if table not in order:
            order.append(table)

    for key in order:
        ids = list(man.get("manifest_ids", {}).get(key) or [])
        if not ids:
            continue
        base_id, table = resolve_client_table(key)
        # Never delete catalog zoom
        if table == "Zoom Meetings":
            keep = [i for i in ids if i in CATALOG_ZOOM]
            ids = [i for i in ids if i not in CATALOG_ZOOM]
            for kid in keep:
                skipped.append(
                    {
                        "table": key,
                        "id": kid,
                        "reason": "catalog_zoom_preserved",
                    }
                )
        if not ids:
            continue
        client = clients[base_id]
        if not execute:
            deleted[key] = ids
            continue
        try:
            client.delete_records(table, ids)
            deleted[key] = ids
            print(f"Deleted {len(ids)} from {base_id}/{table}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{key}: {exc}")
            print(f"ERROR {key}: {exc}", file=sys.stderr)

    # Zero-state verification (read-only)
    sc = AirtableClient(token=load_token(), base_id=SC_BASE, allow_writes=False)
    curr = AirtableClient(token=load_token(), base_id=CURR_HUB, allow_writes=False)
    comms = AirtableClient(token=load_token(), base_id=COMMS_HUB, allow_writes=False)

    def count_all(client: AirtableClient, table: str) -> int:
        try:
            return len(client.list_records(table, max_records=100))
        except Exception as exc:  # noqa: BLE001
            return -1

    sc_zero = {
        t: count_all(sc, t)
        for t in (
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
        )
    }
    zoom_rows = sc.list_records("Zoom Meetings")
    zoom_ids = [r["id"] for r in zoom_rows]
    zoom_ok = set(zoom_ids) == CATALOG_ZOOM or set(zoom_ids).issubset(CATALOG_ZOOM) and len(zoom_ids) == 2

    pha = sc.list_records(
        "Program Homework Assignments",
        formula="{Active?} = TRUE()",
    )
    # fallback without formula
    if not pha:
        try:
            all_pha = sc.list_records("Program Homework Assignments")
            pha = [
                r
                for r in all_pha
                if (r.get("fields") or {}).get("Active?") is True
                or (r.get("fields") or {}).get("Active") is True
            ]
        except Exception:
            pha = []

    curr_zero = {
        t: count_all(curr, t)
        for t in ("Submission Outbox", "Homework Draft Responses", "Homework Draft Attempts")
    }
    comms_zero = {
        t: count_all(comms, t)
        for t in (
            "Delivery Attempts",
            "Audit Events",
            "Deliveries",
            "Delivery Keys",
            "Messages",
            "Integration Events",
        )
    }

    # Formulas
    bundle = load_production_normal_bundle()
    season_sim_hits = []
    hash_check = {}
    meta = sc.meta_tables()
    by_name = {}
    for table in meta:
        if table.get("name") != "Submissions":
            continue
        for field in table.get("fields") or []:
            by_name[field.get("name")] = (field.get("options") or {}).get("formula") or ""
    for fld in bundle.fields:
        live = by_name.get(fld.field_name) or ""
        live_hash = formula_sha256(live) if live else ""
        hash_check[fld.field_name] = {
            "expected": fld.sha256,
            "live": live_hash,
            "match": live_hash == fld.sha256,
            "season_sim": formula_text_has_season_sim_gate(live) or "SEASON-SIM" in live,
        }
        if hash_check[fld.field_name]["season_sim"]:
            season_sim_hits.append(fld.field_name)

    # Simulation lock
    lock_path = (
        REPO
        / "tools"
        / "season_simulation"
        / "run_registries"
        / ".simulation_process.lock"
    )
    lock_active = lock_path.is_file()

    zero_ok = (
        all(v == 0 for v in sc_zero.values())
        and all(v == 0 for v in curr_zero.values())
        and all(v == 0 for v in comms_zero.values())
        and zoom_ok
        and len(pha) == 20
        and not season_sim_hits
        and all(v["match"] for v in hash_check.values())
        and not lock_active
        and not errors
    )

    report = {
        "run": RUN,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "execute": execute,
        "deleted_counts": {k: len(v) for k, v in deleted.items()},
        "deleted_total": sum(len(v) for v in deleted.values()),
        "deleted_ids": deleted if execute else {k: v for k, v in deleted.items()},
        "skipped": skipped,
        "errors": errors,
        "zero_state": {
            "sc": sc_zero,
            "curriculum_hub": curr_zero,
            "comms_hub": comms_zero,
            "zoom_meetings_remaining": zoom_ids,
            "zoom_catalog_only": zoom_ok,
            "active_pha_count": len(pha),
            "formula_hash_check": hash_check,
            "season_sim_hits": season_sim_hits,
            "simulation_lock_active": lock_active,
        },
        "ready_for_new_perfect_simulation": bool(zero_ok and execute),
    }
    out_path = OUT / (
        f"cleanup-execution-{RUN}.json"
        if execute
        else f"cleanup-dry-run-{RUN}.json"
    )
    out_path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "path": str(out_path),
        "execute": execute,
        "deleted_total": report["deleted_total"],
        "errors": errors,
        "zero_ok": zero_ok,
        "ready": report["ready_for_new_perfect_simulation"],
        "sc_zero": sc_zero,
        "zoom": zoom_ids,
        "pha": len(pha),
        "hashes_ok": all(v["match"] for v in hash_check.values()),
    }, indent=2))
    return 0 if not errors and (not execute or zero_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

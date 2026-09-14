"""Execute exact-ID cleanup for Perfect run 202231Z from validated manifest."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token
from season_simulation.clock_override import formula_text_has_season_sim_gate
from season_simulation.constants import CONFIRM_CLEANUP_TOKEN, CONFIRM_TOKEN
from season_simulation.confirmation import require_cleanup_gates
from season_simulation.production_normal_formulas import (
    formula_sha256,
    load_production_normal_bundle,
)
from season_simulation.simulation_process_lock import (
    default_lock_path,
    read_lock,
    release_simulation_lock,
)

RUN = "SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt"
SC_BASE = "appn84sqPw03zEbTT"
CURR_HUB = "appnrW8pPpzq8Nhov"
COMMS_HUB = "appYG1t5DBRimHBCT"
CATALOG_ZOOM = {"recMFP2x5LDqea9ax", "recb9EjQIJVzaRpZa"}
ALLOW = "schmidt@fairfieldbasketballclub.com"
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs" / "audits" / "readiness-20260914"
MANIFEST = OUT / f"cleanup-manifest-{RUN}.json"
OWNERSHIP = OUT / f"cleanup-ownership-{RUN}.json"
REGISTRY_DIR = REPO / "tools" / "season_simulation" / "run_registries"


def resolve_client_table(key: str) -> tuple[str, str]:
    if key.startswith("Hub::"):
        return CURR_HUB, key.split("::", 1)[1]
    if key.startswith("Comms::"):
        return COMMS_HUB, key.split("::", 1)[1]
    return SC_BASE, key


def main() -> int:
    execute = "--execute" in sys.argv
    if not execute:
        print("Dry-run only. Pass --execute to delete.")

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
            action="exact-ID cleanup of passed Perfect run 202231Z",
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
    pre_counts = {
        "ehq": len(clients[SC_BASE].list_records("Email Handoff Queue")),
    }

    order = list(man.get("delete_order") or [])
    for table in man.get("manifest_ids") or {}:
        if table not in order:
            order.append(table)

    for key in order:
        ids = list(man.get("manifest_ids", {}).get(key) or [])
        if not ids:
            continue
        base_id, table = resolve_client_table(key)
        if table == "Zoom Meetings":
            keep = [i for i in ids if i in CATALOG_ZOOM]
            ids = [i for i in ids if i not in CATALOG_ZOOM]
            for kid in keep:
                skipped.append(
                    {"table": key, "id": kid, "reason": "catalog_zoom_preserved"}
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

    # Release any leftover simulation lock for this run
    lock = read_lock(default_lock_path(REGISTRY_DIR))
    lock_released = False
    if lock and RUN in str(lock.run_id):
        if execute:
            release_simulation_lock(registry_dir=REGISTRY_DIR, run_id=lock.run_id)
            lock_released = True

    sc = AirtableClient(token=load_token(), base_id=SC_BASE, allow_writes=False)
    curr = AirtableClient(token=load_token(), base_id=CURR_HUB, allow_writes=False)
    comms = AirtableClient(token=load_token(), base_id=COMMS_HUB, allow_writes=False)

    def count_all(client: AirtableClient, table: str) -> int:
        try:
            return len(client.list_records(table))
        except Exception:
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
    zoom_ids = [r["id"] for r in sc.list_records("Zoom Meetings")]
    zoom_ok = set(zoom_ids) == CATALOG_ZOOM

    all_pha = sc.list_records("Program Homework Assignments")
    pha_active = [
        r
        for r in all_pha
        if (r.get("fields") or {}).get("Active?") is True
        or (r.get("fields") or {}).get("Active") is True
    ]
    week9 = [
        r
        for r in pha_active
        if "week 9" in str((r.get("fields") or {}).get("Name") or (r.get("fields") or {}).get("Display") or "").lower()
        or "week 9" in json.dumps(r.get("fields") or {}).lower()
    ]

    # residual run marker / enrollment
    residual = {}
    for table in ("Submissions", "XP Events", "Email Handoff Queue", "Athletes", "Enrollments"):
        try:
            by_run = sc.list_records(table, formula=f"FIND('{RUN}', {{Notes}} & '' & {{Video Upload Note}} & '' & {{Source Key}} & '' & {{Handoff Key}} & '')")
        except Exception:
            by_run = []
        try:
            by_enr = sc.list_records(
                table, formula=f"FIND('recrQNLC7wX3oqbmm', {{Enrollment Record ID}} & '' & {{Source Key}} & '')"
            ) if table not in ("Athletes", "Enrollments") else []
        except Exception:
            by_enr = []
        residual[table] = {
            "by_run_marker": len(by_run),
            "by_enrollment": len(by_enr),
        }
    # Direct ID checks
    for table, rid in (("Enrollments", "recrQNLC7wX3oqbmm"), ("Athletes", "recmTBFNWWGtCTsCx")):
        try:
            sc.get_record(table, rid)
            residual[table]["record_still_exists"] = True
        except Exception:
            residual[table]["record_still_exists"] = False

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
            "Contact Methods",
            "Communication Identities",
        )
    }

    bundle = load_production_normal_bundle()
    season_sim_hits = []
    hash_check = {}
    meta = sc.meta_tables()
    subs = next(t for t in meta if t.get("name") == "Submissions")
    by_name = {f.get("name"): f for f in (subs.get("fields") or [])}
    for bf in bundle.fields:
        text = (by_name[bf.field_name].get("options") or {}).get("formula") or ""
        hash_check[bf.field_name] = {
            "sha256": formula_sha256(text),
            "matches_bundle": formula_sha256(text) == bf.sha256,
            "gated": formula_text_has_season_sim_gate(text),
            "has_season_sim_text": "SEASON-SIM" in text,
        }
        if "SEASON-SIM" in text or formula_text_has_season_sim_gate(text):
            season_sim_hits.append(bf.field_name)

    post_ehq = sc_zero.get("Email Handoff Queue", -1)
    verify = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": RUN,
        "execute": execute,
        "deleted_counts": {k: len(v) for k, v in deleted.items()},
        "deleted_total": sum(len(v) for v in deleted.values()),
        "errors": errors,
        "skipped": skipped,
        "sc_transactional_counts": sc_zero,
        "curriculum_transactional_counts": curr_zero,
        "comms_transactional_counts": comms_zero,
        "zoom_meeting_ids": zoom_ids,
        "zoom_catalog_only": zoom_ok,
        "active_pha_count": len(pha_active),
        "week9_pha_count": len(week9),
        "residuals": residual,
        "formula_hash_check": hash_check,
        "season_sim_formula_hits": season_sim_hits,
        "lock_released": lock_released,
        "lock_after": None if read_lock(default_lock_path(REGISTRY_DIR)) is None else read_lock(default_lock_path(REGISTRY_DIR)).__dict__,
        "ehq_pre_cleanup": pre_counts["ehq"],
        "ehq_post_cleanup": post_ehq,
        "no_new_ehq_during_cleanup": post_ehq <= 0 if execute else None,
        "allowlist_email": ALLOW,
    }
    path = OUT / (
        f"cleanup-{'execution' if execute else 'dry-run'}-{RUN}.json"
    )
    path.write_text(json.dumps(verify, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: verify[k] for k in (
        "execute", "deleted_total", "deleted_counts", "errors",
        "sc_transactional_counts", "zoom_catalog_only", "active_pha_count",
        "season_sim_formula_hits",
    )}, indent=2))
    print("Wrote", path)
    if errors:
        return 3
    if execute:
        bad = any(v not in (0, -1) for v in sc_zero.values()) or not zoom_ok or season_sim_hits
        return 0 if not bad else 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

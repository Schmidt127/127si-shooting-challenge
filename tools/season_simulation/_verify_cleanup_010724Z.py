#!/usr/bin/env python3
"""Post-cleanup read-only verification for 010724Z."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from season_simulation.airtable_client import AirtableClient

RUN_ID = "SEASON-SIM-2027-20260913T010724Z-threeathlete"
MARKER = "010724Z"
MANIFEST = Path(__file__).parent / "reports/cleanup-manifest-010724Z-final.json"
REPORT = Path(__file__).parent / "reports/cleanup-verify-010724Z-final.json"

SIM_ENROLL = ["recFcH7qLPzzso9s3", "recyH8DPUKi07rkcg", "reclW1BQ9UDd6yl0z"]
SIM_ATH = ["rec5QYk66wEXMdCNG", "recwpqRpE98yQqrbn", "recj0wgEZhyQcCy28"]
OTHER_ENROLL = "recNJaTAevEGQrbg9"
CANONICAL_ZOOM = ["recMFP2x5LDqea9ax", "recb9EjQIJVzaRpZa"]
FORMULA_FIELD_IDS = ["fldyFAjhbfaC4LlPb", "fldE7G8H1O7HPYuIi", "fldLo2GO5aac6tPX1"]
EXEC_REPORT = Path(__file__).parent / "reports/cleanup-execute-010724Z-final.json"


def main() -> int:
    client = AirtableClient(allow_writes=False)
    manifest = json.loads(MANIFEST.read_text())
    ids_by_table = manifest.get("manifest_ids") or {}

    still_present: dict[str, list[str]] = {}
    for table, ids in ids_by_table.items():
        gone = []
        for rid in ids:
            try:
                client.get_record(table, rid)
                gone.append(rid)
            except Exception as exc:  # noqa: BLE001
                if "404" not in str(exc) and "NOT_FOUND" not in str(exc).upper():
                    gone.append(rid)
        if gone:
            still_present[table] = gone

    sim_gone = {"enrollments": [], "athletes": []}
    for eid in SIM_ENROLL:
        try:
            client.get_record("Enrollments", eid)
            sim_gone["enrollments"].append(eid)
        except Exception:
            pass
    for aid in SIM_ATH:
        try:
            client.get_record("Athletes", aid)
            sim_gone["athletes"].append(aid)
        except Exception:
            pass

    marker_hits: dict[str, int] = {}
    for table, formula in [
        ("Submissions", f"FIND('{MARKER}', {{Notes}} & '')"),
        ("XP Events", f"FIND('{MARKER}', {{XP Reason Debug}} & '')"),
    ]:
        try:
            rows = client.list_records(table, formula=formula, max_records=5)
            marker_hits[table] = len(rows)
        except Exception:
            marker_hits[table] = -1

    other_preserved = {}
    try:
        client.get_record("Enrollments", OTHER_ENROLL)
        other_preserved["114448Z_enrollment"] = "present"
    except Exception:
        other_preserved["114448Z_enrollment"] = "missing"

    ehq_114448 = client.list_records(
        "Email Handoff Queue",
        formula=f"FIND('{OTHER_ENROLL}', {{Enrollment Record ID}} & '')",
        max_records=25,
    )
    other_preserved["114448Z_ehq_sample_count"] = len(ehq_114448)

    zoom_ok = {}
    for zid in CANONICAL_ZOOM:
        try:
            client.get_record("Zoom Meetings", zid)
            zoom_ok[zid] = "present"
        except Exception:
            zoom_ok[zid] = "missing"

    meta = client.meta_tables()
    formulas = {}
    for t in meta:
        if t["name"] != "Submissions":
            continue
        for f in t.get("fields", []):
            if f.get("id") in FORMULA_FIELD_IDS:
                text = (f.get("options") or {}).get("formula") or ""
                formulas[f["name"]] = {
                    "has_season_sim": "SEASON-SIM" in text or "SEASON-SIM|" in text,
                    "formula_preview": text[:120],
                }

    cleanup_start = "2026-09-13T18:00:00.000Z"
    if EXEC_REPORT.exists():
        cleanup_start = json.loads(EXEC_REPORT.read_text()).get("started_at") or cleanup_start
    ehq_during = client.list_records(
        "Email Handoff Queue",
        formula=f"IS_AFTER({{Created}}, '{cleanup_start}')",
        max_records=10,
    )
    ehq_sim_during = [
        r for r in ehq_during
        if (r.get("fields") or {}).get("Enrollment Record ID") in SIM_ENROLL
    ]

    result = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "manifest_still_present": still_present,
        "sim_enrollment_still_present": sim_gone["enrollments"],
        "sim_athlete_still_present": sim_gone["athletes"],
        "marker_hits_remaining": marker_hits,
        "114448Z_and_production_preserved": other_preserved,
        "canonical_zoom": zoom_ok,
        "submission_formulas": formulas,
        "ehq_created_during_cleanup": len(ehq_during),
        "ehq_sim_created_during_cleanup": len(ehq_sim_during),
        "cleanup_window_start": cleanup_start,
        "pass": (
            not still_present
            and not sim_gone["enrollments"]
            and not sim_gone["athletes"]
            and all(v == 0 for v in marker_hits.values() if v >= 0)
            and other_preserved.get("114448Z_enrollment") == "present"
            and all(v == "present" for v in zoom_ok.values())
            and all(not v.get("has_season_sim") for v in formulas.values())
            and len(ehq_sim_during) == 0
        ),
    }
    REPORT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

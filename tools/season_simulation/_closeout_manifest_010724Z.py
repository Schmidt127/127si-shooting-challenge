#!/usr/bin/env python3
"""Rebuild and integrity-gate cleanup manifest for 010724Z three-athlete run."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from season_simulation.airtable_client import AirtableClient

RUN_ID = "SEASON-SIM-2027-20260913T010724Z-threeathlete"
MARKER = "010724Z"
OTHER_RUN = "114448Z"
RUN_START = "2026-09-13T01:07:24.000Z"

ENROLLMENTS = {
    "A1_perfect": "recFcH7qLPzzso9s3",
    "A2_recovery": "recyH8DPUKi07rkcg",
    "A3_edge": "reclW1BQ9UDd6yl0z",
}
ATHLETES = {
    "A1_perfect": "rec5QYk66wEXMdCNG",
    "A2_recovery": "recwpqRpE98yQqrbn",
    "A3_edge": "recj0wgEZhyQcCy28",
}
SIM_ENROLL = set(ENROLLMENTS.values())
SIM_ATH = set(ATHLETES.values())
OTHER_RUN_ENROLLMENT = "recNJaTAevEGQrbg9"  # 114448Z — must never appear
CANONICAL_ZOOM = frozenset({"recMFP2x5LDqea9ax", "recb9EjQIJVzaRpZa"})

DELETE_ORDER = [
    "Email Handoff Queue",
    "XP Events",
    "Athlete Achievement Unlocks",
    "Streak Occurrences",
    "Video Feedback",
    "Homework Completions",
    "Submission Assets",
    "Zoom Attendance",
    "Zoom Meetings",
    "Weekly Athlete Summary",
    "Submissions",
    "Enrollments",
    "Athletes",
]

ENROLLMENT_LINK_FIELDS = {
    "Submissions": "Submissions",
    "Homework Completions": "Homework Completions",
    "Video Feedback": "Video Feedback",
    "Weekly Athlete Summary": "Weekly Athlete Summary",
    "Zoom Attendance": "Zoom Attendance",
    "XP Events": "XP Events",
    "Streak Occurrences": "Streak Occurrences",
    "Athlete Achievement Unlocks": "Athlete Achievement Unlocks",
}


def list_all(client: AirtableClient, table: str, *, fields=None, formula=None) -> list[dict]:
    return client.list_records(table, fields=fields, formula=formula, page_size=100)


def main() -> int:
    client = AirtableClient(allow_writes=False)
    manifest: dict[str, list[str]] = {t: [] for t in DELETE_ORDER}
    provenance: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    warnings: list[str] = []

    # --- Primary ownership: enrollment reverse links ---
    for label, eid in ENROLLMENTS.items():
        try:
            rec = client.get_record("Enrollments", eid)
        except Exception as exc:
            errors.append(f"Enrollment missing {eid} ({label}): {exc}")
            continue
        fields = rec.get("fields") or {}
        for table, link_field in ENROLLMENT_LINK_FIELDS.items():
            for rid in fields.get(link_field) or []:
                if rid and rid not in manifest[table]:
                    manifest[table].append(rid)
                    provenance[f"{table}:{rid}"] = f"enrollment_link:{label}:{eid}"

        # Submission Assets via submissions
        for sid in fields.get("Submissions") or []:
            try:
                sub = client.get_record("Submissions", sid)
                for aid in (sub.get("fields") or {}).get("Submission Assets") or []:
                    if aid and aid not in manifest["Submission Assets"]:
                        manifest["Submission Assets"].append(aid)
                        provenance[f"Submission Assets:{aid}"] = f"submission_asset:{label}:{sid}"
            except Exception as exc:
                warnings.append(f"Submission read {sid}: {exc}")

    manifest["Athletes"] = list(ATHLETES.values())
    manifest["Enrollments"] = list(ENROLLMENTS.values())
    for rid in manifest["Athletes"]:
        provenance[f"Athletes:{rid}"] = "fixed_sim_athlete"
    for rid in manifest["Enrollments"]:
        provenance[f"Enrollments:{rid}"] = "fixed_sim_enrollment"

    # --- EHQ: 010724Z only (A1 enrollment, not 114448Z) ---
    ehq_fields = [
        "Handoff Key", "Status", "Enrollment Record ID", "Payload JSON",
        "Hub Event ID", "Send to Hub?",
    ]
    ehq_post = list_all(
        client,
        "Email Handoff Queue",
        fields=ehq_fields,
        formula=f"IS_AFTER({{Created}}, '{RUN_START}')",
    )
    sub_cache: dict[str, str | None] = {}

    def trace_enrollment(hk: str | None) -> str | None:
        m = re.search(
            r"\|(SUBMISSIONS|HOMEWORK_COMPLETIONS|WEEKLY_ATHLETE_SUMMARY)\|(rec[a-zA-Z0-9]+)",
            hk or "",
        )
        if not m:
            return None
        rid = m.group(2)
        if rid not in sub_cache:
            tbl_map = {
                "SUBMISSIONS": "Submissions",
                "HOMEWORK_COMPLETIONS": "Homework Completions",
                "WEEKLY_ATHLETE_SUMMARY": "Weekly Athlete Summary",
            }
            try:
                r = client.get_record(tbl_map[m.group(1)], rid)
                f = r.get("fields") or {}
                e = f.get("Enrollment Record ID Lookup") or f.get("Enrollment Record ID") or f.get("Enrollment")
                sub_cache[rid] = e[0] if isinstance(e, list) and e else (e if isinstance(e, str) else None)
            except Exception:
                sub_cache[rid] = None
        return sub_cache[rid]

    ehq_010724: list[str] = []
    ehq_114448: list[str] = []
    for rec in ehq_post:
        rid = rec["id"]
        f = rec.get("fields") or {}
        blob = json.dumps(f)
        hk = f.get("Handoff Key") or ""
        enr = (f.get("Enrollment Record ID") or "").strip() or (trace_enrollment(hk) or "")
        if OTHER_RUN in blob or "20260913T114448Z" in blob or enr == OTHER_RUN_ENROLLMENT:
            ehq_114448.append(rid)
            continue
        if enr in SIM_ENROLL or MARKER in blob or RUN_ID in blob:
            if rid not in ehq_010724:
                ehq_010724.append(rid)
                provenance[f"Email Handoff Queue:{rid}"] = f"ehq_010724Z:enr={enr}"

    manifest["Email Handoff Queue"] = ehq_010724

    # --- Zoom Meetings: disposable only if linked from sim attendance and not canonical ---
    zoom_meeting_ids: set[str] = set()
    for zid in manifest["Zoom Attendance"]:
        try:
            za = client.get_record("Zoom Attendance", zid)
            for mid in (za.get("fields") or {}).get("Zoom Meeting") or []:
                if mid and mid not in CANONICAL_ZOOM:
                    zoom_meeting_ids.add(mid)
        except Exception as exc:
            warnings.append(f"Zoom Attendance {zid}: {exc}")
    manifest["Zoom Meetings"] = sorted(zoom_meeting_ids)
    for mid in manifest["Zoom Meetings"]:
        provenance[f"Zoom Meetings:{mid}"] = "sim_attendance_linked_non_canonical"

    # --- Dedupe within tables ---
    dup_within: list[str] = []
    for table, ids in manifest.items():
        seen: list[str] = []
        for rid in ids:
            if rid in seen:
                dup_within.append(f"{table}:{rid}")
            else:
                seen.append(rid)
        manifest[table] = seen

    # --- Cross-table duplicate IDs (same rec ID in multiple tables is OK for different tables) ---
    all_ids_flat: list[str] = []
    cross_dup: list[str] = []
    for table in DELETE_ORDER:
        for rid in manifest.get(table, []):
            key = rid
            if key in all_ids_flat:
                cross_dup.append(key)
            all_ids_flat.append(key)

    # --- Integrity: prove ownership of every ID ---
    unowned: list[str] = []
    excluded_run: list[str] = []
    for table in DELETE_ORDER:
        for rid in manifest.get(table, []):
            if table in ("Athletes", "Enrollments"):
                if table == "Athletes" and rid not in SIM_ATH:
                    unowned.append(f"{table}:{rid}")
                if table == "Enrollments" and rid not in SIM_ENROLL:
                    unowned.append(f"{table}:{rid}")
                continue
            if table == "Email Handoff Queue":
                if rid in ehq_114448:
                    excluded_run.append(f"{table}:{rid}")
                continue
            if table == "Zoom Meetings":
                if rid in CANONICAL_ZOOM:
                    excluded_run.append(f"{table}:{rid}")
                continue
            # Live read verify enrollment ownership for transactional rows
            try:
                rec = client.get_record(table, rid)
                f = rec.get("fields") or {}
                owned = False
                if table == "Submissions":
                    lk = f.get("Enrollment Record ID Lookup") or f.get("Enrollment")
                    eids = lk if isinstance(lk, list) else ([lk] if lk else [])
                    owned = any(e in SIM_ENROLL for e in eids)
                elif table == "Submission Assets":
                    owned = f"Submission Assets:{rid}" in provenance
                elif table in ENROLLMENT_LINK_FIELDS:
                    lk = f.get("Enrollment") or f.get("Enrollment Record ID")
                    if isinstance(lk, list):
                        owned = any(x in SIM_ENROLL for x in lk)
                    elif isinstance(lk, str):
                        owned = lk in SIM_ENROLL
                    else:
                        owned = f"{table}:{rid}" in provenance
                else:
                    owned = f"{table}:{rid}" in provenance
                if not owned:
                    unowned.append(f"{table}:{rid}")
            except Exception as exc:
                if "NOT_FOUND" in str(exc).upper() or "404" in str(exc):
                    warnings.append(f"Already gone {table}:{rid}")
                else:
                    errors.append(f"Verify failed {table}:{rid}: {exc}")

    # --- Compare prior artifact ---
    prior_path = Path(__file__).parent / "reports/root-cause-campaign-010724Z.json"
    prior_ids: set[str] = set()
    prior_by_table: dict[str, set[str]] = {}
    if prior_path.exists():
        prior = json.loads(prior_path.read_text())
        prior_by_table = {k: set(v) for k, v in (prior.get("cleanup", {}).get("ids") or {}).items()}
        for ids in prior_by_table.values():
            prior_ids |= ids

    current_by_table = {k: set(v) for k, v in manifest.items() if v}
    current_ids: set[str] = set()
    for ids in current_by_table.values():
        current_ids |= ids

    omitted = sorted(prior_ids - current_ids)
    added = sorted(current_ids - prior_ids)

    counts = {t: len(manifest.get(t, [])) for t in DELETE_ORDER if manifest.get(t)}
    total = sum(counts.values())

    # Prior artifact table sum was 968; user mentioned 1018 display total
    prior_table_sum = sum(len(v) for v in prior_by_table.values())

    gate_pass = (
        not errors
        and not dup_within
        and not unowned
        and not excluded_run
        and total > 0
    )

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN_ID,
        "integrity_gate_pass": gate_pass,
        "total_unique_ids": total,
        "counts_by_table": counts,
        "prior_artifact_total": prior_table_sum,
        "prior_artifact_path": str(prior_path),
        "reconciliation": {
            "prior_total": prior_table_sum,
            "current_total": total,
            "delta": total - prior_table_sum,
            "omitted_from_prior": omitted,
            "added_vs_prior": added,
            "omitted_count": len(omitted),
            "added_count": len(added),
            "note_1018_vs_968": (
                "1018 may include cross-table sum with duplicates or EHQ/other_post_run; "
                "968 was prior cleanup.ids union; current uses deduped DELETE_ORDER tables only."
            ),
        },
        "errors": errors,
        "warnings": warnings,
        "dup_within_table": dup_within,
        "unowned": unowned,
        "excluded_run_hits": excluded_run,
        "ehq_114448_excluded_ids": ehq_114448,
        "manifest_ids": {t: manifest.get(t, []) for t in DELETE_ORDER if manifest.get(t)},
        "provenance_sample": dict(list(provenance.items())[:5]),
    }

    out_path = Path(__file__).parent / "reports/cleanup-manifest-010724Z-final.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({
        "gate_pass": gate_pass,
        "total": total,
        "counts": counts,
        "prior_total": prior_table_sum,
        "omitted": len(omitted),
        "added": len(added),
        "errors": errors,
        "unowned": unowned,
        "dup_within": dup_within,
        "ehq_114448_excluded": len(ehq_114448),
        "out_path": str(out_path),
    }, indent=2))
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

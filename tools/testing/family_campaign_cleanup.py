#!/usr/bin/env python3
"""Delete FAMTEST| and ATHWF| disposable records from family campaign."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from season_simulation.airtable_client import AirtableClient, fields_of

MANIFEST_PATHS = [
    Path(__file__).resolve().parents[2] / "docs/testing/evidence/family-campaign-2026-09-13/_manifest.json",
    Path(__file__).resolve().parents[2] / "docs/testing/athlete-workflow/fixtures/_sc-athlete-wf-last.json",
]

DELETE_ORDER = [
    "XP Events",
    "Homework Completions",
    "Video Feedback",
    "Submission Assets",
    "Submissions",
    "Weekly Athlete Summary",
    "Weeks",
]


def collect_ids(client: AirtableClient) -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {t: [] for t in DELETE_ORDER}

    for path in MANIFEST_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for key in ("created", "submissionIds", "weekId", "wasId", "videoId", "homeworkId", "incompleteHomeworkId"):
            val = data.get(key)
            if isinstance(val, str) and val.startswith("rec"):
                pass  # resolved below by table probe
            elif isinstance(val, list):
                for item in val:
                    rid = item if isinstance(item, str) else item.get("id")
                    if isinstance(rid, str) and rid.startswith("rec"):
                        ids["Submissions"].append(rid) if key == "submissionIds" else None

    # Prefix scan
    scans = [
        ("Submissions", "OR(FIND('ATHWF|', {Daily Email Subject} & ''), FIND('FAMTEST|', {Daily Email Subject} & ''))"),
        ("Weeks", "OR(FIND('ATHWF|', {Week Name} & ''), FIND('FAMTEST|', {Week Name} & ''))"),
        ("Homework Completions", "OR(FIND('ATHWF|', {Notes} & ''), FIND('FAMTEST|', {Notes} & ''))"),
        ("Video Feedback", "FIND('ATHWF|', {Video Feedback Key} & '')"),
        ("Weekly Athlete Summary", "FIND('FAMTEST|', {Notes} & '')"),
    ]
    for table, formula in scans:
        try:
            rows = client.list_records(table, formula=formula, max_records=100)
            for r in rows:
                if r["id"] not in ids[table]:
                    ids[table].append(r["id"])
        except Exception:
            pass

    # Manifest explicit ids
    for path in MANIFEST_PATHS:
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        if data.get("weekId"):
            ids["Weeks"].append(data["weekId"])
        if data.get("wasId") and "FAMTEST" in json.dumps(data):
            ids["Weekly Athlete Summary"].append(data["wasId"])
        for sub in data.get("submissionIds") or []:
            ids["Submissions"].append(sub)
        for rid in data.get("created") or []:
            if isinstance(rid, str):
                for table in DELETE_ORDER:
                    try:
                        client.get_record(table, rid)
                        if rid not in ids[table]:
                            ids[table].append(rid)
                        break
                    except Exception:
                        continue

    # Dedupe
    for table in ids:
        ids[table] = list(dict.fromkeys(ids[table]))
    return ids


def main() -> int:
    client = AirtableClient(allow_writes=True)
    ids = collect_ids(client)
    deleted: dict[str, list[str]] = {}
    failed: list[dict] = []

    for table in DELETE_ORDER:
        if not ids[table]:
            continue
        try:
            client.delete_records(table, ids[table])
            deleted[table] = ids[table]
        except Exception as exc:
            failed.append({"table": table, "ids": ids[table], "error": str(exc)[:300]})

    out = {"deleted": deleted, "failed": failed, "complete": not failed}
    print(json.dumps(out, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())

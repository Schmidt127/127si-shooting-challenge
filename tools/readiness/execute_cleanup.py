#!/usr/bin/env python3
"""Execute exact-ID cleanup from readiness manifest. Dependency-safe order."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "audits" / "readiness-20260914" / "cleanup-manifest.json"
OUT = ROOT / "docs" / "audits" / "readiness-20260914" / "cleanup-execution.json"

SC_BASE = "appn84sqPw03zEbTT"
HUB_BASE = "appnrW8pPpzq8Nhov"

ORDER = [
    ("Email Handoff Queue", SC_BASE),
    ("XP Events", SC_BASE),
    ("Athlete Achievement Unlocks", SC_BASE),
    ("Streak Occurrences", SC_BASE),
    ("Video Feedback", SC_BASE),
    ("Homework Completions", SC_BASE),
    ("Homework Responses", SC_BASE),
    ("Homework Attempts", SC_BASE),
    ("Submission Assets", SC_BASE),
    ("Zoom Attendance", SC_BASE),
    ("Zoom Meetings", SC_BASE),
    ("Weekly Athlete Summary", SC_BASE),
    ("Submissions", SC_BASE),
    ("Enrollments", SC_BASE),
    ("Athletes", SC_BASE),
    ("Hub::Submission Outbox", HUB_BASE),
    ("Hub::Homework Draft Responses", HUB_BASE),
    ("Hub::Homework Draft Attempts", HUB_BASE),
]


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def delete_batch(base: str, table: str, ids: list[str]) -> tuple[list[str], list[dict]]:
    deleted: list[str] = []
    errors: list[dict] = []
    # Hub:: prefix
    real_table = table.split("::", 1)[-1] if table.startswith("Hub::") else table
    enc = quote(real_table, safe="")
    headers = {"Authorization": f"Bearer {token()}"}
    for i in range(0, len(ids), 10):
        chunk = ids[i : i + 10]
        params = [("records[]", rid) for rid in chunk]
        url = f"https://api.airtable.com/v0/{base}/{enc}"
        for attempt in range(5):
            r = requests.delete(url, headers=headers, params=params, timeout=90)
            if r.status_code == 200:
                data = r.json()
                deleted.extend([x["id"] for x in data.get("records") or []])
                break
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            errors.append({"table": table, "ids": chunk, "status": r.status_code, "body": r.text[:400]})
            break
        time.sleep(0.22)
    return deleted, errors


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not m.get("execute_authorized"):
        raise SystemExit("Manifest not execute_authorized")
    ids_by = m["manifest_ids"]
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "deleted": {},
        "errors": [],
        "skipped_exceptions": m.get("exceptions") or [],
    }
    for table, base in ORDER:
        ids = ids_by.get(table) or []
        if not ids:
            continue
        print(f"Deleting {table}: {len(ids)}...", flush=True)
        deleted, errors = delete_batch(base, table, ids)
        report["deleted"][table] = deleted
        report["errors"].extend(errors)
        print(f"  deleted {len(deleted)} errors {len(errors)}", flush=True)
        if errors:
            # retry once individually
            for err in list(errors):
                for rid in err.get("ids") or []:
                    d2, e2 = delete_batch(base, table, [rid])
                    report["deleted"].setdefault(table, []).extend(d2)
                    report["errors"].extend(e2)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["deleted_counts"] = {k: len(v) for k, v in report["deleted"].items()}
    report["deleted_total"] = sum(report["deleted_counts"].values())
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"deleted_total": report["deleted_total"], "error_count": len(report["errors"])}, indent=2))
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

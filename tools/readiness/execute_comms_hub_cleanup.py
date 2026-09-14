#!/usr/bin/env python3
"""Execute Communications Hub exact-ID cleanup from readiness manifest.

Dependency-safe order. Does not touch Programs / Templates / Test Allowlist.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "audits" / "readiness-20260914" / "cleanup-manifest-comms-hub.json"
OUT = ROOT / "docs" / "audits" / "readiness-20260914" / "cleanup-execution-comms-hub.json"

COMMS_BASE = "appYG1t5DBRimHBCT"

ORDER = [
    "Delivery Attempts",
    "Audit Events",
    "Deliveries",
    "Delivery Keys",
    "Messages",
    "Integration Events",
    "Contact Methods",
    "Communication Identities",
]


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def delete_batch(table: str, ids: list[str]) -> tuple[list[str], list[dict]]:
    deleted: list[str] = []
    errors: list[dict] = []
    enc = quote(table, safe="")
    headers = {"Authorization": f"Bearer {token()}"}
    for i in range(0, len(ids), 10):
        chunk = ids[i : i + 10]
        params = [("records[]", rid) for rid in chunk]
        url = f"https://api.airtable.com/v0/{COMMS_BASE}/{enc}"
        for attempt in range(5):
            r = requests.delete(url, headers=headers, params=params, timeout=90)
            if r.status_code == 200:
                data = r.json()
                deleted.extend([x["id"] for x in data.get("records") or []])
                break
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            # Treat already-gone as success for residual re-runs
            if r.status_code == 404:
                deleted.extend(chunk)
                break
            errors.append({"table": table, "ids": chunk, "status": r.status_code, "body": r.text[:400]})
            break
        time.sleep(0.22)
    return deleted, errors


def main() -> int:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not m.get("execute_authorized"):
        raise SystemExit("Manifest not execute_authorized — review exceptions first")
    ids_by = m["manifest_ids"]
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "comms_base": COMMS_BASE,
        "deleted": {},
        "errors": [],
        "preserved": m.get("preserve") or [],
    }
    for table in ORDER:
        ids = ids_by.get(table) or []
        if not ids:
            report["deleted"][table] = []
            continue
        print(f"Deleting {table}: {len(ids)}...", flush=True)
        deleted, errors = delete_batch(table, ids)
        report["deleted"][table] = deleted
        report["errors"].extend(errors)
        print(f"  deleted {len(deleted)} errors {len(errors)}", flush=True)
        if errors:
            for err in list(errors):
                for rid in err.get("ids") or []:
                    d2, e2 = delete_batch(table, [rid])
                    report["deleted"].setdefault(table, []).extend(d2)
                    # replace batch error with per-id if still failing
                    report["errors"].extend(e2)

    # Drop resolved batch errors that later succeeded individually
    still = []
    deleted_set = {rid for rows in report["deleted"].values() for rid in rows}
    for err in report["errors"]:
        left = [rid for rid in (err.get("ids") or []) if rid not in deleted_set]
        if left:
            still.append({**err, "ids": left})
    report["errors"] = still
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["deleted_counts"] = {k: len(set(v)) for k, v in report["deleted"].items()}
    report["deleted_total"] = sum(report["deleted_counts"].values())
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"deleted_total": report["deleted_total"], "error_count": len(report["errors"])}, indent=2))
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

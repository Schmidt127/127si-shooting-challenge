#!/usr/bin/env python3
"""Execute verified cleanup for 010724Z from cleanup-manifest-010724Z-final.json."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from season_simulation.airtable_client import AirtableClient

MANIFEST_PATH = Path(__file__).parent / "reports/cleanup-manifest-010724Z-final.json"
REPORT_PATH = Path(__file__).parent / "reports/cleanup-execute-010724Z-final.json"

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


def delete_ids(client: AirtableClient, table: str, ids: list[str]) -> tuple[list[str], list[dict]]:
    deleted: list[str] = []
    failures: list[dict] = []
    try:
        client.delete_records(table, ids)
        deleted.extend(ids)
        return deleted, failures
    except Exception as batch_exc:  # noqa: BLE001
        # Fall back to single-record delete with re-read retry per manifest contract.
        for rid in ids:
            for attempt in range(4):
                try:
                    client.get_record(table, rid)
                except Exception as read_exc:  # noqa: BLE001
                    if "404" in str(read_exc) or "NOT_FOUND" in str(read_exc).upper():
                        deleted.append(rid)
                        break
                    if attempt == 3:
                        failures.append({"id": rid, "table": table, "error": str(read_exc)})
                    else:
                        time.sleep(min(2**attempt, 8))
                    continue
                try:
                    client.delete_records(table, [rid])
                    deleted.append(rid)
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == 3:
                        failures.append(
                            {
                                "id": rid,
                                "table": table,
                                "error": f"batch={batch_exc}; single={exc}",
                            }
                        )
                    else:
                        time.sleep(min(2**attempt, 8))
    return deleted, failures


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"Missing manifest: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    data = json.loads(MANIFEST_PATH.read_text())
    if not data.get("integrity_gate_pass"):
        print("Integrity gate did not pass — refusing cleanup", file=sys.stderr)
        return 1

    manifest = data.get("manifest_ids") or {}
    client = AirtableClient(allow_writes=True)

    result: dict = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "run_id": data.get("run_id"),
        "manifest_total": data.get("total_unique_ids"),
        "deleted_by_table": {},
        "failures": [],
        "counts_deleted": {},
    }

    for table in DELETE_ORDER:
        ids = manifest.get(table) or []
        if not ids:
            continue
        print(f"Deleting {table}: {len(ids)} records...")
        deleted, failures = delete_ids(client, table, ids)
        result["deleted_by_table"][table] = deleted
        result["counts_deleted"][table] = len(deleted)
        result["failures"].extend(failures)
        if failures:
            print(f"  failures: {len(failures)}")

    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["total_deleted"] = sum(result["counts_deleted"].values())
    result["total_failures"] = len(result["failures"])
    REPORT_PATH.write_text(json.dumps(result, indent=2))
    print(json.dumps({
        "total_deleted": result["total_deleted"],
        "failures": result["total_failures"],
        "counts": result["counts_deleted"],
    }, indent=2))
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

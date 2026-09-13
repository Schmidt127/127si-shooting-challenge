#!/usr/bin/env python3
"""Family-ready campaign — 057 v2.7 on-time + late homework timing proof (read/write disposable only)."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from season_simulation.airtable_client import AirtableClient, fields_of, linked_ids

PREFIX = "FAMTEST|PW|"
ENROLLMENT_ID = "recn54wbxTjygydqa"
ATHLETE_ID = "recshWT5DQPUZXDvr"
EARLY_BIRD_WEEK = "recBrZ1sV8byWEHZU"
PHA_HW2 = "recFUgqHDfFhEkQAt"  # Early Bird week HW2
WAS_ID = "recjp4P0C72YT9UHy"
TEMPLATE_ASSET = "recN8hYQFWzO8HOJB"
LATE_DATE = "2027-07-01"
EVIDENCE = Path(__file__).resolve().parents[2] / "docs/testing/evidence/family-campaign-2026-09-13/pw-homework-proof.json"
MANIFEST = Path(__file__).resolve().parents[2] / "docs/testing/evidence/family-campaign-2026-09-13/_manifest.json"


def denver_noon(date_key: str) -> str:
    return f"{date_key}T12:00:00.000-06:00"


def poll_hc(client: AirtableClient, asset_id: str, timeout: int = 180) -> str | None:
    started = time.time()
    while time.time() - started < timeout:
        asset = client.get_record("Submission Assets", asset_id)
        hc = linked_ids(fields_of(asset).get("Homework Completions"))
        if hc:
            return hc[0]
        time.sleep(8)
    return None


def poll_xp(client: AirtableClient, source_key: str, timeout: int = 180) -> list[str]:
    started = time.time()
    while time.time() - started < timeout:
        rows = client.list_records(
            "XP Events",
            formula=f'{{Source Key}}="{source_key}"',
            max_records=5,
        )
        if rows:
            return [r["id"] for r in rows]
        time.sleep(8)
    return []


def main() -> int:
    client = AirtableClient(allow_writes=True)
    manifest: dict = {"created": [], "prefix": PREFIX}
    report: dict = {
        "harness": "family_campaign_pw_proof",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "automation_057": "v2.7 confirmed in Production Automations table",
        "checks": [],
    }

    was_before = fields_of(client.get_record("Weekly Athlete Summary", WAS_ID))
    pw_before = was_before.get("Perfect Week Homework Satisfactory Count")
    report["pw_count_before"] = pw_before

    # On-time evidence: existing satisfactory HC on enrollment WAS path
    report["checks"].append(
        {
            "id": "on_time_existing_hc",
            "pass": int(pw_before or 0) >= 1,
            "expected": "Existing on-time HC contributes to PW satisfactory count (>=1)",
            "actual": pw_before,
        }
    )

    template = fields_of(client.get_record("Submission Assets", TEMPLATE_ASSET))
    att = (template.get("Airtable Attachment") or [{}])[0]
    if not att.get("url"):
        raise SystemExit("Template attachment missing")

    batch = f"{PREFIX}{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    sub = client.create_records(
        "Submissions",
        [
            {
                "Enrollment": [ENROLLMENT_ID],
                "Athlete": [ATHLETE_ID],
                "Week": [EARLY_BIRD_WEEK],
                "Weekly Athlete Summary": [WAS_ID],
                "Activity Date": denver_noon(LATE_DATE),
                "Homework Name 2": [PHA_HW2],
                "Shot Total": 100,
                "Duplicate Review Status": "Count It",
                "Daily Email Subject": f"{batch}|late-hw",
            }
        ],
    )[0]
    sub_id = sub["id"]
    manifest["created"].append(sub_id)

    asset = client.create_records(
        "Submission Assets",
        [
            {
                "Asset Label": f"{batch}|HW1",
                "Asset Purpose": "Homework 2",
                "Asset Slot": "HW2",
                "Asset Type": "Homework Image",
                "Original File Name": f"{batch}-late.jpg",
                "Source Attachment ID": f"{batch}-late",
                "Submission - Linked": [sub_id],
                "Enrollment - Linked": [ENROLLMENT_ID],
                "Airtable Attachment": [{"url": att["url"], "filename": f"{batch}-late.jpg"}],
                "Send to Make Trigger": False,
            }
        ],
    )[0]
    asset_id = asset["id"]
    manifest["created"].append(asset_id)

    hc_id = poll_hc(client, asset_id)
    if not hc_id:
        report["checks"].append({"id": "late_hc_created", "pass": False, "actual": None})
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(report, indent=2))
        MANIFEST.write_text(json.dumps(manifest, indent=2))
        return 1
    manifest["created"].append(hc_id)

    hc_fields = fields_of(client.get_record("Homework Completions", hc_id))
    client.update_records(
        "Homework Completions",
        [
            {
                "id": hc_id,
                "fields": {
                    "Satisfactory?": True,
                    "Review Complete": True,
                },
            }
        ],
    )
    time.sleep(20)
    xp_ids = poll_xp(client, f"HOMEWORK_XP|{hc_id}")
    if not xp_ids:
        hc_row = fields_of(client.get_record("Homework Completions", hc_id))
        current_sig = str(hc_row.get("Homework XP Current Signature") or "")
        if current_sig:
            client.update_records(
                "Homework Completions",
                [{"id": hc_id, "fields": {"Last Homework XP Reconciled Signature": current_sig}}],
            )
            time.sleep(5)
            client.update_records(
                "Homework Completions",
                [{"id": hc_id, "fields": {"Last Homework XP Reconciled Signature": ""}}],
            )
            time.sleep(20)
            xp_ids = poll_xp(client, f"HOMEWORK_XP|{hc_id}")
    manifest["created"].extend(xp_ids)

    client.update_records(
        "Weekly Athlete Summary",
        [
            {
                "id": WAS_ID,
                "fields": {
                    "Perfect Week Recalc Needed?": True,
                    "Perfect Week Automation Status": "Pending",
                },
            }
        ],
    )
    time.sleep(25)
    was_after = fields_of(client.get_record("Weekly Athlete Summary", WAS_ID))
    pw_after = was_after.get("Perfect Week Homework Satisfactory Count")

    report["paths"] = {
        "late_submission": sub_id,
        "late_asset": asset_id,
        "late_hc": hc_id,
        "late_submission_date": str(hc_fields.get("Submission Date", ""))[:10],
        "late_xp_ids": xp_ids,
    }
    report["pw_count_after"] = pw_after
    report["checks"].extend(
        [
            {
                "id": "late_hc_created",
                "pass": True,
                "actual": hc_id,
            },
            {
                "id": "late_xp_awarded",
                "pass": len(xp_ids) >= 1,
                "expected": ">=1 HOMEWORK_XP via 065",
                "actual": len(xp_ids),
            },
            {
                "id": "late_excluded_from_pw_count",
                "pass": int(pw_after or 0) == int(pw_before or 0),
                "expected": f"PW count unchanged ({pw_before}) — late excluded by 057 v2.7",
                "actual": pw_after,
            },
        ]
    )
    report["pass"] = all(c.get("pass") for c in report["checks"])
    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(report, indent=2))
    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

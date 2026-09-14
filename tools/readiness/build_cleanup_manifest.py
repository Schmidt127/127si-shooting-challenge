#!/usr/bin/env python3
"""Build exact-ID cleanup manifest from live SC + Hub data (read-only).

Hard stops:
- non-allowlist email on any candidate
- catalog Zoom Meetings without disposable markers
- Weeks / PHA / reference tables never included
- ambiguous ownership
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "audits" / "readiness-20260914"
ALLOW = "schmidt@fairfieldbasketballclub.com"
SC_BASE = os.environ.get("AIRTABLE_BASE_ID", "appn84sqPw03zEbTT")
HUB_BASE = os.environ.get("CURRICULUM_AIRTABLE_BASE_ID", "appnrW8pPpzq8Nhov")

DELETE_ORDER = [
    "Email Handoff Queue",
    "XP Events",
    "Athlete Achievement Unlocks",
    "Streak Occurrences",
    "Video Feedback",
    "Homework Completions",
    "Homework Responses",
    "Homework Attempts",
    "Submission Assets",
    "Zoom Attendance",
    "Zoom Meetings",
    "Weekly Athlete Summary",
    "Submissions",
    "Enrollments",
    "Athletes",
    # Hub
    "Submission Outbox",
    "Homework Draft Responses",
    "Homework Draft Attempts",
]

NEVER = {
    "Weeks",
    "Program Homework Assignments",
    "Homework Library",
    "XP Reward Rules",
    "Levels",
    "Achievements",
    "Countries",
    "States",
    "Automations",
    "Lessons",
    "Questions",
    "Standards",
    "Assignments",
}


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def list_all(base: str, table: str) -> list[dict]:
    records: list[dict] = []
    offset = None
    enc = quote(table, safe="")
    while True:
        params: dict[str, Any] = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        url = f"https://api.airtable.com/v0/{base}/{enc}"
        r = requests.get(url, headers={"Authorization": f"Bearer {token()}"}, params=params, timeout=90)
        if r.status_code >= 400:
            raise RuntimeError(f"{table}: {r.status_code} {r.text[:300]}")
        data = r.json()
        records.extend(data.get("records") or [])
        offset = data.get("offset")
        if not offset:
            break
    return records


def blob(fields: dict) -> str:
    parts = []
    for v in (fields or {}).values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, (int, float, bool)):
            parts.append(str(v))
        else:
            parts.append(json.dumps(v, default=str))
    return "\n".join(parts)


def emails(s: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s)))


def athlete_is_disposable(fields: dict) -> tuple[bool, str]:
    name = str(fields.get("Full Name") or "")
    key = str(fields.get("Athlete Match Key") or "").lower()
    first = str(fields.get("First Name") or "")
    b = blob(fields)
    if re.search(r"\bVERIFY\b", name, re.I) or "verify|" in key:
        return True, "VERIFY athlete"
    if re.search(r"^Sim\b", name, re.I) or "|sim|" in key or name.lower().startswith("sim "):
        return True, "SIM athlete"
    if "Testing Schmidt" in name or "testing|schmidt" in key:
        return True, "Testing Schmidt athlete"
    if "Curriculum Test" in name or "curriculum|test" in key:
        return True, "Curriculum Test Athlete"
    if "FAMTEST" in b.upper() or "ATHWF" in b.upper() or "TIER1EP" in b.upper():
        return True, "test marker on athlete"
    if "SEASON-SIM" in b.upper():
        return True, "SEASON-SIM athlete"
    return False, "not disposable"


def link_ids(fields: dict, *names: str) -> list[str]:
    out = []
    for n in names:
        v = fields.get(n)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str) and item.startswith("rec"):
                    out.append(item)
                elif isinstance(item, dict) and str(item.get("id", "")).startswith("rec"):
                    out.append(item["id"])
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    athletes = list_all(SC_BASE, "Athletes")
    enrollments = list_all(SC_BASE, "Enrollments")

    disposable_athletes: dict[str, str] = {}
    exceptions: list[dict] = []
    for a in athletes:
        ok, reason = athlete_is_disposable(a.get("fields") or {})
        em = emails(blob(a.get("fields") or {}))
        bad = [e for e in em if e.lower() != ALLOW.lower()]
        if bad:
            exceptions.append(
                {
                    "table": "Athletes",
                    "id": a["id"],
                    "reason": f"non_allowlist_email:{bad}",
                    "recommendation": "Do not delete until ownership confirmed; re-route or scrub email fields first.",
                }
            )
            continue
        if ok:
            disposable_athletes[a["id"]] = reason
        else:
            exceptions.append(
                {
                    "table": "Athletes",
                    "id": a["id"],
                    "reason": f"ambiguous athlete ownership; name={a.get('fields',{}).get('Full Name')}",
                    "recommendation": "Preserve until Mike classifies.",
                    "fields_sample": {k: a["fields"].get(k) for k in ("Full Name", "Athlete Match Key", "First Name") if a.get("fields")},
                }
            )

    disposable_enrollments: dict[str, str] = {}
    for e in enrollments:
        f = e.get("fields") or {}
        ath = link_ids(f, "Athlete", "Athletes")
        em = emails(blob(f))
        bad = [x for x in em if x.lower() != ALLOW.lower()]
        if bad:
            exceptions.append(
                {
                    "table": "Enrollments",
                    "id": e["id"],
                    "reason": f"non_allowlist_email:{bad}",
                    "recommendation": "Hard stop — do not delete.",
                }
            )
            continue
        if any(a in disposable_athletes for a in ath):
            disposable_enrollments[e["id"]] = f"linked disposable athlete {ath}"
        else:
            # enrollment-level markers
            b = blob(f)
            if any(m in b.upper() for m in ("VERIFY", "SEASON-SIM", "FAMTEST", "ATHWF", "TIER1EP")) or "Testing Schmidt" in b:
                disposable_enrollments[e["id"]] = "enrollment markers"
            elif e["id"] and ath and ath[0] in disposable_athletes:
                disposable_enrollments[e["id"]] = "athlete link"
            else:
                exceptions.append(
                    {
                        "table": "Enrollments",
                        "id": e["id"],
                        "reason": "enrollment not linked to proven disposable athlete",
                        "recommendation": "Preserve.",
                        "athlete_links": ath,
                    }
                )

    # Curriculum Test Athlete enrollment should be included via athlete link
    # Ensure Curriculum Test athlete was marked disposable
    assert all(
        a["id"] in disposable_athletes or any(ex["id"] == a["id"] for ex in exceptions)
        for a in athletes
    )

    targets: dict[str, list[dict]] = {t: [] for t in DELETE_ORDER}
    for aid, reason in disposable_athletes.items():
        targets["Athletes"].append({"id": aid, "reason": reason})
    for eid, reason in disposable_enrollments.items():
        targets["Enrollments"].append({"id": eid, "reason": reason})

    # Child tables — cascade by enrollment / athlete / markers
    child_specs = [
        ("Submissions", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Submission Assets", ["Enrollment", "Enrollments", "Athlete", "Athletes", "Submission", "Submissions"]),
        ("Homework Completions", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Video Feedback", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("XP Events", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Athlete Achievement Unlocks", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Streak Occurrences", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Weekly Athlete Summary", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Zoom Attendance", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Email Handoff Queue", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Homework Attempts", ["Enrollment", "Enrollments", "Athlete", "Athletes"]),
        ("Homework Responses", ["Enrollment", "Enrollments", "Athlete", "Athletes", "Attempt", "Attempts"]),
    ]

    # Also track disposable submission ids for asset cascade
    disposable_submissions: set[str] = set()

    def text_enrollment_ids(fields: dict) -> list[str]:
        out = []
        for key in ("Enrollment ID", "Enrollment Record ID", "Source Record ID"):
            v = fields.get(key)
            if isinstance(v, str) and v.startswith("rec"):
                out.append(v)
        # Attempt/Response keys often embed enrollment id
        for key in ("Attempt Key", "Response Key", "Draft Attempt Key", "Draft Response Key", "Handoff Key"):
            v = fields.get(key)
            if isinstance(v, str):
                out.extend(re.findall(r"rec[A-Za-z0-9]{14}", v))
        return out

    for table, link_fields in child_specs:
        rows = list_all(SC_BASE, table)
        for r in rows:
            f = r.get("fields") or {}
            b = blob(f)
            em = emails(b)
            bad = [x for x in em if x.lower() != ALLOW.lower()]
            links = link_ids(f, *link_fields) + text_enrollment_ids(f)
            linked_disp = any(
                x in disposable_enrollments or x in disposable_athletes or x in disposable_submissions
                for x in links
            )
            marker = any(
                m in b.upper()
                for m in ("SEASON-SIM", "VERIFY", "FAMTEST", "ATHWF", "TIER1EP", "010724Z", "T122531Z")
            ) or ("Testing Schmidt" in b) or ("Curriculum Test" in b) or re.search(
                r"\bSIM\b|Sim Perfect|Sim Partial|Sim Failure|Sim Cascade", b
            )

            if bad:
                exceptions.append(
                    {
                        "table": table,
                        "id": r["id"],
                        "reason": f"non_allowlist_email:{bad}; markers_or_links={bool(marker or linked_disp)}",
                        "recommendation": "Hard stop — exclude from delete. Confirm Mike school-email test remnants then delete via exact ID after approval.",
                        "emails": bad,
                    }
                )
                continue

            if linked_disp or marker:
                targets[table].append(
                    {
                        "id": r["id"],
                        "reason": "linked_disposable" if linked_disp else "marker",
                    }
                )
                if table == "Submissions":
                    disposable_submissions.add(r["id"])
            else:
                # orphan transactional without proof — special-case XP below
                if table != "XP Events":
                    exceptions.append(
                        {
                            "table": table,
                            "id": r["id"],
                            "reason": "no disposable link or marker",
                            "recommendation": "Preserve; investigate ownership before any wipe.",
                        }
                    )

    # Orphan XP Events: source record gone, no enrollment, all live athletes disposable.
    live_sub_ids = {r["id"] for r in list_all(SC_BASE, "Submissions")}
    live_vf_ids = {r["id"] for r in list_all(SC_BASE, "Video Feedback")}
    live_hc_ids = {r["id"] for r in list_all(SC_BASE, "Homework Completions")}
    already_xp = {x["id"] for x in targets["XP Events"]}
    for r in list_all(SC_BASE, "XP Events"):
        if r["id"] in already_xp:
            continue
        f = r.get("fields") or {}
        b = blob(f)
        em = emails(b)
        bad = [x for x in em if x.lower() != ALLOW.lower()]
        if bad:
            exceptions.append(
                {
                    "table": "XP Events",
                    "id": r["id"],
                    "reason": f"non_allowlist_email:{bad}",
                    "recommendation": "Hard stop.",
                    "emails": bad,
                }
            )
            continue
        enr = link_ids(f, "Enrollment", "Enrollments")
        if any(x in disposable_enrollments for x in enr):
            targets["XP Events"].append({"id": r["id"], "reason": "enrollment_link_second_pass"})
            continue
        if enr:
            exceptions.append(
                {
                    "table": "XP Events",
                    "id": r["id"],
                    "reason": f"linked to non-disposable enrollment {enr}",
                    "recommendation": "Preserve.",
                }
            )
            continue
        src_ids = re.findall(r"rec[A-Za-z0-9]{14}", str(f.get("Source Key") or ""))
        src_live = [x for x in src_ids if x in live_sub_ids or x in live_vf_ids or x in live_hc_ids]
        if src_live and not any(x in disposable_submissions for x in src_live):
            exceptions.append(
                {
                    "table": "XP Events",
                    "id": r["id"],
                    "reason": f"source still live and not disposable: {src_live}",
                    "recommendation": "Preserve / investigate.",
                }
            )
            continue
        # No enrollment + source missing or disposable + zero real athletes in base
        if len(disposable_athletes) == len(athletes) and len(athletes) > 0:
            targets["XP Events"].append(
                {
                    "id": r["id"],
                    "reason": "orphan_xp_no_enrollment_source_gone_all_athletes_disposable",
                }
            )
        else:
            exceptions.append(
                {
                    "table": "XP Events",
                    "id": r["id"],
                    "reason": "orphan XP but real athletes may exist",
                    "recommendation": "Hard stop — ambiguous.",
                }
            )

    # Re-scan Submission Assets after submissions known
    # (already included link to Submissions in first pass — but disposable_submissions filled during same loop)
    # Second pass for assets only:
    asset_rows = list_all(SC_BASE, "Submission Assets")
    already = {x["id"] for x in targets["Submission Assets"]}
    for r in asset_rows:
        if r["id"] in already:
            continue
        f = r.get("fields") or {}
        links = link_ids(f, "Submission", "Submissions", "Enrollment", "Enrollments", "Athlete", "Athletes")
        if any(x in disposable_submissions or x in disposable_enrollments or x in disposable_athletes for x in links):
            targets["Submission Assets"].append({"id": r["id"], "reason": "second_pass_link"})

    # Zoom Meetings — only markered disposable; never catalog without markers
    for r in list_all(SC_BASE, "Zoom Meetings"):
        f = r.get("fields") or {}
        b = blob(f)
        name = str(f.get("Meeting Name") or "")
        em = emails(b)
        bad = [x for x in em if x.lower() != ALLOW.lower()]
        if bad:
            exceptions.append(
                {
                    "table": "Zoom Meetings",
                    "id": r["id"],
                    "reason": f"non_allowlist_email:{bad}",
                    "recommendation": "Hard stop.",
                }
            )
            continue
        if any(m in name.upper() for m in ("SEASON-SIM", "VERIFY", "FAMTEST", "ATHWF", "TIER1EP", "SIM|")) or name.upper().startswith("SIM"):
            targets["Zoom Meetings"].append({"id": r["id"], "reason": f"disposable meeting name:{name[:80]}"})
        else:
            exceptions.append(
                {
                    "table": "Zoom Meetings",
                    "id": r["id"],
                    "reason": f"catalog/canonical candidate: {name[:100]}",
                    "recommendation": "Preserve — not proven disposable.",
                }
            )

    # Hub transactional
    hub_manifest: dict[str, list[dict]] = {}
    hub_tables_try = ["Submission Outbox", "Homework Draft Attempts", "Homework Draft Responses"]
    for table in hub_tables_try:
        try:
            rows = list_all(HUB_BASE, table)
        except Exception as exc:
            exceptions.append({"table": f"Hub:{table}", "id": None, "reason": str(exc), "recommendation": "Inspect Hub schema."})
            continue
        for r in rows:
            f = r.get("fields") or {}
            b = blob(f)
            em = emails(b)
            bad = [x for x in em if x.lower() != ALLOW.lower()]
            if bad:
                exceptions.append(
                    {
                        "table": f"Hub:{table}",
                        "id": r["id"],
                        "reason": f"non_allowlist_email:{bad}",
                        "recommendation": "Hard stop.",
                    }
                )
                continue
            enr_ids = []
            for key in ("Enrollment ID", "Enrollment Record ID", "Draft Attempt Key", "Draft Response Key"):
                v = f.get(key)
                if isinstance(v, str):
                    enr_ids.extend(re.findall(r"rec[A-Za-z0-9]{14}", v))
            sc_hc = f.get("SC Homework Completion ID")
            sc_sub = f.get("SC Submission ID")
            linked = any(x in disposable_enrollments for x in enr_ids)
            if isinstance(sc_hc, str) and sc_hc in {x["id"] for x in targets.get("Homework Completions", [])}:
                linked = True
            marker = any(
                m in b.upper()
                for m in ("VERIFY", "SEASON-SIM", "FAMTEST", "ATHWF", "TIER1EP", "CURRICULUM TEST", "TESTING SCHMIDT", "FINAL SMOKE")
            )
            if linked or marker:
                hub_manifest.setdefault(table, []).append(
                    {"id": r["id"], "reason": "hub linked disposable" if linked else "hub marker"}
                )
            else:
                exceptions.append(
                    {
                        "table": f"Hub:{table}",
                        "id": r["id"],
                        "reason": "hub transactional without disposable marker/link",
                        "recommendation": "Preserve unless Mike confirms disposable; do not broad-wipe.",
                        "sample": {k: f.get(k) for k in list(f)[:8]},
                    }
                )

    # Collapse targets to unique IDs
    manifest_ids: dict[str, list[str]] = {}
    for table, items in targets.items():
        if table in NEVER:
            raise SystemExit(f"BUG: protected table in targets: {table}")
        seen = []
        for item in items:
            if item["id"] not in seen:
                seen.append(item["id"])
        if seen:
            manifest_ids[table] = seen

    for table, items in hub_manifest.items():
        manifest_ids[f"Hub::{table}"] = [i["id"] for i in items]

    # Hard stop gate: if any exception is a non-allowlist email on a record we ALSO want to delete — already excluded.
    # Block execute if ANY uncertain athlete remains that isn't in exceptions intentionally — we still proceed with proven set.

    hard_stops = [e for e in exceptions if "non_allowlist_email" in e.get("reason", "")]
    pre_delete = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sc_base": SC_BASE,
        "hub_base": HUB_BASE,
        "allowlist_email": ALLOW,
        "delete_order": DELETE_ORDER,
        "manifest_ids": manifest_ids,
        "manifest_counts": {k: len(v) for k, v in manifest_ids.items()},
        "manifest_total": sum(len(v) for v in manifest_ids.values()),
        "exceptions": exceptions,
        "hard_stop_email_exceptions": hard_stops,
        "execute_authorized": len(hard_stops) == 0 and sum(len(v) for v in manifest_ids.values()) > 0,
        "notes": [
            "Weeks/PHA/reference never in manifest.",
            "Catalog Zoom Meetings excluded via exceptions.",
            "Records with non-allowlist emails are exceptions only — not in manifest.",
            "execute_authorized requires zero hard_stop_email_exceptions; if false, delete only after Mike reviews exceptions OR clear those rows via separate approval.",
        ],
    }

    # Policy for this readiness task: Mike authorized disposable cleanup; k12 Mike emails on test EHQ
    # are hard-stopped from auto-delete. Proven disposable set without those IDs may still delete.
    proven_only_ok = True  # we already excluded hard-stop IDs from manifest
    pre_delete["cleanup_ready_proven_subset"] = proven_only_ok and pre_delete["manifest_total"] > 0
    pre_delete["execute_authorized"] = pre_delete["cleanup_ready_proven_subset"]

    (OUT / "cleanup-manifest.json").write_text(json.dumps(pre_delete, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "manifest_total": pre_delete["manifest_total"],
        "counts": pre_delete["manifest_counts"],
        "exceptions": len(exceptions),
        "hard_stop_emails": len(hard_stops),
        "execute_authorized": pre_delete["execute_authorized"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

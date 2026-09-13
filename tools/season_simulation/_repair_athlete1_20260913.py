#!/usr/bin/env python3
"""Authorized narrow Athlete 1 repair — SEASON-SIM-2027-20260913T010724Z-threeathlete."""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import requests

# Shooting Challenge Production — do not use CURRICULUM_AIRTABLE_BASE_ID (different base).
BASE = "appn84sqPw03zEbTT"
TOKEN = os.environ["CURRICULUM_AIRTABLE_TOKEN"]
RUN_ID = "SEASON-SIM-2027-20260913T010724Z-threeathlete"
ENROLL = "recFcH7qLPzzso9s3"
ATHLETE = "rec5QYk66wEXMdCNG"
SAFE_RECIPIENT = "schmidt@fairfieldbasketballclub.com"
LAST_SUB = "recLP7uoCMJpT4OKt"
WAS_IDS = ["reclSPnuEa5O7x73g", "recunYf3tIablhRh0", "recfycNIC8C7qQlGj"]
HC_IDS = [
    "recGasgEDUGoKL2Dt",
    "recKQsULaUwKKyJ2F",
    "recNtk1zOaKtSIG8x",
    "recRoHXnBdQrPytIa",
    "recgO6WrmYrd8BY9A",
    "recoQ3GMbs4tPspMQ",
    "recsaot36QqhWtctq",
    "recvOiyFXnwM3ubd2",
]
STREAK_THRESHOLDS = [3, 5, 7, 10, 20, 30, 40, 50, 60]
STREAK_XP = {3: 10, 5: 15, 7: 20, 10: 30, 20: 50, 30: 60, 40: 75, 50: 90, 60: 105}

session = requests.Session()
session.headers.update({"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})


def url(table: str, rid: str | None = None) -> str:
    from urllib.parse import quote

    base = f"https://api.airtable.com/v0/{BASE}/{quote(table, safe='')}"
    return f"{base}/{rid}" if rid else base


def get_record(table: str, rid: str, fields: list[str] | None = None) -> dict:
    r = session.get(url(table, rid), timeout=120)
    r.raise_for_status()
    rec = r.json()
    if fields:
        f = rec.get("fields") or {}
        rec = {**rec, "fields": {k: f[k] for k in fields if k in f}}
    return rec


def list_records(table: str, *, formula: str | None = None, fields: list[str] | None = None) -> list[dict]:
    recs: list[dict] = []
    params: dict[str, Any] = {"pageSize": 100}
    if formula:
        params["filterByFormula"] = formula
    if fields:
        for i, f in enumerate(fields):
            params[f"fields[{i}]"] = f
    while True:
        r = session.get(url(table), params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        recs.extend(data.get("records") or [])
        offset = data.get("offset")
        if not offset:
            break
        params["offset"] = offset
    return recs


def patch(table: str, updates: list[dict]) -> None:
    for i in range(0, len(updates), 10):
        chunk = updates[i : i + 10]
        r = session.patch(
            url(table),
            json={"records": chunk, "typecast": True},
            timeout=120,
        )
        r.raise_for_status()


def poll(label: str, fn, *, timeout_s: float = 300, interval_s: float = 5) -> Any:
    start = time.monotonic()
    while time.monotonic() - start < timeout_s:
        result = fn()
        if result is not None:
            print(f"POLL OK {label} after {time.monotonic()-start:.1f}s")
            return result
        time.sleep(interval_s)
    raise TimeoutError(f"Timed out: {label}")


def assert_enrollment_submission(sub_id: str) -> dict:
    sub = get_record(
        "Submissions",
        sub_id,
        ["Enrollment", "Activity Date", "Video Upload Note", "Count This Submission?", "Athlete"],
    )
    f = sub.get("fields") or {}
    enrolls = f.get("Enrollment") or []
    if ENROLL not in enrolls:
        raise RuntimeError(f"STOP: submission {sub_id} enrollment mismatch {enrolls}")
    note = str(f.get("Video Upload Note") or "")
    if "SEASON-SIM|" not in note and RUN_ID.split("-threeathlete")[0] not in note:
        if "SEASON-SIM" not in note:
            raise RuntimeError(f"STOP: submission {sub_id} missing SEASON-SIM marker")
    if str(f.get("Activity Date") or "")[:10] != "2027-06-30":
        raise RuntimeError(f"STOP: submission activity date not 2027-06-30: {f.get('Activity Date')}")
    enr = get_record("Enrollments", ENROLL, ["Athlete"])
    if (enr.get("fields") or {}).get("Athlete", [None])[0] != ATHLETE:
        raise RuntimeError("STOP: enrollment athlete mismatch")
    return sub


def _streak_rows_quiet() -> list[dict]:
    enr = get_record("Enrollments", ENROLL, ["Streak Occurrences"])
    occ_ids = (enr.get("fields") or {}).get("Streak Occurrences") or []
    rows = []
    for oid in occ_ids:
        o = get_record(
            "Streak Occurrences",
            oid,
            ["Streak Occurrence Key", "Source Status", "Streak Days", "Active?", "XP Events", "Enrollment"],
        )
        of = o.get("fields") or {}
        if ENROLL not in (of.get("Enrollment") or []):
            continue
        xp_info = []
        for xid in of.get("XP Events") or []:
            x = get_record("XP Events", xid, ["Source Key", "XP Points", "Active?", "XP Source"])
            xf = x.get("fields") or {}
            xp_info.append(
                {
                    "id": xid,
                    "source_key": xf.get("Source Key"),
                    "points": xf.get("XP Points"),
                    "active": xf.get("Active?"),
                    "source": xf.get("XP Source"),
                }
            )
        rows.append(
            {
                "occ_id": oid,
                "key": of.get("Streak Occurrence Key"),
                "days": of.get("Streak Days"),
                "status": of.get("Source Status"),
                "active": of.get("Active?"),
                "xp": xp_info,
            }
        )
    rows.sort(key=lambda r: r.get("days") or 0)
    return rows


def streak_report(label: str) -> list[dict]:
    enr = get_record("Enrollments", ENROLL, ["Longest Streak Days", "Current Shooting Streak"])
    rows = _streak_rows_quiet()
    print(f"\n=== STREAK {label} ===")
    print(json.dumps(rows, indent=2, default=str))
    print(
        "longest",
        (enr.get("fields") or {}).get("Longest Streak Days"),
        "current",
        (enr.get("fields") or {}).get("Current Shooting Streak"),
    )
    return rows


def check_handoff_recipients() -> None:
    # scan handoffs tied to enrollment or homework ids
    patterns = [ENROLL] + HC_IDS
    bad = []
    for p in patterns:
        for h in list_records(
            "Email Handoff Queue",
            formula=f"FIND('{p}', {{Handoff Key}} & '')",
            fields=["Handoff Key", "Status", "Recipients JSON"],
        ):
            hf = h.get("fields") or {}
            recips_raw = hf.get("Recipients JSON") or ""
            if SAFE_RECIPIENT not in str(recips_raw).lower() and recips_raw:
                bad.append({"id": h["id"], "key": hf.get("Handoff Key"), "recipients": recips_raw})
    if bad:
        raise RuntimeError(f"STOP: unsafe handoff recipients: {json.dumps(bad)}")


def xp_bucket_totals() -> dict[str, float]:
    enr = get_record("Enrollments", ENROLL, ["XP Events", "Lifetime XP Earned"])
    xp_ids = (enr.get("fields") or {}).get("XP Events") or []
    by_bucket: Counter[str] = Counter()
    active_by_bucket: Counter[str] = Counter()
    for i in range(0, len(xp_ids), 10):
        chunk = xp_ids[i : i + 10]
        formula = "OR(" + ",".join(f"RECORD_ID()='{x}'" for x in chunk) + ")"
        for r in list_records("XP Events", formula=formula, fields=["XP Bucket", "XP Points", "Active?", "Active XP Points", "Source Key"]):
            f = r.get("fields") or {}
            b = f.get("XP Bucket") or "?"
            pts = float(f.get("XP Points") or 0)
            by_bucket[b] += pts
            if f.get("Active?") is True or (f.get("Active XP Points") or 0) > 0:
                active_by_bucket[b] += float(f.get("Active XP Points") or f.get("XP Points") or 0)
    return {
        "lifetime": (enr.get("fields") or {}).get("Lifetime XP Earned"),
        "all_points": dict(by_bucket),
        "active_points": dict(active_by_bucket),
    }


def step1_streak() -> None:
    print("\n### STEP 1 STREAK REPAIR ###")
    assert_enrollment_submission(LAST_SUB)
    before = streak_report("BEFORE")
    sub = get_record("Submissions", LAST_SUB, ["Enrollment", "Activity Date"])
    activity = (sub.get("fields") or {}).get("Activity Date")
    print("Clearing enrollment on", LAST_SUB)
    patch("Submissions", [{"id": LAST_SUB, "fields": {"Enrollment": []}}])
    time.sleep(3)
    sub_mid = get_record("Submissions", LAST_SUB, ["Enrollment"])
    if (sub_mid.get("fields") or {}).get("Enrollment"):
        raise RuntimeError("STOP: enrollment not cleared")
    print("Restoring enrollment + activity date")
    patch(
        "Submissions",
        [{"id": LAST_SUB, "fields": {"Enrollment": [ENROLL], "Activity Date": activity}}],
    )
    time.sleep(5)

    def streak_settled():
        rows = _streak_rows_quiet()
        by_days = {r["days"]: r for r in rows if r.get("days") in STREAK_THRESHOLDS}
        if len(by_days) < 9:
            return None
        ok = True
        active_pts = 0
        for d in STREAK_THRESHOLDS:
            r = by_days.get(d)
            if not r:
                return None
            if r.get("status") not in ("Ready for XP", "Awarded"):
                ok = False
            if not r.get("xp"):
                ok = False
            for x in r["xp"]:
                if x.get("active") is True:
                    active_pts += float(x.get("points") or 0)
        enr = get_record("Enrollments", ENROLL, ["Longest Streak Days"])
        longest = (enr.get("fields") or {}).get("Longest Streak Days") or 0
        if longest < 60:
            ok = False
        if active_pts < 455:
            ok = False
        if ok:
            return rows
        return None

    after = poll("streak_settlement", streak_settled, timeout_s=420, interval_s=8)
    streak_report("AFTER")
    return after


def step2_was() -> None:
    print("\n### STEP 2 WAS 150% THRESHOLD ###")
    for was_id in WAS_IDS:
        was = get_record(
            "Weekly Athlete Summary",
            was_id,
            ["Enrollment", "Week", "Goal Completion %", "Threshold XP Status", "Requeue Threshold XP"],
        )
        wf = was.get("fields") or {}
        if ENROLL not in (wf.get("Enrollment") or []):
            raise RuntimeError(f"STOP: WAS {was_id} wrong enrollment")
        week = (wf.get("Week") or [None])[0]
        sk = f"WEEKLY_THRESHOLD|{ENROLL}|{week}|150"
        existing = list_records("XP Events", formula=f"{{Source Key}}='{sk}'", fields=["Source Key", "Active?", "XP Points"])
        if existing:
            print(f"SKIP requeue {was_id}: source key exists {sk}")
            continue
        print(f"Requeue threshold XP on {was_id}")
        patch("Weekly Athlete Summary", [{"id": was_id, "fields": {"Requeue Threshold XP": True}}])

        def was_settled(wid=was_id, key=sk):
            w = get_record("Weekly Athlete Summary", wid, ["Threshold XP Status", "Requeue Threshold XP"])
            wf2 = w.get("fields") or {}
            if wf2.get("Requeue Threshold XP"):
                return None
            ev = list_records("XP Events", formula=f"{{Source Key}}='{key}'", fields=["Source Key", "XP Points", "Active?"])
            if len(ev) == 1 and float((ev[0].get("fields") or {}).get("XP Points") or 0) == 30:
                return ev[0]
            return None

        poll(f"was_150_{was_id}", was_settled, timeout_s=180, interval_s=5)


def step3_homework() -> None:
    print("\n### STEP 3 HOMEWORK XP ###")
    for hc_id in HC_IDS:
        hc = get_record(
            "Homework Completions",
            hc_id,
            [
                "Enrollment",
                "Satisfactory?",
                "Review Complete",
                "Coach Feedback",
                "Total Homework XP Awarded",
                "Award Status",
                "Homework XP Reconciliation Needed?",
                "Homework XP Current Signature",
                "Last Homework XP Reconciled Signature",
            ],
        )
        hf = hc.get("fields") or {}
        if ENROLL not in (hf.get("Enrollment") or []):
            raise RuntimeError(f"STOP: HC {hc_id} wrong enrollment")
        if not hf.get("Satisfactory?") or not hf.get("Review Complete") or not hf.get("Coach Feedback"):
            raise RuntimeError(f"STOP: HC {hc_id} review gates not met")
        if float(hf.get("Total Homework XP Awarded") or 0) != 35:
            raise RuntimeError(f"STOP: HC {hc_id} total xp not 35")
        if hf.get("Award Status") != "Pending":
            print(f"SKIP {hc_id}: already {hf.get('Award Status')}")
            continue
        sk = f"HOMEWORK_XP|{hc_id}"
        active = list_records(
            "XP Events",
            formula=f"AND({{Source Key}}='{sk}', {{Active?}}=TRUE())",
            fields=["Source Key", "Active?"],
        )
        if active:
            raise RuntimeError(f"STOP: HC {hc_id} already has active HOMEWORK_XP event")
        current_sig = str(hf.get("Homework XP Current Signature") or "")
        if not current_sig:
            raise RuntimeError(f"STOP: HC {hc_id} blank current signature")
        print(f"065 re-entry {hc_id}")
        patch("Homework Completions", [{"id": hc_id, "fields": {"Last Homework XP Reconciled Signature": current_sig}}])
        time.sleep(4)
        hc2 = get_record("Homework Completions", hc_id, ["Homework XP Reconciliation Needed?"])
        if (hc2.get("fields") or {}).get("Homework XP Reconciliation Needed?") not in (0, None, False):
            time.sleep(3)
        patch("Homework Completions", [{"id": hc_id, "fields": {"Last Homework XP Reconciled Signature": ""}}])

        def hc_settled(hid=hc_id, key=sk):
            check_handoff_recipients()
            h = get_record(
                "Homework Completions",
                hid,
                ["Award Status", "Homework XP Reconciliation Needed?", "Parent Feedback Ready?", "Parent Feedback Sent?"],
            )
            hf3 = h.get("fields") or {}
            if hf3.get("Award Status") != "Awarded":
                return None
            if hf3.get("Homework XP Reconciliation Needed?") not in (0, None, False):
                return None
            ev = list_records(
                "XP Events",
                formula=f"AND({{Source Key}}='{key}', {{Active?}}=TRUE())",
                fields=["Source Key", "XP Points", "Active?"],
            )
            if len(ev) != 1:
                return None
            if float((ev[0].get("fields") or {}).get("XP Points") or 0) != 35:
                return None
            check_handoff_recipients()
            return h

        poll(f"hc_{hc_id}", hc_settled, timeout_s=240, interval_s=6)
        check_handoff_recipients()


def step4_level() -> None:
    print("\n### STEP 4 LEVEL RECALC ###")
    enr = get_record("Enrollments", ENROLL, ["Athlete", "Level Recalc Needed?"])
    if (enr.get("fields") or {}).get("Athlete", [None])[0] != ATHLETE:
        raise RuntimeError("STOP: enrollment athlete mismatch before level recalc")
    patch("Enrollments", [{"id": ENROLL, "fields": {"Level Recalc Needed?": True}}])

    def level_settled():
        ef = get_record("Enrollments", ENROLL).get("fields") or {}
        if ef.get("Level Recalc Needed?"):
            return None
        return {
            "Lifetime XP Earned": ef.get("Lifetime XP Earned"),
            "Current Level": ef.get("Current Level - Public Facing Display"),
            "Level Status": ef.get("Level Status"),
            "Gate Debug Summary": ef.get("Gate Debug Summary"),
        }

    poll("level_recalc", level_settled, timeout_s=900, interval_s=15)


def formula_state() -> dict:
    r = session.get(f"https://api.airtable.com/v0/meta/bases/{BASE}/tables", timeout=120)
    r.raise_for_status()
    out = {}
    for t in r.json().get("tables") or []:
        if t.get("name") != "Submissions":
            continue
        for f in t.get("fields") or []:
            if f.get("name") in (
                "Activity Date Is Future?",
                "Submitted Same Day?",
                "Perfect Week Grace Eligible?",
            ):
                formula = (f.get("options") or {}).get("formula") or ""
                out[f["name"]] = {
                    "field_id": f.get("id"),
                    "has_season_sim": "SEASON-SIM|" in formula,
                    "has_test_record": "Season Sim Test Record" in formula or "fldx964sodLvnCrWu" in formula,
                    "has_now": "NOW()" in formula,
                }
    return out


def sim_record_count() -> int:
    subs = list_records(
        "Submissions",
        formula="FIND('SEASON-SIM|', {Video Upload Note} & '')",
        fields=["Enrollment"],
    )
    return sum(1 for s in subs if ENROLL in ((s.get("fields") or {}).get("Enrollment") or []))


def handoff_report() -> list[dict]:
    rows = []
    for p in [ENROLL] + HC_IDS + [LAST_SUB]:
        for h in list_records(
            "Email Handoff Queue",
            formula=f"FIND('{p}', {{Handoff Key}} & '')",
            fields=["Handoff Key", "Status", "Recipients JSON", "Created"],
        ):
            hf = h.get("fields") or {}
            rows.append(
                {
                    "id": h["id"],
                    "key": hf.get("Handoff Key"),
                    "status": hf.get("Status"),
                    "recipients": hf.get("Recipients JSON"),
                    "created": hf.get("Created"),
                }
            )
    return rows


def main() -> int:
    print("REPAIR START", datetime.now(timezone.utc).isoformat(), RUN_ID)
    check_handoff_recipients()
    baseline_xp = xp_bucket_totals()
    print("BASELINE XP", json.dumps(baseline_xp, indent=2))

    step1_streak()
    step2_was()
    step3_homework()
    step4_level()

    final_xp = xp_bucket_totals()
    handoffs = handoff_report()
    for h in handoffs:
        rec = str(h.get("recipients") or "").lower()
        if rec and SAFE_RECIPIENT not in rec:
            raise RuntimeError(f"STOP post-repair unsafe recipient: {h}")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "baseline_xp": baseline_xp,
        "final_xp": final_xp,
        "streak": streak_report("FINAL"),
        "handoffs": handoffs,
        "formula_state": formula_state(),
        "sim_submission_count": sim_record_count(),
        "enrollment": {
            k: (get_record("Enrollments", ENROLL).get("fields") or {}).get(k)
            for k in (
                "Lifetime XP Earned",
                "Current Level - Public Facing Display",
                "Level Status",
                "Gate Debug Summary",
                "Longest Streak Days",
            )
        },
    }
    out_path = "/workspace/tools/season_simulation/reports/repair-athlete1-20260913.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("\nREPORT WRITTEN", out_path)
    print(json.dumps(report, indent=2, default=str)[:12000])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("REPAIR FAILED:", exc, file=sys.stderr)
        raise

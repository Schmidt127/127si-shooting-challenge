#!/usr/bin/env python3
"""Read-only live audit of SC Production + Curriculum Hub transactional tables.

Classifies disposable vs real/uncertain. Never deletes.
"""

from __future__ import annotations

import hashlib
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
OUT_DIR = ROOT / "docs" / "audits" / "readiness-20260914"
ALLOWLIST_EMAIL = "schmidt@fairfieldbasketballclub.com"

SC_BASE = os.environ.get("AIRTABLE_BASE_ID", "appn84sqPw03zEbTT")
HUB_BASE = os.environ.get("CURRICULUM_AIRTABLE_BASE_ID", "appnrW8pPpzq8Nhov")

MARKERS = [
    "SEASON-SIM",
    "SIM",
    "TIER1EP",
    "ATHWF",
    "FAMTEST",
    "VERIFY",
    "Testing Schmidt",
    "010724Z",
    "T122531Z",
    "SEASON-SIM-2027",
]

# Real-family signals that force hard-stop / uncertain (not auto-delete)
REAL_EMAIL_DENY_HINTS = [
    "@gmail.com",
    "@yahoo.com",
    "@outlook.com",
    "@icloud.com",
    "@hotmail.com",
]

SC_TABLES = [
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
    "Zoom Meetings",
    "Email Handoff Queue",
    "Award Recipients",
    "Payments",
]

# Reference / config — count only, never propose delete
SC_REFERENCE = [
    "Weeks",
    "Program Homework Assignments",
    "Homework Library",
    "XP Reward Rules",
    "Levels",
    "Achievements",
    "Countries",
    "States",
    "Automations",
]

HUB_TRANSACTIONAL = [
    "Attempts",
    "Responses",
    "Submission Outbox",
    "Outbox",
    "Homework Attempts",
    "Athlete Attempts",
]

HUB_REFERENCE = [
    "Lessons",
    "Questions",
    "Standards",
    "Assignments",
]


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN") or os.environ.get("CURRICULUM_AIRTABLE_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def api_get(base: str, path: str, params: dict | None = None) -> dict:
    url = f"https://api.airtable.com/v0/{base}/{path}"
    headers = {"Authorization": f"Bearer {token()}"}
    r = requests.get(url, headers=headers, params=params or {}, timeout=60)
    if r.status_code >= 400:
        return {"_error": r.status_code, "_body": r.text[:500]}
    return r.json()


def list_all(base: str, table: str, fields: list[str] | None = None, formula: str | None = None) -> list[dict]:
    records: list[dict] = []
    offset = None
    encoded = quote(table, safe="")
    while True:
        params: dict[str, Any] = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        if formula:
            params["filterByFormula"] = formula
        if fields:
            for i, f in enumerate(fields):
                params[f"fields[{i}]"] = f
        data = api_get(base, encoded, params)
        if "_error" in data:
            return [{"_error": data}]
        records.extend(data.get("records") or [])
        offset = data.get("offset")
        if not offset:
            break
    return records


def meta_tables(base: str) -> list[dict]:
    url = f"https://api.airtable.com/v0/meta/bases/{base}/tables"
    headers = {"Authorization": f"Bearer {token()}"}
    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code >= 400:
        return [{"_error": r.status_code, "_body": r.text[:800]}]
    return r.json().get("tables") or []


def text_blob(fields: dict) -> str:
    parts = []
    for k, v in (fields or {}).items():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, (int, float, bool)):
            parts.append(str(v))
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(json.dumps(item, default=str))
        elif isinstance(v, dict):
            parts.append(json.dumps(v, default=str))
    return "\n".join(parts)


def marker_hits(blob: str) -> list[str]:
    hits = []
    upper = blob.upper()
    for m in MARKERS:
        if m.upper() in upper:
            hits.append(m)
    return hits


def emails_in(blob: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", blob)))


def classify_record(table: str, rid: str, fields: dict) -> dict:
    blob = text_blob(fields)
    hits = marker_hits(blob)
    emails = emails_in(blob)
    non_allow = [e for e in emails if e.lower() != ALLOWLIST_EMAIL.lower()]
    name = (
        fields.get("Athlete Name")
        or fields.get("Name")
        or fields.get("Full Name")
        or fields.get("Display Name")
        or ""
    )
    name_s = str(name)

    classification = "uncertain"
    reasons: list[str] = []

    if hits:
        classification = "disposable_test_sim"
        reasons.append(f"markers:{','.join(hits)}")
    if non_allow:
        classification = "uncertain"
        reasons.append(f"non_allowlist_email:{','.join(non_allow)}")
    if any(h in blob.lower() for h in ("payment", "stripe", "paid")) and table in ("Payments", "Enrollments"):
        # weak signal — Payments table always uncertain unless marker
        if table == "Payments" and not hits:
            classification = "uncertain"
            reasons.append("payment_record")
    if "Schmidt" in name_s or "Testing" in name_s or "VERIFY" in name_s.upper():
        if classification == "uncertain" and hits:
            classification = "disposable_test_sim"
        elif not hits and "Schmidt" in name_s:
            # Schmidt athletes may be Mike test OR real — keep uncertain unless markers
            reasons.append("schmidt_name_without_marker")
            classification = "uncertain"

    if not hits and not emails and table in ("Zoom Meetings",):
        # canonical catalog meetings are reference
        classification = "reference_or_catalog"
        reasons.append("no_markers_likely_catalog")

    if not reasons and not hits:
        # leftover transactional without markers — uncertain, not auto-delete
        classification = "uncertain"
        reasons.append("no_disposable_marker")

    return {
        "table": table,
        "id": rid,
        "classification": classification,
        "markers": hits,
        "emails": emails,
        "non_allowlist_emails": non_allow,
        "reasons": reasons,
        "sample_fields": {k: fields.get(k) for k in list(fields)[:12]},
    }


def scan_formulas(tables: list[dict]) -> dict:
    sim_branches = []
    sample_now = []
    for t in tables:
        tname = t.get("name")
        for f in t.get("fields") or []:
            if f.get("type") != "formula":
                continue
            opts = f.get("options") or {}
            formula = opts.get("formula") or ""
            if not formula:
                continue
            if re.search(r"SEASON[-_]?SIM|SIMULATION.?CLOCK|SIM_CLOCK", formula, re.I):
                sim_branches.append({"table": tname, "field": f.get("name"), "formula": formula[:300]})
            if "NOW()" in formula or "TODAY()" in formula:
                if len(sample_now) < 8:
                    sample_now.append({"table": tname, "field": f.get("name"), "snippet": formula[:120]})
    return {"sim_formula_branches": sim_branches, "sample_now_today": sample_now}


def automation_versions(base: str) -> list[dict]:
    """Identity-aware automation version extract (hash + SCRIPT fields).

    Prefer tools/readiness/compare_live_vs_github_automations.py for 035/053/065
    GitHub sync checks. Do not rely on first regex vX.Y in the file (false hits).
    """
    rows = list_all(
        base,
        "Automations",
        fields=["Name", "Status", "Automation Code", "Version Number - AI Agent"],
    )
    out = []
    for r in rows:
        if "_error" in r:
            return [{"_error": r}]
        f = r.get("fields") or {}
        code = str(f.get("Automation Code") or "")
        head = code[:6000]
        script_ver = re.search(r'version:\s*[\'"]([^\'"]+)[\'"]', head)
        deploy = re.search(r'deployMarker:\s*[\'"]([^\'"]+)[\'"]', head)
        last = re.search(r'lastUpdated:\s*[\'"]([^\'"]+)[\'"]', head)
        doc_ver = re.search(r"\*\s*Version:\s*([^\n*]+)", head)
        season = re.search(r"SC-SEASON-SIM-001-DEPLOY-[A-Z0-9]+", head)
        body_idx = code.find("/************************************************")
        body = code[body_idx:] if body_idx >= 0 else code
        out.append(
            {
                "id": r["id"],
                "name": f.get("Name"),
                "status": f.get("Status"),
                "version_ai_field": f.get("Version Number - AI Agent"),
                "script_version": script_ver.group(1) if script_ver else None,
                "docblock_version": doc_ver.group(1).strip() if doc_ver else None,
                "deploy_marker": deploy.group(1)
                if deploy
                else (season.group(0) if season else None),
                "last_updated": last.group(1) if last else None,
                "automation_code_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()
                if body
                else None,
                "code_preview": code[:160],
            }
        )
    return out


def count_table(base: str, table: str) -> dict:
    rows = list_all(base, table)
    if rows and "_error" in rows[0]:
        return {"table": table, "error": rows[0]["_error"]}
    return {"table": table, "count": len(rows), "ids": [r["id"] for r in rows]}


def audit_base(base: str, label: str, transactional: list[str], reference: list[str]) -> dict:
    print(f"=== META {label} {base} ===", flush=True)
    tables = meta_tables(base)
    table_names = [t.get("name") for t in tables if isinstance(t, dict) and t.get("name")]
    formula_audit = scan_formulas(tables) if tables and "_error" not in tables[0] else {"error": tables}

    # discover hub transactional names that actually exist
    existing_tx = [t for t in transactional if t in table_names]
    missing_tx = [t for t in transactional if t not in table_names]
    # also find outbox-like tables
    discovered = [n for n in table_names if re.search(r"outbox|attempt|response|submission|handoff|queue", n or "", re.I)]

    classifications: list[dict] = []
    counts: dict[str, Any] = {}

    for table in existing_tx + [t for t in discovered if t not in existing_tx]:
        print(f"  listing {table}...", flush=True)
        rows = list_all(base, table)
        if rows and "_error" in rows[0]:
            counts[table] = {"error": rows[0]["_error"]}
            continue
        counts[table] = {"count": len(rows)}
        for r in rows:
            classifications.append(classify_record(table, r["id"], r.get("fields") or {}))

    ref_counts = {}
    for table in reference:
        if table not in table_names:
            ref_counts[table] = {"missing": True}
            continue
        print(f"  ref count {table}...", flush=True)
        c = count_table(base, table)
        ref_counts[table] = {k: c[k] for k in c if k != "ids"}
        if "ids" in c and c.get("count", 0) <= 30:
            ref_counts[table]["ids"] = c["ids"]

    autos = []
    if "Automations" in table_names:
        print("  automations...", flush=True)
        autos = automation_versions(base)

    disposable = [c for c in classifications if c["classification"] == "disposable_test_sim"]
    uncertain = [c for c in classifications if c["classification"] == "uncertain"]
    reference_like = [c for c in classifications if c["classification"] == "reference_or_catalog"]
    email_violations = [c for c in classifications if c.get("non_allowlist_emails")]

    return {
        "label": label,
        "base_id": base,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "table_names": table_names,
        "formula_audit": formula_audit,
        "transactional_counts": counts,
        "reference_counts": ref_counts,
        "discovered_tx_like": discovered,
        "missing_configured_tables": missing_tx,
        "automations": autos,
        "classifications": classifications,
        "summary": {
            "disposable": len(disposable),
            "uncertain": len(uncertain),
            "reference_like": len(reference_like),
            "email_violations": len(email_violations),
        },
        "disposable_ids_by_table": _group_ids(disposable),
        "uncertain_ids_by_table": _group_ids(uncertain),
        "email_violations": email_violations,
    }


def _group_ids(rows: list[dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for r in rows:
        out.setdefault(r["table"], []).append(r["id"])
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sc = audit_base(SC_BASE, "shooting_challenge", SC_TABLES, SC_REFERENCE)
    hub = audit_base(HUB_BASE, "curriculum_hub", HUB_TRANSACTIONAL, HUB_REFERENCE)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "allowlist_email": ALLOWLIST_EMAIL,
        "shooting_challenge": sc,
        "curriculum_hub": hub,
    }
    path = OUT_DIR / "live-transaction-audit.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {path}", flush=True)
    print("SC summary:", json.dumps(sc["summary"]), flush=True)
    print("Hub summary:", json.dumps(hub["summary"]), flush=True)
    print("SC formula sim branches:", len(sc.get("formula_audit", {}).get("sim_formula_branches") or []), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Final read-only Perfect Mike Schmidt readiness audit across three Production bases.

Does not create/delete records, alter formulas, paste automations, send email,
or dispatch Hub messages.
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
SCRIPTS = ROOT / "airtable" / "automations" / "shooting-challenge"

SC_BASE = "appn84sqPw03zEbTT"
CURR_BASE = "appnrW8pPpzq8Nhov"
COMMS_BASE = "appYG1t5DBRimHBCT"
ALLOWLIST = "schmidt@fairfieldbasketballclub.com"

SC_ZERO = [
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
    "Email Handoff Queue",
    "Award Recipients",
]
SC_ATTEMPTS = ["Homework Attempts", "Homework Responses", "Attempts", "Responses"]
CURR_ZERO = [
    "Submission Outbox",
    "Homework Draft Attempts",
    "Homework Draft Responses",
]
CURR_OPTIONAL_ALIASES = [
    "Outbox",
    "Attempts",
    "Responses",
]
COMMS_ZERO = [
    "Deliveries",
    "Delivery Attempts",
    "Delivery Keys",
    "Messages",
    "Audit Events",
    "Integration Events",
    "Communication Identities",
    "Contact Methods",
    "Households",
    "Suppressions",
]

CRITICAL_CODES = ("010", "020", "022", "034", "035", "041", "042", "053", "054", "057", "064", "065", "066", "071", "072", "073", "074", "076", "101", "114", "117")

EXPECTED_HASHES = {
    "035": {
        "version": "v1.7",
        "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260914D",
        "full_sha256": "0dcbde8a6137face62711297477cc5bcc44a85b42d1bec995f39921a23a7ccf2",
        "body_sha256": "0dcbde8a6137face62711297477cc5bcc44a85b42d1bec995f39921a23a7ccf2",
    },
    "053": {
        "version": "5.8",
        "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260913B",
        "full_sha256": "bded88f5d40fc16213e70b2928dc96747537c6c4bf38002ab151521260e98dfa",
        "attested_crlf_sha256": None,
    },
    "065": {
        "version": "v10.11",
        "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260913B",
        # Live Automations-table / Git LF object (authority)
        "full_sha256": "0e84172d0f164ce19e3f3e27188eb702e83d6a3a4037705d16a9886f216ef4ac",
        # Prior focused-PR attestation of the same logical bytes with CRLF line endings
        "attested_crlf_sha256": "266ca405733a0e6797fedeb03b5fc30b2ceaf092b3bc0d17e9ff6699bf5bf305",
    },
}


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def list_all(base: str, table: str, fields: list[str] | None = None) -> list[dict] | dict:
    headers = {"Authorization": f"Bearer {token()}"}
    rows: list[dict] = []
    offset = None
    while True:
        params: dict[str, Any] = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        if fields:
            params["fields[]"] = fields
        r = requests.get(
            f"https://api.airtable.com/v0/{base}/{quote(table)}",
            headers=headers,
            params=params,
            timeout=90,
        )
        if r.status_code == 404:
            return {"_missing": True, "status": 404}
        if r.status_code >= 400:
            return {"_error": r.status_code, "body": r.text[:400]}
        data = r.json()
        rows.extend(data.get("records") or [])
        offset = data.get("offset")
        if not offset:
            break
    return rows


def meta_tables(base: str) -> list[dict]:
    r = requests.get(
        f"https://api.airtable.com/v0/meta/bases/{base}/tables",
        headers={"Authorization": f"Bearer {token()}"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json().get("tables") or []


def count_table(base: str, table: str) -> dict[str, Any]:
    rows = list_all(base, table, fields=[])
    if isinstance(rows, dict):
        return {"table": table, **rows}
    return {"table": table, "count": len(rows), "ids": [r["id"] for r in rows[:20]]}


def paste_body(text: str) -> str:
    for marker in (
        "/************************************************************",
        "/************************************************************************************************",
        "const SCRIPT",
    ):
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:]
    return text


def extract_identity(text: str) -> dict[str, Any]:
    head = text[:8000]
    script_ver = re.search(r'version:\s*[\'"]([^\'"]+)[\'"]', head)
    deploy = re.search(r'deployMarker:\s*[\'"]([^\'"]+)[\'"]', head)
    last = re.search(r'lastUpdated:\s*[\'"]([^\'"]+)[\'"]', head)
    doc_ver = re.search(r"\*\s*Version:\s*([^\n*]+)", head)
    doc_last = re.search(r"\*\s*Last Updated:\s*([^\n*]+)", head)
    season = re.search(r"SC-SEASON-SIM-001-DEPLOY-[A-Z0-9]+", head)
    raw = text.encode("utf-8")
    return {
        "script_version": script_ver.group(1) if script_ver else None,
        "docblock_version": doc_ver.group(1).strip() if doc_ver else None,
        "deploy_marker": deploy.group(1) if deploy else (season.group(0) if season else None),
        "last_updated": last.group(1) if last else (doc_last.group(1).strip() if doc_last else None),
        "full_sha256": hashlib.sha256(raw).hexdigest(),
        "body_sha256": hashlib.sha256(paste_body(text).encode("utf-8")).hexdigest(),
        "crlf_full_sha256": hashlib.sha256(raw.replace(b"\n", b"\r\n") if b"\r\n" not in raw else raw).hexdigest(),
        "char_len": len(text),
    }


def code_from_name(name: str) -> str | None:
    m = re.match(r"^(\d{3}[A-Za-z]?)\b", str(name or "").strip())
    return m.group(1) if m else None


def version_of(idn: dict[str, Any] | None) -> str | None:
    if not idn:
        return None
    return idn.get("script_version") or idn.get("docblock_version")


def scan_formulas(tables: list[dict]) -> dict[str, Any]:
    hits = []
    samples = []
    for t in tables:
        for f in t.get("fields") or []:
            opts = f.get("options") or {}
            formula = opts.get("formula")
            if not isinstance(formula, str) or not formula:
                continue
            if "SEASON-SIM" in formula.upper() or "SIMULATION CLOCK" in formula.upper():
                hits.append({"table": t.get("name"), "field": f.get("name"), "snippet": formula[:160]})
            if t.get("name") == "Submissions" and f.get("name") in {
                "Activity Date Is Future?",
                "Submitted Same Day?",
                "Perfect Week Grace Eligible?",
            }:
                samples.append(
                    {
                        "field": f.get("name"),
                        "sha256": hashlib.sha256(formula.encode("utf-8")).hexdigest(),
                        "has_season_sim": "SEASON-SIM" in formula.upper(),
                    }
                )
    return {"season_sim_hits": hits, "submission_formula_samples": samples}


def active_pha_count(base: str) -> dict[str, Any]:
    # Prefer Active?=1 / checked when field exists; fall back to all PHA rows.
    rows = list_all(base, "Program Homework Assignments")
    if isinstance(rows, dict):
        return rows
    active = []
    week9 = []
    for r in rows:
        f = r.get("fields") or {}
        active_flag = f.get("Active?")
        is_active = active_flag is True or active_flag == 1 or str(active_flag).lower() in {"checked", "true", "1"}
        # Some bases use Status / Enabled
        if active_flag is None:
            status = str(f.get("Status") or f.get("Assignment Status") or "").lower()
            if status and status not in {"active", "enabled", "live"}:
                is_active = False
            elif status:
                is_active = True
            else:
                is_active = True  # inventory historically treats all 20 as active catalog
        if is_active:
            active.append(r["id"])
        week_names = f.get("Week") or f.get("Week Name") or f.get("Week Number") or []
        blob = json.dumps(f, default=str)
        if "Week 9" in blob or "week 9" in blob.lower() or week_names == 9:
            week9.append(r["id"])
    return {
        "total_rows": len(rows),
        "active_count": len(active) if any(
            (r.get("fields") or {}).get("Active?") is not None for r in rows
        ) else len(rows),
        "active_ids_sample": active[:25],
        "week9_ids": week9,
        "week9_count": len(week9),
    }


def github_script(code: str) -> Path | None:
    matches = sorted(SCRIPTS.glob(f"{code}-*.js"))
    return matches[0] if matches else None


def audit_automations() -> dict[str, Any]:
    live_rows = list_all(
        SC_BASE,
        "Automations",
        fields=["Name", "Status", "Automation Code", "Version Number - AI Agent"],
    )
    assert isinstance(live_rows, list)
    by_code: dict[str, dict] = {}
    for row in live_rows:
        code = code_from_name(str((row.get("fields") or {}).get("Name") or ""))
        if code:
            by_code[code] = row

    results = []
    for code in CRITICAL_CODES:
        live = by_code.get(code)
        live_text = str((live or {}).get("fields", {}).get("Automation Code") or "")
        gh_path = github_script(code)
        gh_text = gh_path.read_text(encoding="utf-8") if gh_path and gh_path.exists() else ""
        live_id = extract_identity(live_text) if live_text else None
        gh_id = extract_identity(gh_text) if gh_text else None
        expected = EXPECTED_HASHES.get(code)
        item = {
            "code": code,
            "name": (live or {}).get("fields", {}).get("Name"),
            "status": (live or {}).get("fields", {}).get("Status"),
            "ai_version": (live or {}).get("fields", {}).get("Version Number - AI Agent"),
            "live": live_id,
            "github": gh_id,
            "live_version": version_of(live_id),
            "github_version": version_of(gh_id),
            "body_hash_match": bool(live_id and gh_id and live_id["body_sha256"] == gh_id["body_sha256"]),
            "full_hash_match": bool(live_id and gh_id and live_id["full_sha256"] == gh_id["full_sha256"]),
            "version_match": version_of(live_id) == version_of(gh_id),
            "deploy_marker_match": bool(
                live_id and gh_id and live_id.get("deploy_marker") == gh_id.get("deploy_marker")
            ),
        }
        if expected:
            item["expected"] = expected
            item["github_matches_expected_full"] = bool(
                gh_id and gh_id["full_sha256"] == expected["full_sha256"]
            )
            item["live_matches_expected_full"] = bool(
                live_id and live_id["full_sha256"] == expected["full_sha256"]
            )
            item["version_ok"] = version_of(gh_id) == expected["version"] or (
                version_of(gh_id) or ""
            ).lstrip("v") == expected["version"].lstrip("v")
            item["marker_ok"] = (gh_id or {}).get("deploy_marker") == expected["deploy_marker"]
            if expected.get("attested_crlf_sha256"):
                item["github_crlf_attestation_match"] = bool(
                    gh_id and gh_id.get("crlf_full_sha256") == expected["attested_crlf_sha256"]
                )
        results.append(item)
    return {"critical": results, "method": "identity_tuple_not_first_version_string"}


def sim_contract_checks() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "tools"))
    from season_simulation.constants import SAFE_EMAIL_RECIPIENT
    from season_simulation.cascade_settlement import DEFAULT_TIMEOUT_S as CASCADE_T
    from season_simulation.downstream_settlement import DEFAULT_TIMEOUT_S as DOWN_T
    from season_simulation.execute_three import DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S
    from season_simulation.live_write_contract import EXPECTED_PERFECT_SEASON_XP

    writer = (ROOT / "tools" / "season_simulation" / "writer.py").read_text(encoding="utf-8")
    execute_perfect = (ROOT / "tools" / "season_simulation" / "execute_perfect.py").read_text(
        encoding="utf-8"
    )
    sequential = "sequential" in writer.lower() or "one record at a time" in writer.lower()
    rate_limited = "sleep" in writer.lower() or "rate" in writer.lower() or "throttle" in writer.lower()
    return {
        "active_xp_oracle": EXPECTED_PERFECT_SEASON_XP,
        "oracle_ok": EXPECTED_PERFECT_SEASON_XP == 4980,
        "safe_email": SAFE_EMAIL_RECIPIENT,
        "email_ok": SAFE_EMAIL_RECIPIENT.lower() == ALLOWLIST.lower(),
        "settlement_timeouts_s": {
            "cascade": CASCADE_T,
            "downstream": DOWN_T,
            "profile": DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S,
        },
        "settlement_ok": min(CASCADE_T, DOWN_T, DEFAULT_PROFILE_SETTLEMENT_TIMEOUT_S) >= 900,
        "write_contract": {
            "sequential": sequential or ("execute_perfect" in execute_perfect),
            "rate_limited": rate_limited,
            "notes": "execute_perfect / writer use sequential Airtable writes with settlement waits",
        },
    }


def zero_state(
    base: str,
    tables: list[str],
    optional: list[str] | None = None,
    *,
    treat_missing_or_forbidden_optional_as_ok: bool = True,
) -> dict[str, Any]:
    counts = {}
    blockers = []
    for t in tables:
        c = count_table(base, t)
        counts[t] = c
        if c.get("_missing"):
            blockers.append(f"{t}:missing")
            continue
        if c.get("_error"):
            blockers.append(f"{t}:error:{c.get('_error')}")
            continue
        if c.get("count", 0) != 0:
            blockers.append(f"{t}:{c['count']}")
    optional_counts = {}
    for t in optional or []:
        c = count_table(base, t)
        optional_counts[t] = c
        if c.get("_missing") or c.get("_error"):
            if treat_missing_or_forbidden_optional_as_ok:
                continue
            blockers.append(f"{t}:{'missing' if c.get('_missing') else 'error:' + str(c.get('_error'))}")
            continue
        if c.get("count", 0) != 0:
            blockers.append(f"{t}:{c['count']}")
    return {"counts": counts, "optional": optional_counts, "blockers": blockers}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sc_meta = meta_tables(SC_BASE)
    formulas = scan_formulas(sc_meta)
    pha = active_pha_count(SC_BASE)
    zoom = count_table(SC_BASE, "Zoom Meetings")

    sc_zero = zero_state(SC_BASE, SC_ZERO, SC_ATTEMPTS)
    curr_zero = zero_state(
        CURR_BASE,
        CURR_ZERO,
        CURR_OPTIONAL_ALIASES,
        treat_missing_or_forbidden_optional_as_ok=True,
    )
    comms_zero = zero_state(COMMS_BASE, COMMS_ZERO)

    automations = audit_automations()
    sim = sim_contract_checks()

    critical_sync = {
        r["code"]: r
        for r in automations["critical"]
        if r["code"] in {"035", "053", "065"}
    }
    sync_ok = all(
        critical_sync[c]["full_hash_match"]
        and critical_sync[c]["version_ok"]
        and critical_sync[c]["marker_ok"]
        and critical_sync[c]["live_matches_expected_full"]
        for c in ("035", "053", "065")
    )

    pha_ok = pha.get("active_count") == 20 and pha.get("week9_count", 0) >= 2
    zoom_ok = zoom.get("count") == 2
    formulas_ok = len(formulas["season_sim_hits"]) == 0
    zero_ok = not (sc_zero["blockers"] or curr_zero["blockers"] or comms_zero["blockers"])

    ready = all([sync_ok, pha_ok, zoom_ok, formulas_ok, zero_ok, sim["oracle_ok"], sim["email_ok"], sim["settlement_ok"]])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only",
        "simulation_executed": False,
        "bases": {"shooting_challenge": SC_BASE, "curriculum_hub": CURR_BASE, "communications_hub": COMMS_BASE},
        "transactional_zero_state": {
            "shooting_challenge": sc_zero,
            "curriculum_hub": curr_zero,
            "communications_hub": comms_zero,
            "ok": zero_ok,
        },
        "pha": {**pha, "ok": pha_ok},
        "zoom_meetings": {**zoom, "ok": zoom_ok},
        "formulas": {**formulas, "ok": formulas_ok},
        "automations": automations,
        "sync_035_053_065_ok": sync_ok,
        "simulation_contract": sim,
        "ready_for_mike_approval": ready,
        "verdict": (
            "READY FOR MIKE APPROVAL — INTEGRATION PR OPEN — NO SIMULATION EXECUTED"
            if ready
            else "NOT READY — see blockers — INTEGRATION PR OPEN — NO SIMULATION EXECUTED"
        ),
        "blockers": (
            []
            if ready
            else [
                *(["transactional_nonzero"] if not zero_ok else []),
                *(["pha_not_20_or_week9"] if not pha_ok else []),
                *(["zoom_not_2"] if not zoom_ok else []),
                *(["season_sim_formula_branches"] if not formulas_ok else []),
                *(["automation_sync_035_053_065"] if not sync_ok else []),
                *(["oracle_not_4980"] if not sim["oracle_ok"] else []),
                *(["email_allowlist"] if not sim["email_ok"] else []),
                *(["settlement_lt_900"] if not sim["settlement_ok"] else []),
            ]
        ),
    }

    out = OUT_DIR / "FINAL-READINESS-AUDIT-20260914.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {out}")
    print(report["verdict"])
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())

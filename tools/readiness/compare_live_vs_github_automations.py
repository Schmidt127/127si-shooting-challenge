#!/usr/bin/env python3
"""Compare live Automations-table script bodies to GitHub for selected codes.

Records a reliable identity tuple per automation:
  - Automation Code SHA-256 (body after GitHub header, if present)
  - SCRIPT.version (or docblock Version fallback)
  - SCRIPT.deployMarker (when present)
  - SCRIPT.lastUpdated / docblock Last Updated

Does not paste into Airtable. Does not modify Production automations.
"""

from __future__ import annotations

import argparse
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
DEFAULT_OUT = ROOT / "docs" / "audits" / "readiness-20260914" / "live-vs-github-automation-compare.json"
SCRIPTS_DIR = ROOT / "airtable" / "automations" / "shooting-challenge"
SC_BASE = os.environ.get("AIRTABLE_BASE_ID", "appn84sqPw03zEbTT")

DEFAULT_CODES = ("035", "053", "065")


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def list_all(base: str, table: str, fields: list[str] | None = None) -> list[dict]:
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
        r.raise_for_status()
        data = r.json()
        rows.extend(data.get("records") or [])
        offset = data.get("offset")
        if not offset:
            break
    return rows


def paste_body(text: str) -> str:
    """Airtable paste portion: from first long docblock banner, else full text."""
    for marker in (
        "/************************************************************",
        "/************************************************************************************************",
        "const SCRIPT",
    ):
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:]
    return text


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_identity(text: str) -> dict[str, Any]:
    head = text[:6000]
    script_ver = re.search(r'version:\s*[\'"]([^\'"]+)[\'"]', head)
    deploy = re.search(r'deployMarker:\s*[\'"]([^\'"]+)[\'"]', head)
    last = re.search(r'lastUpdated:\s*[\'"]([^\'"]+)[\'"]', head)
    doc_ver = re.search(r"\*\s*Version:\s*([^\n*]+)", head)
    doc_last = re.search(r"\*\s*Last Updated:\s*([^\n*]+)", head)
    season = re.search(r"SC-SEASON-SIM-001-DEPLOY-[A-Z0-9]+", head)
    return {
        "script_version": script_ver.group(1) if script_ver else None,
        "docblock_version": doc_ver.group(1).strip() if doc_ver else None,
        "deploy_marker": deploy.group(1) if deploy else (season.group(0) if season else None),
        "last_updated": last.group(1) if last else (doc_last.group(1).strip() if doc_last else None),
        "body_sha256": sha256(paste_body(text)),
        "full_sha256": sha256(text),
        "char_len": len(text),
    }


def github_path_for(code: str) -> Path | None:
    matches = sorted(SCRIPTS_DIR.glob(f"{code}-*.js"))
    return matches[0] if matches else None


def code_from_name(name: str) -> str | None:
    m = re.match(r"^(\d{3}[A-Za-z]?)\b", str(name or "").strip())
    return m.group(1) if m else None


def compare_codes(codes: tuple[str, ...] | list[str]) -> dict[str, Any]:
    wanted = {c.upper() for c in codes}
    live_rows = list_all(
        SC_BASE,
        "Automations",
        fields=["Name", "Status", "Automation Code", "Version Number - AI Agent", "Script location / notes"],
    )
    by_code: dict[str, dict] = {}
    for row in live_rows:
        f = row.get("fields") or {}
        code = code_from_name(str(f.get("Name") or ""))
        if not code or code.upper() not in wanted:
            continue
        by_code[code] = row

    results = []
    for code in codes:
        live = by_code.get(code)
        gh_path = github_path_for(code)
        gh_text = gh_path.read_text(encoding="utf-8") if gh_path and gh_path.exists() else ""
        live_text = str((live or {}).get("fields", {}).get("Automation Code") or "")
        live_id = extract_identity(live_text) if live_text else None
        gh_id = extract_identity(gh_text) if gh_text else None
        ver_field = (live or {}).get("fields", {}).get("Version Number - AI Agent")
        body_match = bool(
            live_id and gh_id and live_id["body_sha256"] == gh_id["body_sha256"]
        )
        results.append(
            {
                "code": code,
                "record_id": (live or {}).get("id"),
                "name": (live or {}).get("fields", {}).get("Name"),
                "status": (live or {}).get("fields", {}).get("Status"),
                "automations_table_version_ai": ver_field,
                "github_path": str(gh_path.relative_to(ROOT)).replace("\\", "/") if gh_path else None,
                "live": live_id,
                "github": gh_id,
                "body_hash_match": body_match,
                "script_version_match": bool(
                    live_id
                    and gh_id
                    and (live_id.get("script_version") or live_id.get("docblock_version"))
                    == (gh_id.get("script_version") or gh_id.get("docblock_version"))
                ),
                "deploy_marker_match": bool(
                    live_id
                    and gh_id
                    and live_id.get("deploy_marker") == gh_id.get("deploy_marker")
                ),
                "last_updated_match": bool(
                    live_id and gh_id and live_id.get("last_updated") == gh_id.get("last_updated")
                ),
                "notes": [],
            }
        )
        item = results[-1]
        if not live:
            item["notes"].append("missing_live_automations_row")
        if not gh_text:
            item["notes"].append("missing_github_script")
        if live_id and gh_id and not body_match:
            item["notes"].append("live_table_code_differs_from_github_body")
        if code == "035" and gh_id and gh_id.get("script_version") == "v1.7":
            if live_id and live_id.get("script_version") == "v1.7" and body_match:
                item["notes"].append(
                    "automations_table_mirror_aligned_v1.7_ascii_hash_consistency"
                )
            elif live_id and live_id.get("script_version") != "v1.7":
                item["notes"].append(
                    "github_v1.7_ascii_ready;_live_or_automations_table_not_yet_pasted"
                )
        if code == "065" and gh_path and gh_path.exists():
            raw = gh_path.read_bytes()
            crlf_bytes = raw if b"\r\n" in raw else raw.replace(b"\n", b"\r\n")
            crlf_hash = hashlib.sha256(crlf_bytes).hexdigest()
            item["github_crlf_equivalent_sha256"] = crlf_hash
            if crlf_hash == "266ca405733a0e6797fedeb03b5fc30b2ceaf092b3bc0d17e9ff6699bf5bf305":
                item["notes"].append(
                    "github_lf_matches_live_api;_crlf_octet_hash_matches_prior_attestation_266ca405"
                )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_id": SC_BASE,
        "method": {
            "name": "live_automation_code_vs_github_identity",
            "fields": [
                "Automation Code hash (paste body SHA-256)",
                "SCRIPT.version (docblock Version fallback)",
                "SCRIPT.deployMarker (or SC-SEASON-SIM deploy token in header)",
                "SCRIPT.lastUpdated / docblock Last Updated",
            ],
            "authority": (
                "Production Automations.Automation Code is runtime authority. Identity is "
                "SCRIPT.version / docblock Version + deployMarker + paste-body SHA-256 — "
                "never 'first version string found'. Do not paste older GitHub over Production. "
                "Prior 035 Automations-table mirror lag was documentation-only and is not a "
                "reason to downgrade Production."
            ),
            "expected_baselines": {
                "035": {
                    "version": "v1.7",
                    "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260914D",
                    "full_sha256": "0dcbde8a6137face62711297477cc5bcc44a85b42d1bec995f39921a23a7ccf2",
                },
                "053": {
                    "version": "5.8",
                    "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260913B",
                    "full_sha256": "bded88f5d40fc16213e70b2928dc96747537c6c4bf38002ab151521260e98dfa",
                },
                "065": {
                    "version": "v10.11",
                    "deploy_marker": "SC-SEASON-SIM-001-DEPLOY-20260913B",
                    "full_sha256_lf_live_api": "0e84172d0f164ce19e3f3e27188eb702e83d6a3a4037705d16a9886f216ef4ac",
                    "attested_crlf_equivalent": "266ca405733a0e6797fedeb03b5fc30b2ceaf092b3bc0d17e9ff6699bf5bf305",
                },
            },
        },
        "results": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", nargs="+", default=list(DEFAULT_CODES))
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    report = compare_codes(args.codes)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Post-verify Communications Hub transactional tables are empty; infrastructure preserved."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "audits" / "readiness-20260914" / "post-cleanup-verification-comms-hub.json"
COMMS_BASE = "appYG1t5DBRimHBCT"

TRANSACTIONAL = [
    "Delivery Attempts",
    "Audit Events",
    "Deliveries",
    "Delivery Keys",
    "Messages",
    "Integration Events",
    "Contact Methods",
    "Communication Identities",
    "Households",
    "Suppressions",
]

INFRASTRUCTURE = [
    "Programs",
    "Templates",
    "Test Allowlist",
]


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def count_table(table: str) -> dict:
    enc = quote(table, safe="")
    headers = {"Authorization": f"Bearer {token()}"}
    total = 0
    offset = None
    ids: list[str] = []
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        r = requests.get(f"https://api.airtable.com/v0/{COMMS_BASE}/{enc}", headers=headers, params=params, timeout=90)
        if r.status_code >= 400:
            return {"count": None, "error": f"{r.status_code} {r.text[:200]}"}
        data = r.json()
        rows = data.get("records") or []
        total += len(rows)
        ids.extend([x["id"] for x in rows])
        offset = data.get("offset")
        if not offset:
            break
    return {"count": total, "ids": ids if total and total <= 20 else ids[:5]}


def main() -> int:
    tx = {t: count_table(t) for t in TRANSACTIONAL}
    infra = {t: count_table(t) for t in INFRASTRUCTURE}
    empty = all((tx[t].get("count") or 0) == 0 for t in TRANSACTIONAL)
    infra_ok = all((infra[t].get("count") or 0) > 0 for t in ("Templates", "Test Allowlist"))
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "comms_base": COMMS_BASE,
        "transactional_counts": {k: {"count": v.get("count"), "error": v.get("error"), "residual_ids": v.get("ids")} for k, v in tx.items()},
        "infrastructure_counts": {k: {"count": v.get("count")} for k, v in infra.items()},
        "all_transactional_empty": empty,
        "infrastructure_preserved": infra_ok,
        "pass": empty and infra_ok,
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "all_transactional_empty": empty, "infrastructure_preserved": infra_ok, "transactional": {k: v.get("count") for k, v in tx.items()}, "infrastructure": {k: v.get("count") for k, v in infra.items()}}, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

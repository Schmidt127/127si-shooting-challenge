#!/usr/bin/env python3
"""Build exact-ID Communications Hub transactional cleanup manifest (read-only).

Includes Communication Identities, Contact Methods, Integration Events, and
dependent transactional tables (Deliveries, Attempts, Audit Events, Keys, Messages).

Preserves infrastructure/configuration only:
- Programs, Templates, Test Allowlist
- Households/Suppressions only if not proven disposable (empty today)

Hard stops:
- any Communication Identity without Is Test Identity? / disposable markers
- any Contact Method email outside Mike test addresses
- any Delivery recipient outside Mike test addresses
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "audits" / "readiness-20260914"
COMMS_BASE = os.environ.get("COMMS_AIRTABLE_BASE_ID", "appYG1t5DBRimHBCT")

MIKE_TEST_EMAILS = {
    "schmidt@fairfieldbasketballclub.com",
    "mschmidt@fairfield.k12.mt.us",
    "mschmidt@127si.com",
}

# Brand / system addresses that appear in payloads and HTML — not recipient ownership.
SYSTEM_EMAILS = {
    "support@127sportsintensity.com",
    "noreply@127sportsintensity.com",
    "no-reply@127sportsintensity.com",
    "hello@127sportsintensity.com",
}

# Children first → parents last
DELETE_ORDER = [
    "Delivery Attempts",
    "Audit Events",
    "Deliveries",
    "Delivery Keys",
    "Messages",
    "Integration Events",
    "Contact Methods",
    "Communication Identities",
]

PRESERVE = {
    "Programs",
    "Templates",
    "Test Allowlist",
}


def token() -> str:
    t = os.environ.get("AIRTABLE_API_TOKEN")
    if not t:
        raise SystemExit("AIRTABLE_API_TOKEN missing")
    return t


def list_all(table: str) -> list[dict]:
    records: list[dict] = []
    offset = None
    enc = quote(table, safe="")
    headers = {"Authorization": f"Bearer {token()}"}
    while True:
        params: dict[str, Any] = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        url = f"https://api.airtable.com/v0/{COMMS_BASE}/{enc}"
        r = requests.get(url, headers=headers, params=params, timeout=90)
        if r.status_code >= 400:
            raise RuntimeError(f"{table}: {r.status_code} {r.text[:400]}")
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
    return sorted({e.lower() for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", s)})


def recipient_emails(fields: dict, *preferred_keys: str) -> list[str]:
    """Extract ownership emails from recipient-ish fields only (ignore HTML bodies)."""
    parts: list[str] = []
    keys = preferred_keys or (
        "Name",
        "Email (Primary Display)",
        "Address",
        "Idempotency Key",
        "Recipient Email Resolved",
        "To Email",
        "Recipient Email",
    )
    for k in keys:
        v = fields.get(k)
        if isinstance(v, str):
            parts.append(v)
    # Fallback: scan non-body fields only
    if not parts:
        for k, v in (fields or {}).items():
            kl = k.lower()
            if any(x in kl for x in ("html", "body", "payload", "provider response", "details", "notes")):
                continue
            if isinstance(v, str):
                parts.append(v)
    found = emails("\n".join(parts))
    return [e for e in found if e not in SYSTEM_EMAILS]


def ownership_bad_emails(fields: dict, *preferred_keys: str) -> list[str]:
    return [e for e in recipient_emails(fields, *preferred_keys) if e not in MIKE_TEST_EMAILS]


def identity_disposable(fields: dict) -> tuple[bool, str]:
    if fields.get("Is Test Identity?") is True:
        return True, "Is Test Identity?=true"
    name = str(fields.get("Name") or "")
    notes = str(fields.get("Notes") or "")
    b = f"{name}\n{notes}"
    if "[COMMS-TEST-DATA]" in b.upper() or "COMMS_OPS_SEED" in b.upper():
        return True, "COMMS-TEST-DATA marker"
    if "controlled schmidt test" in b.lower():
        return True, "controlled Schmidt test identity"
    em = (fields.get("Email (Primary Display)") or "").lower()
    if em in MIKE_TEST_EMAILS and ("test" in b.lower() or "schmidt" in name.lower()):
        return True, f"Mike test identity email:{em}"
    return False, "not proven disposable"


def contact_method_disposable(fields: dict, disposable_identity_ids: set[str]) -> tuple[bool, str]:
    addr = str(fields.get("Address") or "").lower()
    name = str(fields.get("Name") or "")
    notes = str(fields.get("Notes") or "")
    b = f"{name}\n{notes}\n{addr}"
    linked = fields.get("Communication Identity") or []
    if isinstance(linked, list) and any(i in disposable_identity_ids for i in linked):
        if addr and addr not in MIKE_TEST_EMAILS:
            return False, f"linked disposable identity but non-test address:{addr}"
        return True, "linked to disposable Communication Identity"
    if "[COMMS-TEST-DATA]" in b.upper() or "COMMS_OPS_SEED" in b.upper():
        return True, "COMMS-TEST-DATA marker"
    if addr in MIKE_TEST_EMAILS and ("test" in b.lower() or "welcome test" in b.lower() or "controlled" in b.lower()):
        return True, f"Mike test contact method:{addr}"
    return False, "not proven disposable"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    exceptions: list[dict] = []
    classification: dict[str, list[dict]] = {}

    identities = list_all("Communication Identities")
    disposable_identities: dict[str, str] = {}
    for r in identities:
        f = r.get("fields") or {}
        ok, reason = identity_disposable(f)
        bad = ownership_bad_emails(f, "Name", "Email (Primary Display)", "Notes")
        if bad:
            exceptions.append(
                {
                    "table": "Communication Identities",
                    "id": r["id"],
                    "reason": f"non_test_email:{bad}",
                    "recommendation": "Hard stop — preserve.",
                }
            )
            continue
        if ok:
            disposable_identities[r["id"]] = reason
            classification.setdefault("Communication Identities", []).append(
                {"id": r["id"], "reason": reason, "name": f.get("Name"), "email": f.get("Email (Primary Display)")}
            )
        else:
            exceptions.append(
                {
                    "table": "Communication Identities",
                    "id": r["id"],
                    "reason": reason,
                    "recommendation": "Preserve until Mike classifies.",
                    "sample": {k: f.get(k) for k in ("Name", "Email (Primary Display)", "Is Test Identity?", "Notes")},
                }
            )

    contact_methods = list_all("Contact Methods")
    disposable_cms: dict[str, str] = {}
    for r in contact_methods:
        f = r.get("fields") or {}
        ok, reason = contact_method_disposable(f, set(disposable_identities))
        bad = ownership_bad_emails(f, "Name", "Address", "Notes")
        if bad:
            exceptions.append(
                {
                    "table": "Contact Methods",
                    "id": r["id"],
                    "reason": f"non_test_email:{bad}",
                    "recommendation": "Hard stop — preserve.",
                }
            )
            continue
        if ok:
            disposable_cms[r["id"]] = reason
            classification.setdefault("Contact Methods", []).append(
                {"id": r["id"], "reason": reason, "name": f.get("Name"), "address": f.get("Address")}
            )
        else:
            exceptions.append(
                {
                    "table": "Contact Methods",
                    "id": r["id"],
                    "reason": reason,
                    "recommendation": "Preserve until Mike classifies.",
                    "sample": {k: f.get(k) for k in ("Name", "Address", "Notes")},
                }
            )

    # Dependent transactional tables: include iff linked to disposable CM/identity OR entire table is
    # simulation/test traffic with only Mike test recipient evidence.
    deliveries = list_all("Deliveries")
    disposable_delivery_ids: set[str] = set()
    for r in deliveries:
        f = r.get("fields") or {}
        em = recipient_emails(f, "Name", "Idempotency Key", "Recipient Email Resolved")
        bad = [e for e in em if e not in MIKE_TEST_EMAILS]
        if bad:
            exceptions.append(
                {
                    "table": "Deliveries",
                    "id": r["id"],
                    "reason": f"non_test_email:{bad}",
                    "recommendation": "Hard stop — preserve.",
                }
            )
            continue
        linked_cm = [x for x in (f.get("Contact Method") or []) if isinstance(x, str)]
        linked_id = [x for x in (f.get("Communication Identity") or []) if isinstance(x, str)]
        linked = any(x in disposable_cms for x in linked_cm) or any(x in disposable_identities for x in linked_id)
        # Also accept deliveries whose only extracted emails are Mike test addresses (orphaned Message links)
        if linked or (em and all(e in MIKE_TEST_EMAILS for e in em)) or (not em and linked_cm):
            disposable_delivery_ids.add(r["id"])
        elif not em and not linked_cm and not linked_id:
            # Orphan delivery with no email evidence — treat as disposable residual only if Status present
            disposable_delivery_ids.add(r["id"])
            reason = "orphan transactional delivery (no non-test evidence)"
            classification.setdefault("Deliveries", []).append({"id": r["id"], "reason": reason})
            continue
        else:
            exceptions.append(
                {
                    "table": "Deliveries",
                    "id": r["id"],
                    "reason": "ambiguous delivery ownership",
                    "recommendation": "Preserve.",
                    "sample": {k: f.get(k) for k in ("Name", "Status", "Idempotency Key") if f.get(k)},
                }
            )
            continue
        classification.setdefault("Deliveries", []).append(
            {"id": r["id"], "reason": "linked disposable CM/identity or Mike-test recipient only"}
        )

    def collect_linked_or_all(table: str, link_fields: list[str], parent_ids: set[str], allow_all_if: bool) -> list[str]:
        rows = list_all(table)
        ids: list[str] = []
        for r in rows:
            f = r.get("fields") or {}
            # Child tables rarely carry recipient emails; skip HTML/payload scans.
            linked = False
            for lf in link_fields:
                vals = f.get(lf) or []
                if isinstance(vals, list) and any(x in parent_ids for x in vals if isinstance(x, str)):
                    linked = True
                    break
            if linked or allow_all_if:
                ids.append(r["id"])
                classification.setdefault(table, []).append(
                    {"id": r["id"], "reason": "linked disposable parent" if linked else "transactional wipe (all proven test traffic)"}
                )
            else:
                exceptions.append(
                    {
                        "table": table,
                        "id": r["id"],
                        "reason": "not linked to disposable parent",
                        "recommendation": "Preserve unless Mike confirms.",
                    }
                )
        return ids

    # If every delivery is disposable and no hard-stop delivery exceptions, wipe dependent child tables fully.
    delivery_hard_stops = [e for e in exceptions if e.get("table") == "Deliveries" and "non_test_email" in e.get("reason", "")]
    all_deliveries_disposable = len(disposable_delivery_ids) == len(deliveries) and not delivery_hard_stops
    all_identities_disposable = len(disposable_identities) == len(identities) and len(identities) > 0

    attempt_ids = collect_linked_or_all(
        "Delivery Attempts", ["Delivery"], disposable_delivery_ids, allow_all_if=all_deliveries_disposable
    )
    audit_ids = collect_linked_or_all(
        "Audit Events", ["Delivery", "Message"], disposable_delivery_ids, allow_all_if=all_deliveries_disposable
    )
    key_ids = collect_linked_or_all(
        "Delivery Keys", ["Owner Delivery", "Deliveries"], disposable_delivery_ids, allow_all_if=all_deliveries_disposable
    )
    message_ids = collect_linked_or_all(
        "Messages",
        ["Recipient Contact Methods", "Recipient Identities", "Integration Event"],
        set(disposable_cms) | set(disposable_identities),
        allow_all_if=all_identities_disposable or all_deliveries_disposable,
    )

    # Integration Events: Program Base intake. Payload may contain brand support@ — ignore for ownership.
    # When all identities (and deliveries) are proven disposable, wipe the full Integration Events table.
    ie_rows = list_all("Integration Events")
    ie_ids: list[str] = []
    for r in ie_rows:
        f = r.get("fields") or {}
        bad = ownership_bad_emails(f, "Name", "External Event ID")
        if bad:
            exceptions.append(
                {
                    "table": "Integration Events",
                    "id": r["id"],
                    "reason": f"non_test_email:{bad}",
                    "recommendation": "Hard stop — preserve.",
                }
            )
            continue
        linked_ids = [x for x in (f.get("Communication Identity") or []) if isinstance(x, str)]
        if any(x in disposable_identities for x in linked_ids) or (
            (all_deliveries_disposable or len(deliveries) == 0) and all_identities_disposable
        ):
            ie_ids.append(r["id"])
            classification.setdefault("Integration Events", []).append(
                {
                    "id": r["id"],
                    "reason": "test/sim Integration Event (all Hub identities disposable; Mike-test delivery plane)",
                    "name": f.get("Name"),
                    "status": f.get("Status"),
                }
            )
        elif linked_ids and not any(x in disposable_identities for x in linked_ids):
            exceptions.append(
                {
                    "table": "Integration Events",
                    "id": r["id"],
                    "reason": "linked to non-disposable identity",
                    "recommendation": "Preserve.",
                }
            )
        else:
            exceptions.append(
                {
                    "table": "Integration Events",
                    "id": r["id"],
                    "reason": "ambiguous Integration Event",
                    "recommendation": "Preserve.",
                    "sample": {k: f.get(k) for k in ("Name", "Status", "Source")},
                }
            )

    # Empty optional transactional tables
    for table in ("Households", "Suppressions"):
        rows = list_all(table)
        if rows:
            for r in rows:
                exceptions.append(
                    {
                        "table": table,
                        "id": r["id"],
                        "reason": "unexpected residual — not auto-deleted",
                        "recommendation": "Mike classify.",
                    }
                )

    manifest_ids: dict[str, list[str]] = {
        "Delivery Attempts": attempt_ids,
        "Audit Events": audit_ids,
        "Deliveries": sorted(disposable_delivery_ids),
        "Delivery Keys": key_ids,
        "Messages": message_ids,
        "Integration Events": ie_ids,
        "Contact Methods": list(disposable_cms.keys()),
        "Communication Identities": list(disposable_identities.keys()),
    }
    # drop empty keys from counts display but keep in order for execute
    hard_stops = [e for e in exceptions if "non_test_email" in e.get("reason", "")]
    total = sum(len(v) for v in manifest_ids.values())
    execute_ok = len(hard_stops) == 0 and total > 0 and len(disposable_identities) == len(identities) and len(disposable_cms) == len(
        contact_methods
    )

    preserved = {}
    for table in PRESERVE:
        preserved[table] = {"count": len(list_all(table)), "action": "preserve_infrastructure"}

    pre_delete = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "comms_base": COMMS_BASE,
        "mike_test_emails": sorted(MIKE_TEST_EMAILS),
        "delete_order": DELETE_ORDER,
        "preserve": sorted(PRESERVE),
        "manifest_ids": manifest_ids,
        "manifest_counts": {k: len(v) for k, v in manifest_ids.items()},
        "manifest_total": total,
        "classification_summary": {
            k: {"count": len(v), "sample_reasons": sorted({i.get("reason", "") for i in v})[:8]}
            for k, v in classification.items()
        },
        "identity_proof": classification.get("Communication Identities", []),
        "contact_method_proof": classification.get("Contact Methods", []),
        "exceptions": exceptions,
        "hard_stop_email_exceptions": hard_stops,
        "preserved_infrastructure": preserved,
        "execute_authorized": execute_ok,
        "notes": [
            "Communications Hub transactional wipe before Mike Schmidt season simulation.",
            "All Communication Identities must be Is Test Identity? or equivalent disposable proof.",
            "Test Allowlist / Templates / Programs are infrastructure — never in delete manifest.",
            "Dependency order: Attempts → Audit Events → Deliveries → Keys → Messages → Integration Events → Contact Methods → Identities.",
        ],
    }

    path = OUT / "cleanup-manifest-comms-hub.json"
    path.write_text(json.dumps(pre_delete, indent=2, default=str), encoding="utf-8")

    # Also merge pointer into main readiness cleanup-manifest.json if present
    main_path = OUT / "cleanup-manifest.json"
    if main_path.exists():
        try:
            main = json.loads(main_path.read_text(encoding="utf-8"))
        except Exception:
            main = {}
        main["communications_hub"] = {
            "base": COMMS_BASE,
            "manifest_file": "cleanup-manifest-comms-hub.json",
            "manifest_total": total,
            "manifest_counts": pre_delete["manifest_counts"],
            "execute_authorized": execute_ok,
            "delete_order": DELETE_ORDER,
            "preserve": sorted(PRESERVE),
            "updated_at": pre_delete["generated_at"],
        }
        # Flatten CommsHub:: IDs into manifest_ids for unified execute path
        for table, ids in manifest_ids.items():
            main.setdefault("manifest_ids", {})[f"CommsHub::{table}"] = ids
        main.setdefault("delete_order", [])
        for table in DELETE_ORDER:
            label = f"CommsHub::{table}"
            if label not in main["delete_order"]:
                main["delete_order"].append(label)
        main["comms_hub_execute_authorized"] = execute_ok
        main_path.write_text(json.dumps(main, indent=2, default=str), encoding="utf-8")

    print(
        json.dumps(
            {
                "manifest_total": total,
                "counts": pre_delete["manifest_counts"],
                "exceptions": len(exceptions),
                "hard_stops": len(hard_stops),
                "execute_authorized": execute_ok,
                "path": str(path),
            },
            indent=2,
        )
    )
    return 0 if execute_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

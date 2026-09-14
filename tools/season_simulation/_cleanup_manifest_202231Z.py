"""Build read-only exact-ID cleanup manifest for Perfect run 202231Z."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token

RUN = "SEASON-SIM-PERFECT-20260914T202231Z-mike-schmidt"
ENROLLMENT = "recrQNLC7wX3oqbmm"
ATHLETE = "recmTBFNWWGtCTsCx"
ALLOW = "schmidt@fairfieldbasketballclub.com"
SC_BASE = "appn84sqPw03zEbTT"
CURR_HUB = "appnrW8pPpzq8Nhov"
COMMS_HUB = "appYG1t5DBRimHBCT"
CATALOG_ZOOM = {
    "recMFP2x5LDqea9ax": "Introduction to the Challenge",
    "recb9EjQIJVzaRpZa": "Motivation for a Strong Finish",
}
EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)

REPO = Path(__file__).resolve().parents[2]
REG_PATH = (
    REPO
    / "tools"
    / "season_simulation"
    / "run_registries"
    / f"{RUN}__athlete1-perfect.json"
)
OUT = REPO / "docs" / "audits" / "readiness-20260914"

DELETE_ORDER = [
    "Comms::Delivery Attempts",
    "Comms::Audit Events",
    "Comms::Deliveries",
    "Comms::Delivery Keys",
    "Comms::Messages",
    "Comms::Integration Events",
    "Comms::Contact Methods",
    "Comms::Communication Identities",
    "Hub::Submission Outbox",
    "Hub::Homework Draft Responses",
    "Hub::Homework Draft Attempts",
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


def link_ids(value) -> list[str]:
    out: list[str] = []
    if not value:
        return out
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str) and item.startswith("rec"):
                out.append(item)
            elif isinstance(item, dict) and str(item.get("id") or "").startswith("rec"):
                out.append(str(item["id"]))
    return out


def batch_get(client: AirtableClient, table: str, ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    uniq = list(dict.fromkeys([i for i in ids if i and i.startswith("rec")]))
    for i in range(0, len(uniq), 40):
        chunk = uniq[i : i + 40]
        formula = "OR(" + ",".join(f"RECORD_ID()='{rid}'" for rid in chunk) + ")"
        rows.extend(client.list_records(table, formula=formula))
    return rows


def add(targets: dict[str, set[str]], table: str, ids, *, reason: str, ownership: dict):
    for rid in ids or []:
        if not rid or not str(rid).startswith("rec"):
            continue
        targets.setdefault(table, set()).add(str(rid))
        ownership.setdefault(table, {})[str(rid)] = reason


def extract_emails(value) -> list[str]:
    if value is None:
        return []
    text = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    return [m.strip().lower() for m in EMAIL_RE.findall(text)]


def main() -> int:
    if not REG_PATH.is_file():
        print(f"Missing registry {REG_PATH}")
        return 2

    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    assert reg.get("enrollment_id") == ENROLLMENT, reg.get("enrollment_id")
    assert reg.get("athlete_id") == ATHLETE, reg.get("athlete_id")

    sc = AirtableClient(token=load_token(), base_id=SC_BASE, allow_writes=False)
    curr = AirtableClient(token=load_token(), base_id=CURR_HUB, allow_writes=False)
    comms = AirtableClient(token=load_token(), base_id=COMMS_HUB, allow_writes=False)

    targets: dict[str, set[str]] = {}
    ownership: dict[str, dict[str, str]] = {}
    warnings: list[str] = []
    blockers: list[str] = []
    preserved: dict[str, list[str]] = defaultdict(list)

    ids_by = reg.get("ids_by_table") or {}
    for table, ids in ids_by.items():
        uniq = list(dict.fromkeys(ids or []))
        if table == "Zoom Meetings":
            for rid in uniq:
                if rid in CATALOG_ZOOM:
                    preserved["Zoom Meetings"].append(rid)
                    continue
                add(
                    targets,
                    table,
                    [rid],
                    reason="registry_disposable_zoom",
                    ownership=ownership,
                )
            continue
        add(targets, table, uniq, reason="registry_ids_by_table", ownership=ownership)

    add(targets, "Athletes", [ATHLETE], reason="fixed_athlete_id", ownership=ownership)
    add(
        targets,
        "Enrollments",
        [ENROLLMENT],
        reason="fixed_enrollment_id",
        ownership=ownership,
    )

    enr = sc.get_record("Enrollments", ENROLLMENT)
    ef = enr.get("fields") or {}
    add(
        targets,
        "XP Events",
        link_ids(ef.get("XP Events")),
        reason="enrollment_xp_events_link",
        ownership=ownership,
    )
    more_xp = sc.list_records(
        "XP Events", formula=f"{{Enrollment Record ID}}='{ENROLLMENT}'"
    )
    add(
        targets,
        "XP Events",
        [r["id"] for r in more_xp],
        reason="enrollment_record_id_match",
        ownership=ownership,
    )
    add(
        targets,
        "Athlete Achievement Unlocks",
        link_ids(ef.get("Athlete Achievement Unlocks")),
        reason="enrollment_achievement_unlocks_link",
        ownership=ownership,
    )
    add(
        targets,
        "Streak Occurrences",
        link_ids(ef.get("Streak Occurrences")),
        reason="enrollment_streak_occurrences_link",
        ownership=ownership,
    )

    for table, formulas in (
        (
            "Streak Occurrences",
            [f"{{Enrollment Record ID}}='{ENROLLMENT}'"],
        ),
        (
            "Email Handoff Queue",
            [f"{{Enrollment Record ID}}='{ENROLLMENT}'"],
        ),
        (
            "Athlete Achievement Unlocks",
            [
                f"FIND('{ENROLLMENT}', {{Milestone Source Key}} & '')",
                f"FIND('{RUN}', {{Milestone Source Key}} & '')",
            ],
        ),
        (
            "Weekly Athlete Summary",
            [
                f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
                f"FIND('{ENROLLMENT}', {{Name}} & '')",
            ],
        ),
    ):
        for formula in formulas:
            try:
                rows = sc.list_records(table, formula=formula)
                add(
                    targets,
                    table,
                    [r["id"] for r in rows],
                    reason=f"formula:{formula[:60]}",
                    ownership=ownership,
                )
                break
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{table}: {exc}")

    # Marker scans on notes-like fields
    for table, field in (
        ("Submissions", "Video Upload Note"),
        ("Homework Completions", "Notes"),
        ("Video Feedback", "Coach Feedback"),
    ):
        try:
            rows = sc.list_records(table, formula=f"FIND('{RUN}', {{{field}}} & '')")
            add(
                targets,
                table,
                [r["id"] for r in rows],
                reason=f"run_marker_in_{field}",
                ownership=ownership,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"marker {table}/{field}: {exc}")

    ehq_ids = sorted(targets.get("Email Handoff Queue") or [])
    ehq_rows = batch_get(sc, "Email Handoff Queue", ehq_ids) if ehq_ids else []
    recipients: set[str] = set()
    hub_event_ids: list[str] = []
    for r in ehq_rows:
        f = r.get("fields") or {}
        for em in extract_emails(f.get("Recipients JSON")) + extract_emails(
            f.get("Payload JSON")
        ) + extract_emails(f.get("To")):
            recipients.add(em)
        hid = f.get("Hub Event ID")
        if hid and str(hid).startswith("rec"):
            hub_event_ids.append(str(hid))
    unsafe = sorted(e for e in recipients if e and e != ALLOW)
    if unsafe:
        blockers.append(f"unsafe_recipients:{unsafe}")

    for table, formulas in (
        (
            "Submission Outbox",
            [
                f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
                f"FIND('{ENROLLMENT}', {{Enrollment}} & '')",
            ],
        ),
        (
            "Homework Draft Responses",
            [
                f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
                f"FIND('{ATHLETE}', {{Athlete Record ID}} & '')",
            ],
        ),
        (
            "Homework Draft Attempts",
            [
                f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
                f"FIND('{ATHLETE}', {{Athlete Record ID}} & '')",
            ],
        ),
    ):
        for formula in formulas:
            try:
                rows = curr.list_records(table, formula=formula)
                add(
                    targets,
                    f"Hub::{table}",
                    [r["id"] for r in rows],
                    reason=f"curriculum_hub:{formula[:50]}",
                    ownership=ownership,
                )
                break
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Curriculum {table}: {exc}")

    comms_targets: dict[str, set[str]] = {}
    if hub_event_ids:
        add(
            comms_targets,
            "Integration Events",
            hub_event_ids,
            reason="ehq_hub_event_id",
            ownership=ownership,
        )

    try:
        identities = comms.list_records(
            "Communication Identities",
            formula=f"FIND('{ALLOW}', {{Email}} & '')",
        )
        for r in identities:
            f = r.get("fields") or {}
            emails = extract_emails(f.get("Email")) + extract_emails(f)
            if any(e != ALLOW for e in emails if e):
                blockers.append(f"comms_identity_unsafe:{r['id']}:{emails}")
                continue
            if f.get("Is Test Identity?") is True:
                add(
                    comms_targets,
                    "Communication Identities",
                    [r["id"]],
                    reason="allowlisted_test_identity",
                    ownership=ownership,
                )
            else:
                preserved["Communication Identities"].append(r["id"])
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Communication Identities scan: {exc}")

    for ie_id in list(comms_targets.get("Integration Events") or []):
        try:
            ie = comms.get_record("Integration Events", ie_id)
            f = ie.get("fields") or {}
            for table, field in (
                ("Messages", "Messages"),
                ("Deliveries", "Deliveries"),
                ("Delivery Attempts", "Delivery Attempts"),
                ("Delivery Keys", "Delivery Keys"),
                ("Audit Events", "Audit Events"),
            ):
                linked = link_ids(f.get(field))
                if linked:
                    add(
                        comms_targets,
                        table,
                        linked,
                        reason=f"integration_event_link:{ie_id}",
                        ownership=ownership,
                    )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Integration Event expand {ie_id}: {exc}")

    # Contact methods for test identities
    for ident in list(comms_targets.get("Communication Identities") or []):
        try:
            rec = comms.get_record("Communication Identities", ident)
            f = rec.get("fields") or {}
            cms = link_ids(f.get("Contact Methods"))
            add(
                comms_targets,
                "Contact Methods",
                cms,
                reason=f"test_identity_contact_methods:{ident}",
                ownership=ownership,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Contact Methods for {ident}: {exc}")

    for table, ids in comms_targets.items():
        add(
            targets,
            f"Comms::{table}",
            ids,
            reason="comms_hub_owned",
            ownership=ownership,
        )

    # Validate no catalog zoom in delete set
    zoom_del = targets.get("Zoom Meetings") or set()
    for cid in CATALOG_ZOOM:
        if cid in zoom_del:
            blockers.append(f"catalog_zoom_in_delete_set:{cid}")
            zoom_del.discard(cid)
            preserved["Zoom Meetings"].append(cid)

    # Duplicate ID check across tables (same id in multiple tables is ok; within table no)
    dup_report = {}
    for table, ids in targets.items():
        if len(ids) != len(set(ids)):
            dup_report[table] = "internal_duplicate"
    if dup_report:
        blockers.append(f"duplicate_ids:{dup_report}")

    # Ambiguous ownership: any target without ownership reason
    ambiguous = []
    for table, ids in targets.items():
        for rid in ids:
            if not (ownership.get(table) or {}).get(rid):
                ambiguous.append(f"{table}:{rid}")
    if ambiguous:
        blockers.append(f"ambiguous_ownership:{ambiguous[:20]}")

    manifest_ids = {k: sorted(v) for k, v in sorted(targets.items()) if v}
    total = sum(len(v) for v in manifest_ids.values())
    ownership_flat = {
        k: dict(sorted(v.items())) for k, v in sorted(ownership.items()) if v
    }

    ownership_pass = not blockers and total > 0
    man = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": RUN,
        "enrollment_id": ENROLLMENT,
        "athlete_id": ATHLETE,
        "sc_base": SC_BASE,
        "curriculum_hub_base": CURR_HUB,
        "comms_hub_base": COMMS_HUB,
        "allowlist_email": ALLOW,
        "delete_order": DELETE_ORDER,
        "manifest_ids": manifest_ids,
        "counts": {k: len(v) for k, v in manifest_ids.items()},
        "total_ids": total,
        "preserved": {k: sorted(set(v)) for k, v in preserved.items()},
        "recipients_observed": sorted(recipients),
        "unsafe_recipients": unsafe,
        "warnings": warnings,
        "blockers": blockers,
        "ownership_pass": ownership_pass,
    }
    own = {
        "pass": ownership_pass,
        "run": RUN,
        "enrollment_id": ENROLLMENT,
        "athlete_id": ATHLETE,
        "ownership": ownership_flat,
        "unsafe_recipients": unsafe,
        "blockers": blockers,
        "warnings": warnings,
        "total_ids": total,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    man_path = OUT / f"cleanup-manifest-{RUN}.json"
    own_path = OUT / f"cleanup-ownership-{RUN}.json"
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    own_path.write_text(json.dumps(own, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total_ids": total, "ownership_pass": ownership_pass, "counts": man["counts"], "blockers": blockers, "unsafe": unsafe}, indent=2))
    print("Wrote", man_path)
    print("Wrote", own_path)
    return 0 if ownership_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Build read-only exact-ID cleanup manifest for Perfect run 183404Z.

Does not delete. Stops if non-allowlisted recipients are found.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token
from season_simulation.clock_override import formula_text_has_season_sim_gate

RUN = "SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt"
ENROLLMENT = "rec2r1VgYEEWJBeKG"
ATHLETE = "recRrd9nLKwK4vspy"
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
WT_REG = (
    REPO
    / ".worktrees"
    / "perfect-sim-master-20260914"
    / "tools"
    / "season_simulation"
    / "run_registries"
    / f"{RUN}__athlete1-perfect.json"
)
REG_DIR = REPO / "tools" / "season_simulation" / "run_registries"
REG_PATH = REG_DIR / f"{RUN}__athlete1-perfect.json"
OUT = REPO / "docs" / "audits" / "readiness-20260914"


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
    if WT_REG.is_file() and not REG_PATH.is_file():
        REG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(WT_REG, REG_PATH)
    if not REG_PATH.is_file():
        print(f"Missing registry {REG_PATH}", file=sys.stderr)
        return 2

    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    assert reg.get("enrollment_id") == ENROLLMENT
    assert reg.get("athlete_id") == ATHLETE

    sc = AirtableClient(token=load_token(), base_id=SC_BASE, allow_writes=False)
    curr = AirtableClient(token=load_token(), base_id=CURR_HUB, allow_writes=False)
    comms = AirtableClient(token=load_token(), base_id=COMMS_HUB, allow_writes=False)

    targets: dict[str, set[str]] = {}
    ownership: dict[str, dict[str, str]] = {}
    warnings: list[str] = []
    blockers: list[str] = []
    preserved: dict[str, list[str]] = defaultdict(list)

    # Registry tables
    ids_by = reg.get("ids_by_table") or {}
    for table, ids in ids_by.items():
        if table == "Zoom Meetings":
            for rid in ids:
                if rid in CATALOG_ZOOM:
                    preserved["Zoom Meetings"].append(rid)
                    continue
                add(targets, table, [rid], reason="registry_disposable_zoom", ownership=ownership)
            continue
        add(targets, table, ids, reason="registry_ids_by_table", ownership=ownership)

    # Enrollment live links
    enr = sc.get_record("Enrollments", ENROLLMENT)
    ef = enr.get("fields") or {}
    xp_ids = link_ids(ef.get("XP Events"))
    add(targets, "XP Events", xp_ids, reason="enrollment_xp_events_link", ownership=ownership)
    more_xp = sc.list_records(
        "XP Events", formula=f"FIND('{ENROLLMENT}', {{Source Key}} & '')"
    )
    add(
        targets,
        "XP Events",
        [r["id"] for r in more_xp],
        reason="source_key_contains_enrollment",
        ownership=ownership,
    )
    unlock_ids = link_ids(ef.get("Athlete Achievement Unlocks"))
    add(
        targets,
        "Athlete Achievement Unlocks",
        unlock_ids,
        reason="enrollment_achievement_unlocks_link",
        ownership=ownership,
    )
    streak_ids = link_ids(ef.get("Streak Occurrences"))
    if streak_ids:
        add(
            targets,
            "Streak Occurrences",
            streak_ids,
            reason="enrollment_streak_occurrences_link",
            ownership=ownership,
        )

    for table, formula in (
        (
            "Athlete Achievement Unlocks",
            f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
        ),
        (
            "Streak Occurrences",
            f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
        ),
        (
            "Email Handoff Queue",
            f"{{Enrollment Record ID}} = '{ENROLLMENT}'",
        ),
    ):
        try:
            rows = sc.list_records(table, formula=formula)
            add(
                targets,
                table,
                [r["id"] for r in rows],
                reason="enrollment_record_id_match",
                ownership=ownership,
            )
        except Exception as exc:  # noqa: BLE001
            # try alternate formulas
            warnings.append(f"{table} primary formula failed: {exc}")
            for alt in (
                f"FIND('{ENROLLMENT}', {{Source Key}} & '')",
                f"FIND('{ENROLLMENT}', ARRAYJOIN({{Enrollment}}))",
            ):
                try:
                    rows = sc.list_records(table, formula=alt)
                    add(
                        targets,
                        table,
                        [r["id"] for r in rows],
                        reason=f"alt:{alt[:40]}",
                        ownership=ownership,
                    )
                    break
                except Exception as exc2:  # noqa: BLE001
                    warnings.append(f"{table} alt failed: {exc2}")

    # EHQ recipient safety + hub event ids
    ehq_ids = sorted(targets.get("Email Handoff Queue") or [])
    ehq_rows = batch_get(sc, "Email Handoff Queue", ehq_ids) if ehq_ids else []
    recipients = set()
    hub_event_ids = []
    for r in ehq_rows:
        f = r.get("fields") or {}
        for em in extract_emails(f.get("Recipients JSON")) + extract_emails(
            f.get("Payload JSON")
        ):
            recipients.add(em)
        hid = f.get("Hub Event ID")
        if hid and str(hid).startswith("rec"):
            hub_event_ids.append(str(hid))
    unsafe = sorted(e for e in recipients if e and e != ALLOW)
    if unsafe:
        blockers.append(f"unsafe_recipients:{unsafe}")

    # Curriculum Hub — enrollment / source record ownership
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
        found = False
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
                found = True
                break
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Curriculum {table}: {exc}")
        if not found:
            warnings.append(f"Curriculum {table}: no matching formula succeeded")

    # Communications Hub — only via Hub Event IDs / allowlisted test identity
    comms_targets: dict[str, set[str]] = {}
    if hub_event_ids:
        # Integration Events by id
        add(
            comms_targets,
            "Integration Events",
            hub_event_ids,
            reason="ehq_hub_event_id",
            ownership=ownership,
        )
    # Test identities for allowlisted email only
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
            # Only delete if marked test AND created around this run — require Is Test Identity?
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

    # If Hub Event IDs exist, pull dependent deliveries via Integration Event links
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
                ("Contact Methods", "Contact Methods"),
            ):
                linked = link_ids(f.get(field))
                if linked:
                    add(
                        comms_targets,
                        table,
                        linked,
                        reason=f"linked_from_integration_event:{ie_id}",
                        ownership=ownership,
                    )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Integration Event expand {ie_id}: {exc}")

    # Merge Hub targets with prefix
    for table, ids in comms_targets.items():
        add(
            targets,
            f"Comms::{table}",
            ids,
            reason="comms_hub_owned",
            ownership=ownership,
        )

    # Force-exclude catalog zooms
    for rid in CATALOG_ZOOM:
        if rid in (targets.get("Zoom Meetings") or set()):
            targets["Zoom Meetings"].discard(rid)
            preserved["Zoom Meetings"].append(rid)
            warnings.append(f"removed catalog zoom from delete set: {rid}")

    # Never delete Athletes/Enrollments until dependents listed — keep order later
    manifest_ids = {k: sorted(v) for k, v in sorted(targets.items()) if v}
    counts = {k: len(v) for k, v in manifest_ids.items()}

    # Formula state
    season_sim_hits = []
    for table in sc.meta_tables():
        for field in table.get("fields") or []:
            formula = (field.get("options") or {}).get("formula")
            if not formula:
                continue
            if formula_text_has_season_sim_gate(formula) or "SEASON-SIM" in formula:
                season_sim_hits.append(
                    {
                        "table": table.get("name"),
                        "field": field.get("name"),
                        "preview": formula[:120],
                    }
                )

    ownership_ok = not blockers and not unsafe
    ownership_report = {
        "run": RUN,
        "enrollment_id": ENROLLMENT,
        "athlete_id": ATHLETE,
        "pass": ownership_ok,
        "unsafe_recipients": unsafe,
        "recipients": sorted(recipients),
        "allowlist_only": not unsafe,
        "ehq_count": len(ehq_ids),
        "hub_event_ids": hub_event_ids,
        "preserved_catalog_zoom": dict(CATALOG_ZOOM),
        "preserved": {k: sorted(set(v)) for k, v in preserved.items()},
        "counts_by_table": counts,
        "blockers": blockers,
        "warnings": warnings,
        "formula_season_sim_hits": season_sim_hits,
        "production_normal_formulas": len(season_sim_hits) == 0,
        "ownership_sample": {
            t: dict(list(rows.items())[:3]) for t, rows in ownership.items()
        },
    }

    delete_order = [
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

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run": RUN,
        "enrollment_id": ENROLLMENT,
        "athlete_id": ATHLETE,
        "sc_base": SC_BASE,
        "curriculum_hub_base": CURR_HUB,
        "comms_hub_base": COMMS_HUB,
        "allowlist_email": ALLOW,
        "delete_order": delete_order,
        "manifest_ids": manifest_ids,
        "counts": counts,
        "total_ids": sum(counts.values()),
        "preserved_catalog_zoom": dict(CATALOG_ZOOM),
        "ownership_pass": ownership_ok,
        "blockers": blockers,
        "warnings": warnings,
    }

    OUT.mkdir(parents=True, exist_ok=True)
    man_path = OUT / f"cleanup-manifest-{RUN}.json"
    own_path = OUT / f"cleanup-ownership-{RUN}.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    own_path.write_text(json.dumps(ownership_report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(man_path), "ownership": str(own_path), "total": manifest["total_ids"], "pass": ownership_ok, "counts": counts, "blockers": blockers}, indent=2))
    return 0 if ownership_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())

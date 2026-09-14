"""Phase 1 read-only failure evidence for Perfect run 183404Z. Do not write."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from season_simulation.airtable_client import AirtableClient, load_token
from season_simulation.business_reconciliation import (
    actual_xp_buckets_from_events,
    event_is_active,
    sum_active_xp_points,
)
from season_simulation.clock_override import formula_text_has_season_sim_gate

RUN = "SEASON-SIM-PERFECT-20260914T183404Z-mike-schmidt"
ENROLLMENT = "rec2r1VgYEEWJBeKG"
WAS_W2 = "recYhbzze2Xc75lDa"
WEEK_W2 = "rec7RpUMVLbcrmn4h"
ALLOW = "schmidt@fairfieldbasketballclub.com"
MISSING_150 = f"WEEKLY_THRESHOLD|{ENROLLMENT}|{WEEK_W2}|150"
REPO = Path(__file__).resolve().parents[2]
REG_PATH = (
    REPO
    / ".worktrees"
    / "perfect-sim-master-20260914"
    / "tools"
    / "season_simulation"
    / "run_registries"
    / f"{RUN}__athlete1-perfect.json"
)
OUT = REPO / "docs" / "audits" / "readiness-20260914"

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)


def bucket_of(fields: dict) -> str:
    sk = str(fields.get("Source Key") or "").upper()
    xp_bucket = str(fields.get("XP Bucket") or "").upper()
    hay = f"{sk}|{xp_bucket}|{fields.get('XP Source') or ''}".upper()
    mapping = (
        ("STREAK", "Streak XP"),
        ("WEEKLY_THRESHOLD", "Weekly Threshold XP"),
        ("THRESHOLD", "Weekly Threshold XP"),
        ("SUBMISSION", "Submission XP"),
        ("HOMEWORK", "Homework XP"),
        ("VIDEO", "Video XP"),
        ("PERFECT_WEEK", "Perfect Week XP"),
        ("PERFECT WEEK", "Perfect Week XP"),
        ("SHOT", "Shot Milestone XP"),
        ("MILESTONE", "Shot Milestone XP"),
        ("ZOOM", "Zoom XP"),
    )
    for needle, name in mapping:
        if needle in hay:
            return name
    return "Other"


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
    elif isinstance(value, str) and value.startswith("rec"):
        out.append(value)
    return out


def batch_get(client: AirtableClient, table: str, ids: list[str]) -> list[dict]:
    rows: list[dict] = []
    uniq = list(dict.fromkeys(ids))
    for i in range(0, len(uniq), 40):
        chunk = uniq[i : i + 40]
        formula = "OR(" + ",".join(f"RECORD_ID()='{rid}'" for rid in chunk) + ")"
        rows.extend(client.list_records(table, formula=formula))
    return rows


def extract_emails(value) -> list[str]:
    found: list[str] = []
    if value is None:
        return found
    if isinstance(value, (dict, list)):
        text = json.dumps(value)
    else:
        text = str(value)
    for m in EMAIL_RE.findall(text):
        found.append(m.strip().lower())
    return found


def main() -> int:
    if not REG_PATH.is_file():
        print(f"Missing registry: {REG_PATH}", file=sys.stderr)
        return 2

    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    c = AirtableClient(token=load_token(), allow_writes=False)
    print("base", c.base_id)

    enr = c.get_record("Enrollments", ENROLLMENT)
    ef = enr.get("fields") or {}
    xp_ids = link_ids(ef.get("XP Events"))
    print(
        "ENROLLMENT lifetime",
        ef.get("Lifetime XP Earned"),
        "xp_links",
        len(xp_ids),
        "level",
        ef.get("Active Level") or ef.get("Current Level") or ef.get("Level"),
    )

    events = batch_get(c, "XP Events", xp_ids) if xp_ids else []
    # Supplement by Source Key containing enrollment id
    more = c.list_records(
        "XP Events",
        formula=f"FIND('{ENROLLMENT}', {{Source Key}} & '')",
    )
    by_id = {e["id"]: e for e in events}
    for e in more:
        by_id[e["id"]] = e
    events = list(by_id.values())

    active = [e for e in events if event_is_active(e.get("fields") or {})]
    inactive = [e for e in events if not event_is_active(e.get("fields") or {})]
    buckets_active = actual_xp_buckets_from_events(events)
    active_sum = sum_active_xp_points(events)

    inactive_by_bucket: Counter[str] = Counter()
    active_by_bucket: Counter[str] = Counter()
    inactive_streak: list[dict] = []
    active_streak: list[dict] = []
    for e in events:
        f = e.get("fields") or {}
        b = bucket_of(f)
        row = {
            "id": e["id"],
            "source_key": str(f.get("Source Key") or ""),
            "xp_points": f.get("XP Points") or f.get("Points"),
            "active_xp_points": f.get("Active XP Points"),
            "active_flag": f.get("Active?") if "Active?" in f else f.get("Active"),
            "xp_bucket": f.get("XP Bucket"),
            "bucket": b,
        }
        if event_is_active(f):
            active_by_bucket[b] += 1
            if b == "Streak XP":
                active_streak.append(row)
        else:
            inactive_by_bucket[b] += 1
            if b == "Streak XP":
                inactive_streak.append(row)

    print(
        f"XP total={len(events)} active={len(active)} inactive={len(inactive)} "
        f"active_sum={active_sum}"
    )
    print("active buckets", buckets_active)
    print("active counts", dict(active_by_bucket))
    print("inactive counts", dict(inactive_by_bucket))
    print("inactive streak count", len(inactive_streak))
    for row in inactive_streak:
        print("  INACTIVE STREAK", row["id"], row["source_key"], row["xp_points"])

    was = c.get_record("Weekly Athlete Summary", WAS_W2)
    wf = was.get("fields") or {}
    print("WAS W2 Goal Completion %", wf.get("Goal Completion %"))
    print("WAS W2 Threshold XP Status", wf.get("Threshold XP Status"))
    print("WAS W2 Requeue Threshold XP", wf.get("Requeue Threshold XP"))

    wt = []
    for e in events:
        f = e.get("fields") or {}
        sk = str(f.get("Source Key") or "")
        if "WEEKLY_THRESHOLD" in sk.upper():
            wt.append(
                {
                    "id": e["id"],
                    "key": sk,
                    "active": event_is_active(f),
                    "pts": f.get("XP Points") or f.get("Points"),
                }
            )
    w2_related = [x for x in wt if WEEK_W2 in x["key"] or WAS_W2 in x["key"]]
    has_150 = any(x["key"] == MISSING_150 for x in wt)
    print("W2-related WT events:")
    for x in sorted(w2_related, key=lambda z: z["key"]):
        print(" ", x)
    print("missing_150_key_present", has_150, "expected", MISSING_150)

    meta = c.meta_tables()
    season_sim_hits = []
    monitored = []
    for table in meta:
        for field in table.get("fields") or []:
            opts = field.get("options") or {}
            formula = opts.get("formula")
            if not formula:
                continue
            name = field.get("name")
            tname = table.get("name")
            gated = formula_text_has_season_sim_gate(formula)
            entry = {
                "table": tname,
                "field": name,
                "has_season_sim_gate": gated,
                "contains_season_sim_text": ("SEASON-SIM" in formula)
                or ("SEASON SIM" in formula.upper()),
                "formula_preview": formula[:220],
                "formula_len": len(formula),
            }
            if gated or entry["contains_season_sim_text"]:
                season_sim_hits.append(entry)
            if name in (
                "Activity Date Is Future?",
                "Submitted Same Day?",
                "Perfect Week Grace Eligible?",
            ):
                monitored.append(entry)

    print(
        "formula monitored",
        len(monitored),
        "season_sim_hits",
        len(season_sim_hits),
    )

    # EHQ via Enrollment Record ID + Payload/Recipients scan
    ehq_by_id: dict[str, dict] = {}
    for formula in (
        f"{{Enrollment Record ID}} = '{ENROLLMENT}'",
        f"FIND('{ENROLLMENT}', {{Enrollment Record ID}} & '')",
        f"FIND('{ENROLLMENT}', {{Source Record ID}} & '')",
        f"FIND('{RUN}', {{Payload JSON}} & '')",
        f"FIND('{RUN}', {{Handoff Key}} & '')",
    ):
        try:
            for r in c.list_records("Email Handoff Queue", formula=formula):
                ehq_by_id[r["id"]] = r
        except Exception as exc:  # noqa: BLE001
            print("EHQ formula fail", formula[:70], exc)

    ehq = list(ehq_by_id.values())
    recipients: Counter[str] = Counter()
    ehq_summary = []
    for r in ehq:
        f = r.get("fields") or {}
        emails: list[str] = []
        for field in ("Recipients JSON", "Payload JSON", "Last Error", "Hub Response JSON"):
            emails.extend(extract_emails(f.get(field)))
        for em in emails:
            recipients[em] += 1
        ehq_summary.append(
            {
                "id": r["id"],
                "status": f.get("Status"),
                "test_mode": f.get("Test Mode?"),
                "template_key": f.get("Template Key"),
                "event_type": f.get("Event Type"),
                "hub_event_id": f.get("Hub Event ID"),
                "source_record_id": f.get("Source Record ID"),
                "enrollment_record_id": f.get("Enrollment Record ID"),
                "recipients": sorted(set(emails)),
                "handoff_key": f.get("Handoff Key"),
            }
        )
    unsafe = sorted({e for e in recipients if e and e != ALLOW})
    print("EHQ", len(ehq), "recipients", dict(recipients), "unsafe", unsafe or "NONE")

    streak_occ = []
    try:
        streak_occ = c.list_records(
            "Streak Occurrences",
            formula=f"FIND('{ENROLLMENT}', {{Source Key}} & '')",
        )
    except Exception:
        try:
            # fallback via enrollment links if present on enrollment
            so_ids = link_ids(ef.get("Streak Occurrences"))
            if so_ids:
                streak_occ = batch_get(c, "Streak Occurrences", so_ids)
        except Exception as exc:  # noqa: BLE001
            print("Streak Occurrences query fail", exc)

    report = {
        "phase": "1_failure_evidence_readonly",
        "generated_by": "tools/season_simulation/_phase1_failure_evidence_183404Z.py",
        "run": RUN,
        "enrollment_id": ENROLLMENT,
        "athlete_id": reg.get("athlete_id"),
        "registry_status": reg.get("status"),
        "registry_path": str(REG_PATH),
        "enrollment_live": {
            "lifetime_xp_earned": ef.get("Lifetime XP Earned"),
            "lifetime_xp_total": ef.get("Lifetime XP Total"),
            "active_level": ef.get("Active Level")
            or ef.get("Current Level")
            or ef.get("Level"),
            "xp_event_link_count": len(xp_ids),
        },
        "xp": {
            "total_events": len(events),
            "active_count": len(active),
            "inactive_count": len(inactive),
            "active_xp_sum": active_sum,
            "active_buckets": buckets_active,
            "active_event_counts_by_bucket": dict(active_by_bucket),
            "inactive_event_counts_by_bucket": dict(inactive_by_bucket),
            "active_streak_xp_events": active_streak,
            "inactive_streak_xp_events": inactive_streak,
            "weekly_threshold_events": wt,
            "weekly_threshold_active_count": sum(1 for x in wt if x["active"]),
            "weekly_threshold_active_xp": buckets_active.get("Weekly Threshold XP"),
        },
        "week2_was": {
            "id": WAS_W2,
            "goal_completion_pct": wf.get("Goal Completion %")
            or wf.get("Goal Completion Percent"),
            "threshold_xp_status": wf.get("Threshold XP Status"),
            "requeue_threshold_xp": wf.get("Requeue Threshold XP"),
            "week": wf.get("Week"),
            "related_wt_events": w2_related,
            "expected_missing_150_source_key": MISSING_150,
            "missing_150_source_key_present": has_150,
            "present_wt_keys_for_week": [x["key"] for x in w2_related],
        },
        "streak_occurrences_count": len(streak_occ),
        "formulas": {
            "production_normal_no_season_sim_branches": len(season_sim_hits) == 0,
            "season_sim_hits": season_sim_hits,
            "monitored_fields": monitored,
        },
        "ehq": {
            "count": len(ehq),
            "recipients": dict(recipients),
            "unsafe_recipients": unsafe,
            "allowlist_only": not unsafe,
            "rows": ehq_summary,
        },
        "interpretation": {
            "pre_restore_snapshot_xp": 4950,
            "live_active_xp_after_restore": active_sum,
            "inactive_streak_count": len(inactive_streak),
            "statement": (
                "The 4,950 number was a pre-restore simulation snapshot "
                "(missing one 150% Weekly Threshold award = 30 XP vs target 4,980). "
                "The live active XP after Production-normal formula restore reflects "
                "post-restore ineligibility/deactivation (nine STREAK_XP events "
                "inactive when that state is present). Future-dated Week 2 WAS "
                f"{WAS_W2} shows Goal Completion %=0 under Production NOW() formulas. "
                "Do not fabricate the missing 30-XP event and do not requeue under "
                "restored formulas. Treat this run as a failed acceptance test."
            ),
        },
    }

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"failure-evidence-{RUN}.json"
    path.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")

    streak_lines = [
        f"- `{row['id']}` — `{row['source_key']}` ({row['xp_points']} XP)"
        for row in inactive_streak
    ] or ["- (none found in this read)"]
    md_lines = [
        f"# Failure evidence — `{RUN}`",
        "",
        "## Verdict",
        "",
        "Failed Perfect acceptance test. Do not treat as a passing season.",
        "",
        "## Enrollment",
        "",
        f"- Enrollment: `{ENROLLMENT}`",
        f"- Athlete: `{reg.get('athlete_id')}`",
        f"- Live Lifetime XP Earned: `{ef.get('Lifetime XP Earned')}`",
        f"- Live active XP sum (Active XP Points): `{active_sum}`",
        f"- Pre-restore snapshot (documented): `4950`",
        f"- Target: `4980`",
        "",
        "## Active XP buckets",
        "",
        "```json",
        json.dumps(buckets_active, indent=2),
        "```",
        "",
        f"- Active events: {len(active)}; Inactive events: {len(inactive)}",
        f"- Inactive Streak XP events: {len(inactive_streak)}",
        "",
        "## Inactive STREAK_XP Source Keys",
        "",
        *streak_lines,
        "",
        "## Week 2 WAS",
        "",
        f"- WAS: `{WAS_W2}`",
        f"- Goal Completion %: `{wf.get('Goal Completion %')}`",
        f"- Threshold XP Status: `{wf.get('Threshold XP Status')}`",
        f"- Requeue Threshold XP: `{wf.get('Requeue Threshold XP')}`",
        f"- Expected missing 150 Source Key: `{MISSING_150}`",
        f"- Missing 150 key present in base: `{has_150}`",
        f"- Present WT keys for week: `{[x['key'] for x in w2_related]}`",
        "",
        "## Formula state",
        "",
        f"- Production-normal (no SEASON-SIM branches): `{len(season_sim_hits) == 0}`",
        f"- SEASON-SIM hits: `{len(season_sim_hits)}`",
        "",
        "## EHQ / email safety",
        "",
        f"- EHQ rows: `{len(ehq)}`",
        f"- Recipients: `{dict(recipients)}`",
        f"- Unsafe recipients: `{unsafe or 'NONE'}`",
        f"- Allowlist only: `{not unsafe}`",
        "",
        "## Explicit statement",
        "",
        report["interpretation"]["statement"],
        "",
        f"Machine-readable: `{path.as_posix()}`",
        "",
    ]
    md = OUT / f"failure-evidence-{RUN}.md"
    md.write_text("\n".join(md_lines), encoding="utf-8")
    print("Wrote", path)
    print("Wrote", md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Hydrate local run registries from prior execute-three reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .execute_three import profile_registry_run_id
from .run_registry import RunRegistry, save_registry


def hydrate_registry_from_execute_three_report(
    *,
    report_path: Path,
    profile: str,
    registry_dir: Path,
    run_id: str,
) -> RunRegistry:
    """Rebuild a profile registry from execute-three JSON (created_records + ids)."""
    data = json.loads(report_path.read_text(encoding="utf-8"))
    pr = (data.get("profile_results") or {}).get(profile) or {}
    b_create = pr.get("B_create") or {}
    reg_run_id = profile_registry_run_id(run_id, profile)
    created = list(b_create.get("created_records") or [])
    athlete_id = ""
    enrollment_id = ""
    for row in created:
        if row.get("table") == "Athletes" and row.get("step") == "athlete":
            athlete_id = str(row.get("id") or "")
        if row.get("table") == "Enrollments" and row.get("step") == "enrollment":
            enrollment_id = str(row.get("id") or "")

    reg = RunRegistry(
        run_id=reg_run_id,
        created_at=str(b_create.get("generated_at") or datetime.now(timezone.utc).isoformat()),
        athlete_name=profile.replace("_", " ").title(),
        enrollment_id=enrollment_id,
        athlete_id=athlete_id,
        status="complete",
        last_completed_step="H_post_cascade_hooks",
        pause_reason="",
        meta={
            "shared_run_id": run_id,
            "profile": profile,
            "hydrated_from_report": str(report_path),
        },
    )
    for row in created:
        rid = str(row.get("id") or "")
        if not rid.startswith("rec"):
            continue
        reg.add(
            str(row.get("table") or ""),
            rid,
            dedupe_key=str(row.get("dedupe_key") or ""),
            notes=str(row.get("step") or ""),
            fields_snapshot=dict(row.get("fields_snapshot") or {}),
        )
    save_registry(reg, registry_dir)
    return reg


def hydrate_all_from_report(
    *,
    report_path: Path,
    registry_dir: Path,
    run_id: str,
    profiles: tuple[str, ...] = (
        "athlete1_perfect",
        "athlete2_recovery",
        "athlete3_edge",
    ),
) -> dict[str, Any]:
    registry_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {"profiles": {}, "report_path": str(report_path)}
    for profile in profiles:
        pr = json.loads(report_path.read_text(encoding="utf-8")).get("profile_results", {}).get(
            profile, {}
        )
        if not (pr.get("B_create") or {}).get("created_records"):
            out["profiles"][profile] = {"status": "skipped_no_created_records"}
            continue
        reg = hydrate_registry_from_execute_three_report(
            report_path=report_path,
            profile=profile,
            registry_dir=registry_dir,
            run_id=run_id,
        )
        out["profiles"][profile] = {
            "status": "hydrated",
            "registry_run_id": reg.run_id,
            "enrollment_id": reg.enrollment_id,
            "athlete_id": reg.athlete_id,
            "record_count": len(reg.records),
        }
    return out

"""Formula snapshot / restore lifecycle for season sim execute (Stage Z).

**Never use OMNI / in-base AI to generate or paste formulas.** OMNI has produced
``Unable to generate formula`` failures that leave fields invalid. Operators must
paste from ``tools/season_simulation/FORMULAS-TO-PASTE.txt`` or committed docs,
or use the Airtable Meta API with **exact** formula text from the committed
Production-normal bundle.

Stage Z restores **only** from ``production_normal_formulas.json`` — never from a
Stage-0 pre-run snapshot (that snapshot may already contain Season Sim gates).

Lifecycle registry flags: gates_applied, settlement_complete, formula_restore_pending,
production_formulas_restored, formula_restore_failed.

Public hooks: ``snapshot_formulas``, ``restore_production_formulas``,
``recover_pending_formula_restore``.
"""

from __future__ import annotations

import json
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .clock_override import (
    GATED_ACTIVITY_DATE_IS_FUTURE_FORMULA,
    PRODUCTION_ACTIVITY_DATE_IS_FUTURE_FORMULA,
    formula_text_has_season_sim_gate,
)
from .constants import CONFIRM_TOKEN, DEFAULT_BASE_ID
from .production_normal_formulas import (
    ProductionNormalBundle,
    ProductionNormalBundleError,
    formula_sha256,
    load_production_normal_bundle,
)

# Fail-closed: never accept OMNI / broken formula output.
OMNI_FORMULA_FAILURE_STRING = "Unable to generate formula"

MONITORED_FORMULA_FIELDS: tuple[tuple[str, str], ...] = (
    ("Submissions", "Activity Date Is Future?"),
    ("Submissions", "Submitted Same Day?"),
    ("Submissions", "Perfect Week Grace Eligible?"),
)

FORMULA_RESTORE_API_HOOK = {
    "tool": "AirtableClient.update_formula_field",
    "notes": (
        "Restore exact Production-normal formula_text via Meta API PATCH; "
        "assert base/table/field IDs; pre/post SHA-256 verify; refuse if "
        "SEASON-SIM text remains. Do NOT restore from Stage-0 snapshots. "
        "Do NOT use OMNI or natural-language formula generation."
    ),
    "required_payload_keys": ("baseId", "tableId", "fieldId", "formula"),
    "restore_source": "tools/season_simulation/production_normal_formulas.json",
}

# Explicit lifecycle flags stored on run registry.meta["formula_lifecycle"].
FORMULA_LIFECYCLE_KEYS: tuple[str, ...] = (
    "gates_applied",
    "settlement_complete",
    "formula_restore_pending",
    "production_formulas_restored",
    "formula_restore_failed",
)


def default_formula_lifecycle_state() -> dict[str, bool]:
    return {k: False for k in FORMULA_LIFECYCLE_KEYS}


def merge_formula_lifecycle(
    existing: dict[str, Any] | None,
    **updates: bool,
) -> dict[str, bool]:
    state = default_formula_lifecycle_state()
    if existing:
        for key in FORMULA_LIFECYCLE_KEYS:
            if key in existing:
                state[key] = bool(existing[key])
    for key, value in updates.items():
        if key not in FORMULA_LIFECYCLE_KEYS:
            raise FormulaLifecycleError(f"Unknown formula lifecycle key: {key!r}")
        state[key] = bool(value)
    if state["production_formulas_restored"] and state["formula_restore_failed"]:
        state["production_formulas_restored"] = False
    if state["production_formulas_restored"]:
        state["formula_restore_pending"] = False
        state["formula_restore_failed"] = False
    return state



class FormulaLifecycleError(RuntimeError):
    """Formula snapshot/verify/restore refused (fail-closed)."""


@dataclass(frozen=True)
class FormulaFieldSnapshot:
    table: str
    field_name: str
    field_id: str
    formula_text: str
    captured_at: str
    result_type: str = "formula"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormulaFieldSnapshot":
        return cls(
            table=str(data["table"]),
            field_name=str(data["field_name"]),
            field_id=str(data.get("field_id") or ""),
            formula_text=str(data["formula_text"]),
            captured_at=str(data.get("captured_at") or ""),
            result_type=str(data.get("result_type") or "formula"),
        )


@dataclass
class FormulaSnapshotBundle:
    snapshots: list[FormulaFieldSnapshot]
    base_id: str = ""
    git_sha: str = ""
    run_id: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_id": self.base_id,
            "git_sha": self.git_sha,
            "run_id": self.run_id,
            "notes": list(self.notes),
            "snapshots": [s.to_dict() for s in self.snapshots],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormulaSnapshotBundle":
        return cls(
            snapshots=[
                FormulaFieldSnapshot.from_dict(row)
                for row in (data.get("snapshots") or [])
            ],
            base_id=str(data.get("base_id") or ""),
            git_sha=str(data.get("git_sha") or ""),
            run_id=str(data.get("run_id") or ""),
            notes=list(data.get("notes") or []),
        )


@dataclass
class FormulaVerifyResult:
    ok: bool
    production_normal: bool
    gated_detected: bool
    field_results: dict[str, dict[str, Any]]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageZRestoreResult:
    attempted: bool
    dry_run: bool
    restored_fields: list[str]
    errors: list[str]
    hooks: dict[str, Any]
    production_formulas_restored: bool = False
    formula_restore_failed: bool = False
    verified_hashes: dict[str, str] = field(default_factory=dict)
    expected_hashes: dict[str, str] = field(default_factory=dict)
    season_sim_remaining: bool = False
    lifecycle: dict[str, bool] = field(default_factory=default_formula_lifecycle_state)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require_formula_confirm(*, allow_writes: bool, confirm: str | None, action: str) -> None:
    if not allow_writes:
        return
    if (confirm or "") != CONFIRM_TOKEN:
        raise FormulaLifecycleError(
            f"{action} requires allow_writes with --confirm \"{CONFIRM_TOKEN}\" exactly; "
            f"got {confirm!r}"
        )


def reject_invalid_formula_text(formula_text: str | None, *, field_name: str) -> None:
    text = (formula_text or "").strip()
    if not text:
        raise FormulaLifecycleError(
            f"Formula for {field_name!r} is empty â€” refuse install/restore"
        )
    if OMNI_FORMULA_FAILURE_STRING in text:
        raise FormulaLifecycleError(
            f"Formula for {field_name!r} contains OMNI failure "
            f"{OMNI_FORMULA_FAILURE_STRING!r} â€” refuse (paste from repo docs)"
        )


def _field_from_meta(
    meta_tables: list[dict[str, Any]],
    table_name: str,
    field_name: str,
) -> dict[str, Any] | None:
    for table in meta_tables:
        if table.get("name") != table_name:
            continue
        for fld in table.get("fields") or []:
            if fld.get("name") == field_name:
                return fld
    return None


def _meta_tables_from_client(client: Any | None) -> list[dict[str, Any]]:
    if client is None:
        return []
    getter = getattr(client, "meta_tables", None)
    if not callable(getter):
        return []
    try:
        return list(getter() or [])
    except Exception:  # noqa: BLE001
        return []


def snapshot_formulas_from_meta(
    meta_tables: list[dict[str, Any]],
    *,
    base_id: str = "",
    git_sha: str = "",
    run_id: str = "",
    fields: tuple[tuple[str, str], ...] = MONITORED_FORMULA_FIELDS,
) -> FormulaSnapshotBundle:
    """Read-only snapshot of exact Production formula text before temporary paste."""
    captured_at = datetime.now(timezone.utc).isoformat()
    snapshots: list[FormulaFieldSnapshot] = []
    notes: list[str] = []

    for table_name, field_name in fields:
        fld = _field_from_meta(meta_tables, table_name, field_name)
        if fld is None:
            notes.append(f"Missing field {table_name}.{field_name} â€” skipped")
            continue
        opts = fld.get("options") or {}
        formula_text = str(opts.get("formula") or "")
        reject_invalid_formula_text(formula_text, field_name=field_name)
        snapshots.append(
            FormulaFieldSnapshot(
                table=table_name,
                field_name=field_name,
                field_id=str(fld.get("id") or ""),
                formula_text=formula_text,
                captured_at=captured_at,
                result_type=str(fld.get("type") or "formula"),
            )
        )

    return FormulaSnapshotBundle(
        snapshots=snapshots,
        base_id=base_id,
        git_sha=git_sha,
        run_id=run_id,
        notes=notes,
    )


def snapshot_formulas(
    client: Any | None,
    *,
    allow_writes: bool = False,
    confirm: str | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Stage 0 hook â€” capture Production formula text before temporary gate paste.

    Read-only by default. Refuses live schema writes (fail-closed).
    """
    _require_formula_confirm(
        allow_writes=allow_writes,
        confirm=confirm,
        action="formula snapshot",
    )
    if allow_writes:
        raise FormulaLifecycleError(
            "snapshot_formulas refuses live writes â€” read-only Meta snapshot only"
        )

    meta_tables = _meta_tables_from_client(client)
    base_id = str(getattr(client, "base_id", "") or "")
    bundle = snapshot_formulas_from_meta(
        meta_tables,
        base_id=base_id,
        run_id=run_id,
    )
    return {
        "status": "ok" if bundle.snapshots else "partial",
        "snapshotted": bool(bundle.snapshots),
        "client_present": client is not None,
        "field_count": len(bundle.snapshots),
        "bundle": bundle.to_dict(),
        "notes": list(bundle.notes),
        "prohibit_omni_formula_generation": True,
    }


def save_formula_snapshot(bundle: FormulaSnapshotBundle, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def load_formula_snapshot(path: Path) -> FormulaSnapshotBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    return FormulaSnapshotBundle.from_dict(data)


def verify_formula_state(
    meta_tables: list[dict[str, Any]],
    *,
    expect_production_normal: bool = True,
    expect_gated: bool = False,
    baseline: FormulaSnapshotBundle | None = None,
) -> FormulaVerifyResult:
    """Verify live formula text is valid and matches expected mode."""
    field_results: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    warnings: list[str] = []
    gated_any = False
    production_any = False

    for table_name, field_name in MONITORED_FORMULA_FIELDS:
        key = f"{table_name}.{field_name}"
        fld = _field_from_meta(meta_tables, table_name, field_name)
        if fld is None:
            field_results[key] = {"present": False}
            if field_name == "Activity Date Is Future?":
                errors.append(f"Missing required formula field {key}")
            continue

        opts = fld.get("options") or {}
        formula_text = str(opts.get("formula") or "")
        try:
            reject_invalid_formula_text(formula_text, field_name=field_name)
        except FormulaLifecycleError as exc:
            errors.append(str(exc))
            field_results[key] = {"present": True, "valid": False, "error": str(exc)}
            continue

        is_gated = formula_text_has_season_sim_gate(formula_text)
        is_production = _is_production_activity_future_formula(field_name, formula_text)
        if is_gated:
            gated_any = True
        if is_production:
            production_any = True

        field_results[key] = {
            "present": True,
            "valid": True,
            "gated": is_gated,
            "production_normal": is_production,
            "length": len(formula_text),
        }

        if baseline:
            snap = next(
                (s for s in baseline.snapshots if s.field_name == field_name),
                None,
            )
            if snap and snap.formula_text != formula_text:
                warnings.append(
                    f"{key} differs from snapshot captured at {snap.captured_at}"
                )

    if expect_production_normal and gated_any:
        errors.append(
            "Production-normal required but Season Sim gate detected in formula text"
        )
    if expect_gated and not gated_any:
        errors.append(
            "Gated formula expected but Season Sim gate not detected "
            "(verify paste from FORMULAS-TO-PASTE.txt â€” not OMNI)"
        )

    ok = not errors
    production_normal = production_any and not gated_any
    return FormulaVerifyResult(
        ok=ok,
        production_normal=production_normal,
        gated_detected=gated_any,
        field_results=field_results,
        errors=errors,
        warnings=warnings,
    )


def stage_f_formula_verify_hook(
    client: Any | None,
    *,
    expect_gated: bool = False,
    snapshot_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stage F hook for execute-three â€” read-only formula verification."""
    meta_tables = _meta_tables_from_client(client)
    baseline = None
    if snapshot_bundle:
        baseline = FormulaSnapshotBundle.from_dict(snapshot_bundle)
    verify = verify_formula_state(
        meta_tables,
        expect_production_normal=not expect_gated,
        expect_gated=expect_gated,
        baseline=baseline,
    )
    return {
        "stage": "F_formula_verify",
        "status": "ok" if verify.ok else "failed",
        "writes": False,
        "verify": verify.to_dict(),
    }


def _is_production_activity_future_formula(field_name: str, formula_text: str) -> bool:
    if field_name != "Activity Date Is Future?":
        return not formula_text_has_season_sim_gate(formula_text)
    normalized = " ".join(formula_text.split())
    prod = " ".join(PRODUCTION_ACTIVITY_DATE_IS_FUTURE_FORMULA.split())
    return prod in normalized or (
        "NOW()" in normalized
        and "Season Sim" not in normalized
        and "SEASON-SIM|" not in normalized
    )


def install_formula_hooks(
    *,
    bundle: FormulaSnapshotBundle | None = None,
    target_mode: str = "gated",
) -> dict[str, Any]:
    """Document install hooks for temporary gated formulas â€” never writes live."""
    gated_targets = {
        "Submissions.Activity Date Is Future?": GATED_ACTIVITY_DATE_IS_FUTURE_FORMULA,
    }
    return {
        "executed": False,
        "target_mode": target_mode,
        "prohibit_omni_formula_generation": True,
        "omni_failure_marker": OMNI_FORMULA_FAILURE_STRING,
        "gated_formula_templates": gated_targets,
        "restore_api_hook": FORMULA_RESTORE_API_HOOK,
        "baseline_snapshot": bundle.to_dict() if bundle else None,
        "operator_steps": [
            "Snapshot Production formulas (snapshot_formulas) before any paste",
            "Paste exact text from tools/season_simulation/FORMULAS-TO-PASTE.txt",
            "Re-run verify_formula_state(expect_gated=True)",
            "On closeout/interrupt: restore_production_formulas / restore_stage_z",
        ],
    }



def _assert_bundle_targets(
    bundle: ProductionNormalBundle,
    *,
    client: Any | None,
) -> list[str]:
    """Return errors if live client base/table/field IDs disagree with bundle."""
    errors: list[str] = []
    if client is not None:
        base_id = str(getattr(client, "base_id", "") or "")
        if base_id and base_id != bundle.base_id:
            errors.append(
                f"base_id mismatch: client={base_id!r} bundle={bundle.base_id!r}"
            )
        if base_id and base_id != DEFAULT_BASE_ID:
            errors.append(
                f"base_id is not Production DEFAULT_BASE_ID={DEFAULT_BASE_ID!r}"
            )
    meta_tables = _meta_tables_from_client(client)
    if not meta_tables:
        return errors
    for fld in bundle.fields:
        live = _field_from_meta(meta_tables, fld.table, fld.field_name)
        if live is None:
            errors.append(f"Missing live field {fld.table}.{fld.field_name}")
            continue
        live_id = str(live.get("id") or "")
        if live_id and live_id != fld.field_id:
            errors.append(
                f"field_id mismatch for {fld.field_name}: "
                f"live={live_id!r} bundle={fld.field_id!r}"
            )
        table_row = next((t for t in meta_tables if t.get("name") == fld.table), None)
        live_table_id = str((table_row or {}).get("id") or "")
        if live_table_id and live_table_id != bundle.table_id:
            errors.append(
                f"table_id mismatch: live={live_table_id!r} bundle={bundle.table_id!r}"
            )
    return errors


def _live_formula_text(
    meta_tables: list[dict[str, Any]],
    *,
    table: str,
    field_name: str,
) -> str:
    fld = _field_from_meta(meta_tables, table, field_name)
    if fld is None:
        return ""
    opts = fld.get("options") or {}
    return str(opts.get("formula") or "")


def verify_production_normal_restored(
    meta_tables: list[dict[str, Any]],
    bundle: ProductionNormalBundle,
) -> tuple[bool, dict[str, str], list[str], bool]:
    """Post-write verification: hashes match + no SEASON-SIM text.

    Returns (ok, verified_hashes, errors, season_sim_remaining).
    """
    errors: list[str] = []
    verified: dict[str, str] = {}
    season_sim_remaining = False
    for fld in bundle.fields:
        live = _live_formula_text(
            meta_tables, table=fld.table, field_name=fld.field_name
        )
        if not live:
            errors.append(f"Missing formula after restore: {fld.field_name}")
            continue
        if formula_text_has_season_sim_gate(live) or "SEASON-SIM" in live:
            season_sim_remaining = True
            errors.append(f"SEASON-SIM text still present on {fld.field_name}")
        digest = formula_sha256(live)
        verified[fld.field_name] = digest
        if digest != fld.sha256:
            errors.append(
                f"Hash mismatch after restore for {fld.field_name}: "
                f"expected={fld.sha256} actual={digest}"
            )
    return (not errors and not season_sim_remaining, verified, errors, season_sim_remaining)


def restore_stage_z(
    bundle: FormulaSnapshotBundle | ProductionNormalBundle | None = None,
    *,
    client: Any | None = None,
    dry_run: bool = True,
    reason: str = "stage_z_closeout",
    allow_writes: bool = False,
    confirm: str | None = None,
    production_bundle: ProductionNormalBundle | None = None,
) -> StageZRestoreResult:
    """Restore Production-normal formulas (Stage Z).

    Always uses the committed Production-normal bundle. A FormulaSnapshotBundle
    argument is accepted only for legacy call sites and is **ignored** as a
    restore source (Stage-0 snapshots are unsafe).
    """
    errors: list[str] = []
    warnings_ignored_snapshot = isinstance(bundle, FormulaSnapshotBundle)

    try:
        prod = production_bundle or load_production_normal_bundle()
    except ProductionNormalBundleError as exc:
        return StageZRestoreResult(
            attempted=True,
            dry_run=True,
            restored_fields=[],
            errors=[str(exc)],
            hooks={**FORMULA_RESTORE_API_HOOK, "reason": reason},
            production_formulas_restored=False,
            formula_restore_failed=True,
            lifecycle=merge_formula_lifecycle(
                None,
                formula_restore_pending=True,
                formula_restore_failed=True,
            ),
        )

    if warnings_ignored_snapshot:
        errors.append(
            "Stage-0 snapshot ignored — restore source is Production-normal bundle only"
        )

    id_errors = _assert_bundle_targets(prod, client=client)
    errors.extend(id_errors)

    expected_hashes = prod.hashes()
    hooks = {
        **FORMULA_RESTORE_API_HOOK,
        "reason": reason,
        "bundle_id": prod.bundle_id,
        "expected_hashes": expected_hashes,
        "ignored_stage0_snapshot": warnings_ignored_snapshot,
    }

    # Dry-run / unconfirmed path — never claim restored.
    live_writes = bool(allow_writes and not dry_run and client is not None)
    if live_writes:
        try:
            _require_formula_confirm(
                allow_writes=True,
                confirm=confirm,
                action="formula restore",
            )
        except FormulaLifecycleError as exc:
            return StageZRestoreResult(
                attempted=True,
                dry_run=True,
                restored_fields=[],
                errors=[str(exc)],
                hooks=hooks,
                production_formulas_restored=False,
                formula_restore_failed=True,
                expected_hashes=expected_hashes,
                lifecycle=merge_formula_lifecycle(
                    None,
                    formula_restore_pending=True,
                    formula_restore_failed=True,
                ),
            )

    if id_errors and live_writes:
        return StageZRestoreResult(
            attempted=True,
            dry_run=False,
            restored_fields=[],
            errors=errors,
            hooks=hooks,
            production_formulas_restored=False,
            formula_restore_failed=True,
            expected_hashes=expected_hashes,
            lifecycle=merge_formula_lifecycle(
                None,
                formula_restore_pending=True,
                formula_restore_failed=True,
            ),
        )

    restored: list[str] = []
    if not live_writes:
        for fld in prod.fields:
            restored.append(f"{fld.table}.{fld.field_name}")
        # Dry-run plans the restore; never sets production_formulas_restored.
        return StageZRestoreResult(
            attempted=True,
            dry_run=True,
            restored_fields=restored,
            errors=[e for e in errors if "Stage-0 snapshot ignored" not in e],
            hooks=hooks,
            production_formulas_restored=False,
            formula_restore_failed=False,
            expected_hashes=expected_hashes,
            lifecycle=merge_formula_lifecycle(
                None,
                formula_restore_pending=True,
            ),
        )

    writer = getattr(client, "update_formula_field", None)
    if not callable(writer):
        return StageZRestoreResult(
            attempted=True,
            dry_run=False,
            restored_fields=[],
            errors=errors
            + ["No update_formula_field on client — cannot perform live Stage Z restore"],
            hooks=hooks,
            production_formulas_restored=False,
            formula_restore_failed=True,
            expected_hashes=expected_hashes,
            lifecycle=merge_formula_lifecycle(
                None,
                formula_restore_pending=True,
                formula_restore_failed=True,
            ),
        )

    # Pre-write hash capture (informational)
    meta_before = _meta_tables_from_client(client)
    pre_hashes = {
        fld.field_name: formula_sha256(
            _live_formula_text(
                meta_before, table=fld.table, field_name=fld.field_name
            )
        )
        for fld in prod.fields
    }
    hooks["pre_write_hashes"] = pre_hashes

    write_errors: list[str] = []
    for fld in prod.fields:
        key = f"{fld.table}.{fld.field_name}"
        try:
            reject_invalid_formula_text(fld.formula_text, field_name=fld.field_name)
            writer(
                table_id=fld.table_id,
                field_id=fld.field_id,
                formula=fld.formula_text,
            )
            restored.append(key)
        except Exception as exc:  # noqa: BLE001
            write_errors.append(f"Restore failed for {key}: {exc}")

    meta_after = _meta_tables_from_client(client)
    ok, verified, verify_errors, season_left = verify_production_normal_restored(
        meta_after, prod
    )
    all_errors = errors + write_errors + verify_errors
    # Drop the informational Stage-0 ignore note from hard failure set when writes ok
    hard_errors = [e for e in all_errors if "Stage-0 snapshot ignored" not in e]

    restored_ok = bool(ok and not write_errors and not hard_errors)
    return StageZRestoreResult(
        attempted=True,
        dry_run=False,
        restored_fields=restored if restored_ok else [],
        errors=hard_errors,
        hooks=hooks,
        production_formulas_restored=restored_ok,
        formula_restore_failed=not restored_ok,
        verified_hashes=verified,
        expected_hashes=expected_hashes,
        season_sim_remaining=season_left,
        lifecycle=merge_formula_lifecycle(
            None,
            gates_applied=True,
            settlement_complete=True,
            formula_restore_pending=not restored_ok,
            production_formulas_restored=restored_ok,
            formula_restore_failed=not restored_ok,
        ),
    )


def restore_production_formulas(
    client: Any | None = None,
    *,
    allow_writes: bool = False,
    confirm: str | None = None,
    snapshot_bundle: dict[str, Any] | FormulaSnapshotBundle | None = None,
    reason: str = "stage_z_closeout",
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Stage Z hook — restore Production-normal formulas after settlement.

    **Keyword-only** after ``client``. Never uses ``snapshot_bundle`` as the
    restore source (Stage-0 may already contain Season Sim gates). Pass
    ``allow_writes=True`` + ``confirm=CONFIRM_TOKEN`` for a live Meta restore.
    """
    _ = snapshot_bundle  # explicitly ignored — Production-normal bundle only
    effective_dry_run = (not allow_writes) if dry_run is None else bool(dry_run)

    try:
        result = restore_stage_z(
            None,
            client=client,
            dry_run=effective_dry_run,
            reason=reason,
            allow_writes=allow_writes,
            confirm=confirm,
        )
    except Exception as exc:  # noqa: BLE001
        # Caught writer / unexpected errors still record restore state correctly.
        failed_lifecycle = merge_formula_lifecycle(
            None,
            formula_restore_pending=True,
            formula_restore_failed=True,
            production_formulas_restored=False,
        )
        return {
            "status": "failed",
            "stage": "Z_formula_restore",
            "restored": False,
            "dry_run": effective_dry_run,
            "client_present": client is not None,
            "production_formulas_restored": False,
            "formula_restore_failed": True,
            "formula_restore_pending": True,
            "errors": [str(exc)],
            "lifecycle": failed_lifecycle,
            "hooks": {**FORMULA_RESTORE_API_HOOK, "reason": reason},
            "restore_source": "production_normal_bundle",
            "ignored_stage0_snapshot": snapshot_bundle is not None,
        }

    status = "ok" if result.production_formulas_restored else (
        "planned" if result.dry_run and not result.formula_restore_failed else "failed"
    )
    return {
        "status": status,
        "stage": "Z_formula_restore",
        "restored": bool(result.production_formulas_restored),
        "dry_run": result.dry_run,
        "client_present": client is not None,
        "restored_fields": list(result.restored_fields),
        "errors": list(result.errors),
        "hooks": result.hooks,
        "production_formulas_restored": bool(result.production_formulas_restored),
        "formula_restore_failed": bool(result.formula_restore_failed),
        "formula_restore_pending": bool(
            result.lifecycle.get("formula_restore_pending")
        ),
        "verified_hashes": dict(result.verified_hashes),
        "expected_hashes": dict(result.expected_hashes),
        "season_sim_remaining": bool(result.season_sim_remaining),
        "lifecycle": dict(result.lifecycle),
        "restore_source": "production_normal_bundle",
        "ignored_stage0_snapshot": snapshot_bundle is not None,
    }


def recover_pending_formula_restore(
    *,
    registry: Any,
    registry_dir: Path,
    client: Any | None,
    allow_writes: bool = False,
    confirm: str | None = None,
) -> dict[str, Any]:
    """Recovery for interrupted/force-killed runs with formula_restore_pending.

    Restores and verifies **only** the three Production-normal formula fields.
    Never deletes simulation data or alters unrelated fields.
    """
    from .run_registry import save_registry

    meta = dict(getattr(registry, "meta", None) or {})
    lifecycle = merge_formula_lifecycle(meta.get("formula_lifecycle"))
    if not lifecycle.get("formula_restore_pending") and lifecycle.get(
        "production_formulas_restored"
    ):
        return {
            "status": "skipped",
            "note": "No pending formula restore on registry",
            "lifecycle": lifecycle,
            "expected_hashes": {},
        }

    try:
        bundle = load_production_normal_bundle()
    except ProductionNormalBundleError as exc:
        return {
            "status": "failed",
            "errors": [str(exc)],
            "lifecycle": merge_formula_lifecycle(
                lifecycle,
                formula_restore_pending=True,
                formula_restore_failed=True,
            ),
        }

    expected = bundle.hashes()
    if not allow_writes:
        return {
            "status": "planned",
            "dry_run": True,
            "note": (
                "Recovery dry-run — pass allow_writes=True and confirm token "
                "to restore Production-normal formulas"
            ),
            "expected_hashes": expected,
            "fields": [f.field_name for f in bundle.fields],
            "lifecycle": lifecycle,
            "run_id": getattr(registry, "run_id", ""),
        }

    result = restore_production_formulas(
        client,
        allow_writes=True,
        confirm=confirm,
        reason="recovery_pending_formula_restore",
        dry_run=False,
    )
    new_lifecycle = merge_formula_lifecycle(
        lifecycle,
        formula_restore_pending=not result.get("production_formulas_restored"),
        production_formulas_restored=bool(result.get("production_formulas_restored")),
        formula_restore_failed=bool(result.get("formula_restore_failed")),
    )
    meta["formula_lifecycle"] = new_lifecycle
    registry.meta = meta
    save_registry(registry, registry_dir)
    return {
        **result,
        "status": "ok" if result.get("production_formulas_restored") else "failed",
        "recovery": True,
        "lifecycle": new_lifecycle,
        "expected_hashes": expected,
    }


class FormulaLifecycleContext(AbstractContextManager["FormulaLifecycleContext"]):
    """Context manager â€” Stage Z restore on __exit__ (always, including errors)."""

    def __init__(
        self,
        bundle: FormulaSnapshotBundle,
        *,
        restore_fn: Callable[..., StageZRestoreResult] | None = None,
        dry_run: bool = True,
        client: Any | None = None,
    ) -> None:
        self.bundle = bundle
        self.restore_fn = restore_fn or restore_stage_z
        self.dry_run = dry_run
        self.client = client
        self.restore_result: StageZRestoreResult | None = None

    def __enter__(self) -> "FormulaLifecycleContext":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        reason = "stage_z_success" if exc_type is None else "stage_z_failure_or_interrupt"
        self.restore_result = self.restore_fn(
            self.bundle,
            client=self.client,
            dry_run=self.dry_run,
            reason=reason,
        )
        return False


__all__ = [
    "FormulaLifecycleError",
    "FormulaFieldSnapshot",
    "FormulaSnapshotBundle",
    "FormulaVerifyResult",
    "StageZRestoreResult",
    "OMNI_FORMULA_FAILURE_STRING",
    "MONITORED_FORMULA_FIELDS",
    "FORMULA_LIFECYCLE_KEYS",
    "default_formula_lifecycle_state",
    "merge_formula_lifecycle",
    "snapshot_formulas",
    "snapshot_formulas_from_meta",
    "restore_production_formulas",
    "restore_stage_z",
    "recover_pending_formula_restore",
    "verify_formula_state",
    "verify_production_normal_restored",
    "stage_f_formula_verify_hook",
    "install_formula_hooks",
    "FormulaLifecycleContext",
    "reject_invalid_formula_text",
    "save_formula_snapshot",
    "load_formula_snapshot",
]

"""Immutable Production-normal formula bundle — sole Stage Z restore source.

Do **not** restore from Stage-0 pre-run snapshots (they may already contain
Season Sim gates). The committed JSON next to this module is the only restore
source for:

* Activity Date Is Future?
* Submitted Same Day?
* Perfect Week Grace Eligible?
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BUNDLE_PATH = Path(__file__).resolve().with_name("production_normal_formulas.json")
BUNDLE_ID = "PRODUCTION-NORMAL-FORMULAS-V1"

EXPECTED_FIELD_NAMES: tuple[str, ...] = (
    "Activity Date Is Future?",
    "Submitted Same Day?",
    "Perfect Week Grace Eligible?",
)


class ProductionNormalBundleError(RuntimeError):
    """Bundle missing, corrupt, or hash-mismatched (fail-closed)."""


@dataclass(frozen=True)
class ProductionNormalField:
    table: str
    table_id: str
    field_name: str
    field_id: str
    formula_text: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "table_id": self.table_id,
            "field_name": self.field_name,
            "field_id": self.field_id,
            "formula_text": self.formula_text,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ProductionNormalBundle:
    bundle_id: str
    base_id: str
    table_id: str
    table_name: str
    fields: tuple[ProductionNormalField, ...]
    immutable: bool = True
    purpose: str = ""
    captured_from: str = ""
    captured_at: str = ""

    def field_by_name(self, name: str) -> ProductionNormalField:
        for fld in self.fields:
            if fld.field_name == name:
                return fld
        raise ProductionNormalBundleError(f"Field {name!r} missing from Production-normal bundle")

    def hashes(self) -> dict[str, str]:
        return {f.field_name: f.sha256 for f in self.fields}

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "immutable": self.immutable,
            "purpose": self.purpose,
            "base_id": self.base_id,
            "table_id": self.table_id,
            "table_name": self.table_name,
            "captured_from": self.captured_from,
            "captured_at": self.captured_at,
            "fields": [f.to_dict() for f in self.fields],
            "hashes": self.hashes(),
        }


def formula_sha256(formula_text: str) -> str:
    return hashlib.sha256((formula_text or "").encode("utf-8")).hexdigest()


def load_production_normal_bundle(
    path: Path | None = None,
) -> ProductionNormalBundle:
    """Load and validate the committed Production-normal formula bundle."""
    bundle_path = path or BUNDLE_PATH
    if not bundle_path.is_file():
        raise ProductionNormalBundleError(
            f"Production-normal formula bundle missing: {bundle_path}"
        )
    try:
        data = json.loads(bundle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionNormalBundleError(
            f"Production-normal formula bundle unreadable: {exc}"
        ) from exc

    if not data.get("immutable"):
        raise ProductionNormalBundleError("Bundle must set immutable=true")
    if str(data.get("bundle_id") or "") != BUNDLE_ID:
        raise ProductionNormalBundleError(
            f"Unexpected bundle_id {data.get('bundle_id')!r}; expected {BUNDLE_ID!r}"
        )

    base_id = str(data.get("base_id") or "")
    table_id = str(data.get("table_id") or "")
    table_name = str(data.get("table_name") or "Submissions")
    if not base_id.startswith("app") or not table_id.startswith("tbl"):
        raise ProductionNormalBundleError("Bundle base_id/table_id invalid")

    raw_fields = list(data.get("fields") or [])
    if len(raw_fields) != len(EXPECTED_FIELD_NAMES):
        raise ProductionNormalBundleError(
            f"Bundle must contain exactly {len(EXPECTED_FIELD_NAMES)} fields; "
            f"got {len(raw_fields)}"
        )

    fields: list[ProductionNormalField] = []
    seen: set[str] = set()
    for row in raw_fields:
        name = str(row.get("field_name") or "")
        formula = str(row.get("formula_text") or "")
        field_id = str(row.get("field_id") or "")
        declared = str(row.get("sha256") or "")
        if name not in EXPECTED_FIELD_NAMES:
            raise ProductionNormalBundleError(f"Unexpected field in bundle: {name!r}")
        if name in seen:
            raise ProductionNormalBundleError(f"Duplicate field in bundle: {name!r}")
        if not field_id.startswith("fld"):
            raise ProductionNormalBundleError(f"Invalid field_id for {name!r}")
        if not formula.strip():
            raise ProductionNormalBundleError(f"Empty formula for {name!r}")
        if "SEASON-SIM" in formula or "Season Sim" in formula:
            raise ProductionNormalBundleError(
                f"Production-normal formula for {name!r} contains Season Sim gate text"
            )
        actual = formula_sha256(formula)
        if declared and declared != actual:
            raise ProductionNormalBundleError(
                f"Hash mismatch for {name!r}: declared={declared} actual={actual}"
            )
        seen.add(name)
        fields.append(
            ProductionNormalField(
                table=str(row.get("table") or table_name),
                table_id=str(row.get("table_id") or table_id),
                field_name=name,
                field_id=field_id,
                formula_text=formula,
                sha256=actual,
            )
        )

    missing = [n for n in EXPECTED_FIELD_NAMES if n not in seen]
    if missing:
        raise ProductionNormalBundleError(f"Bundle missing fields: {missing}")

    return ProductionNormalBundle(
        bundle_id=BUNDLE_ID,
        base_id=base_id,
        table_id=table_id,
        table_name=table_name,
        fields=tuple(fields),
        immutable=True,
        purpose=str(data.get("purpose") or ""),
        captured_from=str(data.get("captured_from") or ""),
        captured_at=str(data.get("captured_at") or ""),
    )


__all__ = [
    "BUNDLE_ID",
    "BUNDLE_PATH",
    "EXPECTED_FIELD_NAMES",
    "ProductionNormalBundle",
    "ProductionNormalBundleError",
    "ProductionNormalField",
    "formula_sha256",
    "load_production_normal_bundle",
]

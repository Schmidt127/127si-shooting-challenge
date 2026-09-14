"""Shared active-XP Source Key integrity gate.

Used by final business reconciliation and the read-only reconciliation checker.
Only **active** XP Events are evaluated. Inactive events with blank keys must
not fail.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

CANONICAL_HOMEWORK_PREFIX = "HOMEWORK_XP|"
LEGACY_HOMEWORK_PREFIX = "HOMEWORK_COMPLETION|"


@dataclass
class SourceKeyIntegrityIssue:
    code: str
    message: str
    event_ids: list[str] = field(default_factory=list)
    evidence: str = ""
    source_key: str = ""

    def to_error_string(self) -> str:
        ids = ",".join(self.event_ids) if self.event_ids else "(none)"
        return (
            f"{self.code}: event_ids=[{ids}] "
            f"evidence={self.evidence or self.message}"
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActiveXpSourceKeyIntegrityResult:
    ok: bool
    issues: list[SourceKeyIntegrityIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[str]:
        return [i.to_error_string() for i in self.issues]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
            "errors": self.errors,
        }


def _fields(ev: dict[str, Any]) -> dict[str, Any]:
    f = ev.get("fields")
    return f if isinstance(f, dict) else ev


def _event_id(ev: dict[str, Any]) -> str:
    rid = ev.get("id")
    if rid:
        return str(rid)
    f = _fields(ev)
    for key in ("id", "record_id", "Record ID"):
        if f.get(key):
            return str(f[key])
    return "(missing-id)"


def _is_active_xp_event(fields: dict[str, Any]) -> bool:
    """Match Production Active XP Points: only truthy Active? counts."""
    status = str(fields.get("Status") or "").lower()
    if status in {"void", "inactive", "duplicate", "superseded"}:
        return False
    return fields.get("Active?") is True


def _raw_source_key(fields: dict[str, Any]) -> str:
    """Return Source Key as stored (preserve whitespace; None → empty)."""
    val = fields.get("Source Key")
    if val is None:
        return ""
    return str(val)


def validate_active_xp_source_keys(
    events: Sequence[dict[str, Any]],
) -> ActiveXpSourceKeyIntegrityResult:
    """Fail-closed integrity checks for active XP Event Source Keys.

    Failures (active events only):
    1. Blank or whitespace-only Source Key
    2. Exact duplicate Source Key (after strip of non-blank keys)
    3. Both HOMEWORK_XP|{hcId} and HOMEWORK_COMPLETION|{hcId} active
    """
    issues: list[SourceKeyIntegrityIssue] = []

    active_rows: list[tuple[str, dict[str, Any], str]] = []
    for ev in events:
        f = _fields(ev)
        if not _is_active_xp_event(f):
            continue
        eid = _event_id(ev)
        active_rows.append((eid, f, _raw_source_key(f)))

    # 1) Blank / whitespace Source Key
    for eid, _f, raw in active_rows:
        if raw.strip() == "":
            kind = "whitespace" if raw else "blank"
            issues.append(
                SourceKeyIntegrityIssue(
                    code="blank_or_whitespace_source_key",
                    message=f"active XP Event has {kind} Source Key",
                    event_ids=[eid],
                    evidence=f"raw_source_key={raw!r} kind={kind}",
                )
            )

    # 2) Exact duplicate Source Key (non-blank after strip; exact string match
    #    on stripped key so "KEY" duplicates collide; blank already reported)
    by_key: dict[str, list[str]] = defaultdict(list)
    for eid, _f, raw in active_rows:
        stripped = raw.strip()
        if not stripped:
            continue
        by_key[stripped].append(eid)

    for key, eids in sorted(by_key.items()):
        if len(eids) > 1:
            issues.append(
                SourceKeyIntegrityIssue(
                    code="duplicate_source_key",
                    message=f"exact duplicate active Source Key {key!r}",
                    event_ids=list(eids),
                    evidence=f"source_key={key!r} count={len(eids)}",
                    source_key=key,
                )
            )

    # 3) Legacy + canonical Homework XP for the same Homework Completion
    hw_canonical: dict[str, list[str]] = defaultdict(list)
    hw_legacy: dict[str, list[str]] = defaultdict(list)
    for eid, _f, raw in active_rows:
        stripped = raw.strip()
        if stripped.startswith(CANONICAL_HOMEWORK_PREFIX):
            hc_id = stripped[len(CANONICAL_HOMEWORK_PREFIX) :]
            if hc_id:
                hw_canonical[hc_id].append(eid)
        elif stripped.startswith(LEGACY_HOMEWORK_PREFIX):
            hc_id = stripped[len(LEGACY_HOMEWORK_PREFIX) :]
            if hc_id:
                hw_legacy[hc_id].append(eid)

    for hc_id in sorted(set(hw_canonical) & set(hw_legacy)):
        eids = list(dict.fromkeys(hw_canonical[hc_id] + hw_legacy[hc_id]))
        canon_key = f"{CANONICAL_HOMEWORK_PREFIX}{hc_id}"
        legacy_key = f"{LEGACY_HOMEWORK_PREFIX}{hc_id}"
        issues.append(
            SourceKeyIntegrityIssue(
                code="homework_legacy_plus_canonical",
                message=(
                    f"both {canon_key!r} and {legacy_key!r} active "
                    f"for Homework Completion {hc_id}"
                ),
                event_ids=eids,
                evidence=(
                    f"homework_completion_id={hc_id} "
                    f"canonical_key={canon_key!r} legacy_key={legacy_key!r}"
                ),
                source_key=canon_key,
            )
        )

    return ActiveXpSourceKeyIntegrityResult(ok=not issues, issues=issues)


def duplicate_active_source_keys(
    events: Sequence[dict[str, Any]],
) -> dict[str, int]:
    """Map of active Source Key → count for keys with count > 1.

    Uses the same active/strip rules as ``validate_active_xp_source_keys``.
    """
    by_key: dict[str, list[str]] = defaultdict(list)
    for ev in events:
        f = _fields(ev)
        if not _is_active_xp_event(f):
            continue
        stripped = _raw_source_key(f).strip()
        if not stripped:
            continue
        by_key[stripped].append(_event_id(ev))
    return {k: len(ids) for k, ids in by_key.items() if len(ids) > 1}


__all__ = [
    "CANONICAL_HOMEWORK_PREFIX",
    "LEGACY_HOMEWORK_PREFIX",
    "ActiveXpSourceKeyIntegrityResult",
    "SourceKeyIntegrityIssue",
    "duplicate_active_source_keys",
    "validate_active_xp_source_keys",
]

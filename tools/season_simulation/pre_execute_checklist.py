"""Pre-execute Email/Hub checklist (read-only + operator attestations).

Does not read or write Airtable UI-only input variables (e.g. 079 ingressSecret).
Operator must visually attest those immediately before email-enabled execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .constants import SAFE_EMAIL_RECIPIENT
from .simulation_process_lock import read_lock, default_lock_path


@dataclass
class ChecklistItem:
    name: str
    ok: bool
    detail: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreExecuteChecklistReport:
    ok: bool
    items: list[ChecklistItem] = field(default_factory=list)
    stop_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "items": [i.to_dict() for i in self.items],
            "stop_reasons": list(self.stop_reasons),
        }


def run_pre_execute_email_hub_checklist(
    *,
    registry_dir: Path | None = None,
    run_id: str = "",
    allowlist_recipient: str = SAFE_EMAIL_RECIPIENT,
    ehq_backlog_count: int = 0,
    hub_transactional_backlog_count: int = 0,
    enable_email_delivery: bool = False,
    attest_079_ingress_secret: bool = False,
    attest_producer_input_modes: bool = False,
    single_process_ok: bool | None = None,
) -> PreExecuteChecklistReport:
    """Build fail-closed pre-execute checklist for Email/Hub safety."""
    items: list[ChecklistItem] = []
    stops: list[str] = []

    # 1) Single simulation process
    if single_process_ok is None and registry_dir is not None:
        lock = read_lock(default_lock_path(registry_dir))
        if lock is None:
            single_process_ok = True
            detail = "no execute lock held"
        elif run_id and lock.run_id == run_id:
            single_process_ok = True
            detail = f"lock held by this run_id={run_id!r}"
        else:
            single_process_ok = False
            detail = (
                f"competing lock pid={lock.pid} run_id={lock.run_id!r} "
                f"acquired_at={lock.acquired_at}"
            )
    elif single_process_ok is None:
        single_process_ok = True
        detail = "single_process not checked (no registry_dir)"
    else:
        detail = "single_process_ok supplied by caller"

    items.append(
        ChecklistItem(
            name="single_simulation_process",
            ok=bool(single_process_ok),
            detail=detail,
        )
    )
    if not single_process_ok:
        stops.append("Only one simulation process may run")

    # 2) Sole allowed recipient
    ok_allow = (allowlist_recipient or "").strip().lower() == SAFE_EMAIL_RECIPIENT.lower()
    items.append(
        ChecklistItem(
            name="allowlist_sole_recipient",
            ok=ok_allow,
            detail=f"allowlist={allowlist_recipient!r} required={SAFE_EMAIL_RECIPIENT!r}",
        )
    )
    if not ok_allow:
        stops.append(f"Sole allowed recipient must be {SAFE_EMAIL_RECIPIENT}")

    # 3) EHQ backlog zero
    ok_ehq = int(ehq_backlog_count) == 0
    items.append(
        ChecklistItem(
            name="ehq_backlog_zero",
            ok=ok_ehq,
            detail=f"ehq_backlog_count={ehq_backlog_count}",
        )
    )
    if not ok_ehq:
        stops.append("Email Handoff Queue transactional backlog must be zero")

    # 4) Hub transactional backlog zero
    ok_hub = int(hub_transactional_backlog_count) == 0
    items.append(
        ChecklistItem(
            name="hub_transactional_backlog_zero",
            ok=ok_hub,
            detail=f"hub_transactional_backlog_count={hub_transactional_backlog_count}",
        )
    )
    if not ok_hub:
        stops.append("Communications Hub transactional backlog must be zero")

    # 5–6) Visual attestations (required when email delivery enabled)
    if enable_email_delivery:
        items.append(
            ChecklistItem(
                name="attest_079_ingress_secret",
                ok=bool(attest_079_ingress_secret),
                detail=(
                    "Operator must visually attest 079 ingressSecret in Airtable UI "
                    "(API cannot read UI-only input variables)"
                ),
            )
        )
        if not attest_079_ingress_secret:
            stops.append(
                "Email-enabled execute requires --attest-079-ingress-secret "
                "(visual UI attestation)"
            )
        items.append(
            ChecklistItem(
                name="attest_producer_input_modes",
                ok=bool(attest_producer_input_modes),
                detail=(
                    "Operator must visually attest producer input modes immediately "
                    "before email-enabled execution"
                ),
            )
        )
        if not attest_producer_input_modes:
            stops.append(
                "Email-enabled execute requires --attest-producer-input-modes "
                "(visual UI attestation)"
            )
    else:
        items.append(
            ChecklistItem(
                name="email_delivery_off",
                ok=True,
                detail="enable_email_delivery=False — 079/producer attestations not required",
                required=False,
            )
        )

    ok = not stops
    return PreExecuteChecklistReport(ok=ok, items=items, stop_reasons=stops)


__all__ = [
    "ChecklistItem",
    "PreExecuteChecklistReport",
    "run_pre_execute_email_hub_checklist",
]

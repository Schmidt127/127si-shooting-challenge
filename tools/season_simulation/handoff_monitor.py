"""Email Handoff Queue baseline + delta monitoring for season simulation runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .season_sim_email_suppression import HandoffBaseline, handoff_row_is_run_attributable


@dataclass
class HandoffMonitorResult:
    ok: bool
    baseline: HandoffBaseline
    current_run_attributable: int
    new_row_ids: list[str]
    new_rows: list[dict[str, Any]]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "baseline": {
                "run_id": self.baseline.run_id,
                "total_queue_rows": self.baseline.total_queue_rows,
                "run_attributable_rows": self.baseline.run_attributable_rows,
                "captured_at": self.baseline.captured_at,
            },
            "current_run_attributable": self.current_run_attributable,
            "new_row_ids": self.new_row_ids,
            "new_rows": self.new_rows,
            "errors": self.errors,
        }


def _list_all_handoffs(client: Any) -> list[dict[str, Any]]:
    return client.list_records(
        "Email Handoff Queue",
        fields=["Handoff Key", "Status", "Event Type", "Created", "Payload JSON", "Source Record ID"],
    )


def capture_handoff_baseline(client: Any, *, run_id: str) -> HandoffBaseline:
    rows = _list_all_handoffs(client)
    run_rows = [r for r in rows if handoff_row_is_run_attributable(r.get("fields") or {}, run_id)]
    return HandoffBaseline(
        run_id=run_id,
        total_queue_rows=len(rows),
        run_attributable_rows=len(run_rows),
        captured_at=datetime.now(timezone.utc).isoformat(),
        row_ids=frozenset(r["id"] for r in rows),
    )


def verify_no_new_run_handoffs(
    client: Any,
    *,
    baseline: HandoffBaseline,
    run_id: str,
    strict_any_new_row: bool = False,
) -> HandoffMonitorResult:
    rows = _list_all_handoffs(client)
    current_ids = {r["id"] for r in rows}
    new_ids = sorted(baseline.delta(current_ids=current_ids))
    new_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for rid in new_ids:
        row = next(r for r in rows if r["id"] == rid)
        fields = row.get("fields") or {}
        attributable = handoff_row_is_run_attributable(fields, run_id)
        if strict_any_new_row or attributable:
            new_rows.append(
                {
                    "id": rid,
                    "handoff_key": fields.get("Handoff Key"),
                    "status": fields.get("Status"),
                    "event_type": fields.get("Event Type"),
                    "created": fields.get("Created"),
                    "run_attributable": attributable,
                }
            )
    if new_rows:
        mode = "any new queue row(s)" if strict_any_new_row else "run-attributable row(s)"
        errors.append(
            f"Email Handoff Queue increased by {len(new_rows)} {mode}: "
            + ", ".join(f"{r['handoff_key']} ({r['id']})" for r in new_rows[:5])
        )
    run_rows = [r for r in rows if handoff_row_is_run_attributable(r.get("fields") or {}, run_id)]
    return HandoffMonitorResult(
        ok=not new_rows,
        baseline=baseline,
        current_run_attributable=len(run_rows),
        new_row_ids=new_ids,
        new_rows=new_rows,
        errors=errors,
    )

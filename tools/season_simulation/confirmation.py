"""Confirmation token gating for execute / cleanup."""

from __future__ import annotations

from .constants import (
    CONFIRM_CLEANUP_TOKEN,
    CONFIRM_DISPOSABLE_TOKEN,
    CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN,
    CONFIRM_THREE_ATHLETE_TOKEN,
    CONFIRM_TOKEN,
    THREE_ATHLETE_AUTHORIZATION_PHRASE,
    THREE_ATHLETE_RUN_SUFFIX,
)
from .run_registry import is_valid_run_id_prefix


class ConfirmationError(RuntimeError):
    pass


def require_confirmation(
    *,
    execute: bool,
    confirm: str | None,
    action: str,
) -> None:
    if not execute:
        raise ConfirmationError(
            f"{action} requires --execute (dry-run is the default)"
        )
    if (confirm or "") != CONFIRM_TOKEN:
        raise ConfirmationError(
            f"{action} requires --confirm \"{CONFIRM_TOKEN}\" exactly; "
            f"got {confirm!r}"
        )


def require_execute_gates(
    *,
    execute: bool,
    confirm: str | None,
    confirm_disposable: str | None,
    simulation_id: str | None,
    action: str = "season simulation execute",
) -> None:
    """Execute requires --execute, --confirm, --confirm-disposable, and --simulation-id."""
    require_confirmation(execute=execute, confirm=confirm, action=action)
    if (confirm_disposable or "") != CONFIRM_DISPOSABLE_TOKEN:
        raise ConfirmationError(
            f"{action} requires --confirm-disposable \"{CONFIRM_DISPOSABLE_TOKEN}\" "
            f"exactly; got {confirm_disposable!r}"
        )
    sid = (simulation_id or "").strip()
    if not is_valid_run_id_prefix(sid):
        raise ConfirmationError(
            f"{action} requires --simulation-id starting with SEASON-SIM-2027- "
            f"or SEASON-SIM-PERFECT-; got {simulation_id!r}"
        )


def require_cleanup_gates(
    *,
    execute: bool,
    confirm: str | None,
    confirm_cleanup: str | None,
    simulation_id: str | None,
    action: str = "season simulation cleanup",
) -> None:
    """Cleanup deletes require --execute, --confirm, --confirm-cleanup, and --simulation-id."""
    require_confirmation(execute=execute, confirm=confirm, action=action)
    if (confirm_cleanup or "") != CONFIRM_CLEANUP_TOKEN:
        raise ConfirmationError(
            f"{action} requires --confirm-cleanup \"{CONFIRM_CLEANUP_TOKEN}\" "
            f"exactly; got {confirm_cleanup!r}"
        )
    sid = (simulation_id or "").strip()
    if not is_valid_run_id_prefix(sid):
        raise ConfirmationError(
            f"{action} requires --simulation-id / --run-id starting with "
            f"SEASON-SIM-2027- or SEASON-SIM-PERFECT-; got {simulation_id!r}"
        )


INCOMPLETE_CLEANUP_STATUSES = frozenset(
    {"paused", "failed", "incomplete", "error", "interrupted"}
)


def require_incomplete_cleanup_force(
    *,
    registry_status: str | None,
    confirm_force_incomplete: str | None,
    action: str = "season simulation cleanup",
) -> None:
    """Refuse cleanup of failed/incomplete runs without an extra force token.

    Cleanup never runs automatically after execute. Paused/failed registries
    require Mike-authorized ``CONFIRM-FORCE-CLEANUP-INCOMPLETE-SEASON-SIM``.
    """
    status = str(registry_status or "").strip().lower()
    if status not in INCOMPLETE_CLEANUP_STATUSES:
        return
    if (confirm_force_incomplete or "") != CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN:
        raise ConfirmationError(
            f"{action} for registry status {status!r} requires "
            f"--confirm-force-incomplete-cleanup "
            f"\"{CONFIRM_FORCE_INCOMPLETE_CLEANUP_TOKEN}\" exactly; "
            f"got {confirm_force_incomplete!r}. "
            "Cleanup is never automatic after a failed or incomplete simulation."
        )


def is_confirmed(*, execute: bool, confirm: str | None) -> bool:
    return bool(execute) and (confirm or "") == CONFIRM_TOKEN


def is_execute_fully_gated(
    *,
    execute: bool,
    confirm: str | None,
    confirm_disposable: str | None,
    simulation_id: str | None,
) -> bool:
    try:
        require_execute_gates(
            execute=execute,
            confirm=confirm,
            confirm_disposable=confirm_disposable,
            simulation_id=simulation_id,
        )
        return True
    except ConfirmationError:
        return False


def require_three_athlete_execute_gates(
    *,
    execute: bool,
    confirm: str | None,
    confirm_disposable: str | None,
    confirm_three_athlete: str | None,
    authorization_phrase: str | None,
    simulation_id: str | None,
    action: str = "three-athlete season simulation execute",
) -> None:
    """SC-SEASON-SIM-001 execute — stricter than single-athlete SC-002."""
    require_execute_gates(
        execute=execute,
        confirm=confirm,
        confirm_disposable=confirm_disposable,
        simulation_id=simulation_id,
        action=action,
    )
    if (confirm_three_athlete or "") != CONFIRM_THREE_ATHLETE_TOKEN:
        raise ConfirmationError(
            f"{action} requires --confirm-three-athlete "
            f"\"{CONFIRM_THREE_ATHLETE_TOKEN}\" exactly; "
            f"got {confirm_three_athlete!r}"
        )
    if (authorization_phrase or "").strip() != THREE_ATHLETE_AUTHORIZATION_PHRASE:
        raise ConfirmationError(
            f"{action} requires --authorization-phrase "
            f"\"{THREE_ATHLETE_AUTHORIZATION_PHRASE}\" exactly; "
            f"got {authorization_phrase!r}"
        )
    sid = (simulation_id or "").strip()
    if THREE_ATHLETE_RUN_SUFFIX not in sid:
        raise ConfirmationError(
            f"{action} requires --simulation-id containing "
            f"\"{THREE_ATHLETE_RUN_SUFFIX}\"; got {simulation_id!r}"
        )


def is_three_athlete_execute_gated(
    *,
    execute: bool,
    confirm: str | None,
    confirm_disposable: str | None,
    confirm_three_athlete: str | None,
    authorization_phrase: str | None,
    simulation_id: str | None,
) -> bool:
    try:
        require_three_athlete_execute_gates(
            execute=execute,
            confirm=confirm,
            confirm_disposable=confirm_disposable,
            confirm_three_athlete=confirm_three_athlete,
            authorization_phrase=authorization_phrase,
            simulation_id=simulation_id,
        )
        return True
    except ConfirmationError:
        return False

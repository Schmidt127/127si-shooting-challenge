"""Single-process guard for season simulation execute.

Only one simulation process may hold the lock. Force-killed processes leave a
stale PID file that must be cleared explicitly — never silent concurrent runs.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SimulationProcessLockError(RuntimeError):
    """Another simulation process holds (or appears to hold) the lock."""


@dataclass
class ProcessLockInfo:
    pid: int
    run_id: str
    acquired_at: str
    lock_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_lock_path(registry_dir: Path) -> Path:
    return Path(registry_dir) / ".season-sim-execute.lock"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we cannot signal it — treat as alive.
        return True
    except OSError:
        return False
    return True


def read_lock(lock_path: Path) -> ProcessLockInfo | None:
    if not lock_path.is_file():
        return None
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return ProcessLockInfo(
            pid=int(data.get("pid") or 0),
            run_id=str(data.get("run_id") or ""),
            acquired_at=str(data.get("acquired_at") or ""),
            lock_path=str(lock_path),
        )
    except (TypeError, ValueError):
        return None


def acquire_simulation_lock(
    *,
    registry_dir: Path,
    run_id: str,
    lock_path: Path | None = None,
    pid: int | None = None,
) -> ProcessLockInfo:
    """Acquire exclusive execute lock (fail-closed if another live process holds it)."""
    path = lock_path or default_lock_path(registry_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_lock(path)
    my_pid = int(pid if pid is not None else os.getpid())
    if existing is not None:
        if existing.pid == my_pid and existing.run_id == run_id:
            return existing
        if _pid_alive(existing.pid):
            raise SimulationProcessLockError(
                f"Another simulation process holds the lock: "
                f"pid={existing.pid} run_id={existing.run_id!r} "
                f"acquired_at={existing.acquired_at}"
            )
        # Stale lock from dead process — replace.
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise SimulationProcessLockError(
                f"Stale lock present but could not clear {path}: {exc}"
            ) from exc

    info = ProcessLockInfo(
        pid=my_pid,
        run_id=run_id,
        acquired_at=datetime.now(timezone.utc).isoformat(),
        lock_path=str(path),
    )
    # Exclusive create when possible.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as exc:
        other = read_lock(path)
        raise SimulationProcessLockError(
            f"Lock race: {path} already exists ({other})"
        ) from exc
    try:
        os.write(fd, (json.dumps(info.to_dict(), indent=2) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return info


def release_simulation_lock(
    *,
    registry_dir: Path,
    run_id: str,
    lock_path: Path | None = None,
    pid: int | None = None,
) -> bool:
    """Release lock if owned by this pid/run_id. Returns True when removed."""
    path = lock_path or default_lock_path(registry_dir)
    existing = read_lock(path)
    if existing is None:
        return False
    my_pid = int(pid if pid is not None else os.getpid())
    if existing.pid != my_pid or existing.run_id != run_id:
        return False
    path.unlink(missing_ok=True)
    return True


__all__ = [
    "ProcessLockInfo",
    "SimulationProcessLockError",
    "acquire_simulation_lock",
    "default_lock_path",
    "read_lock",
    "release_simulation_lock",
]

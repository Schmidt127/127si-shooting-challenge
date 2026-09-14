#!/usr/bin/env python3
"""ASCII-normalize 035 comments and bump to v1.7 (hash consistency)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = (
    ROOT
    / "airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js"
)

REPL = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2192": "->",  # arrow
}


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    changes = []
    out_chars: list[str] = []
    for i, ch in enumerate(text):
        if ch in REPL:
            line = text.count("\n", 0, i) + 1
            ls = text.rfind("\n", 0, i) + 1
            le = text.find("\n", i)
            if le < 0:
                le = len(text)
            line_text = text[ls:le]
            stripped = line_text.lstrip()
            kind = (
                "comment"
                if (
                    stripped.startswith(("//", "*", "/*"))
                    or line_text.startswith("Status:")
                    or line_text.startswith("/*")
                    or line_text.startswith(" *")
                )
                else "OTHER"
            )
            if kind != "comment":
                raise SystemExit(f"Refusing non-comment replacement at line {line}: {line_text!r}")
            changes.append(
                {
                    "line": line,
                    "from": f"U+{ord(ch):04X}",
                    "to": REPL[ch],
                    "kind": kind,
                    "line_preview": line_text[:140],
                }
            )
            out_chars.append(REPL[ch])
        else:
            out_chars.append(ch)

    ascii_text = "".join(out_chars)
    if any(ord(c) > 127 for c in ascii_text):
        bad = sorted({f"U+{ord(c):04X}" for c in ascii_text if ord(c) > 127})
        raise SystemExit(f"Non-ASCII remain: {bad}")

    old_hist = (
        " * VERSION HISTORY\n"
        " * - v1.6 (2026-09-13): SC-SEASON-SIM-001-DEPLOY-20260913C - progressive tier state"
    )
    new_hist = (
        " * VERSION HISTORY\n"
        " * - v1.7 (2026-09-14): SC-SEASON-SIM-001-DEPLOY-20260914D - ASCII/comment normalization\n"
        " *   and live-hash consistency. Replaced non-ASCII punctuation in comments/headers\n"
        " *   only (em dash -> '-', en dash -> '-', arrow -> '->'). Executable behavior\n"
        " *   unchanged from v1.6.\n"
        " * - v1.6 (2026-09-13): SC-SEASON-SIM-001-DEPLOY-20260913C - progressive tier state"
    )
    if old_hist not in ascii_text:
        raise SystemExit("version history anchor missing after ASCII normalize")
    ascii_text = ascii_text.replace(old_hist, new_hist, 1)

    replacements = [
        ("* Version: v1.6\n", "* Version: v1.7\n"),
        ("* Last Updated: 2026-09-13\n", "* Last Updated: 2026-09-14\n"),
        (
            "Last GitHub Update: 2026-09-14 (synced from Mike-attested live Production v1.6)",
            "Last GitHub Update: 2026-09-14 (v1.7 ASCII/comment hash consistency)",
        ),
        ('version: "v1.6"', 'version: "v1.7"'),
        ('versionDate: "2026-09-13"', 'versionDate: "2026-09-14"'),
        ('lastUpdated: "2026-09-13"', 'lastUpdated: "2026-09-14"'),
        (
            'deployMarker: "SC-SEASON-SIM-001-DEPLOY-20260913C"',
            'deployMarker: "SC-SEASON-SIM-001-DEPLOY-20260914D"',
        ),
    ]
    for old, new in replacements:
        if old not in ascii_text:
            raise SystemExit(f"missing expected text: {old!r}")
        ascii_text = ascii_text.replace(old, new, 1)

    if "v1.7" not in ascii_text or "DEPLOY-20260914D" not in ascii_text:
        raise SystemExit("version bump failed")
    if any(ord(c) > 127 for c in ascii_text):
        raise SystemExit("non-ASCII after version bump")

    # Normalize to LF.
    ascii_text = ascii_text.replace("\r\n", "\n").replace("\r", "\n")
    if not ascii_text.endswith("\n"):
        ascii_text += "\n"
    PATH.write_text(ascii_text, encoding="utf-8", newline="\n")

    sha = hashlib.sha256(ascii_text.encode("utf-8")).hexdigest()
    report = {
        "path": str(PATH.relative_to(ROOT)).replace("\\", "/"),
        "change_count": len(changes),
        "changes": changes,
        "sha256": sha,
        "length": len(ascii_text),
        "version": "v1.7",
        "deployMarker": "SC-SEASON-SIM-001-DEPLOY-20260914D",
    }
    out_dir = ROOT / "docs/audits/readiness-20260914"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "035-v1.7-ascii-normalize-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "sha256": sha, "changes": len(changes)}, indent=2))


if __name__ == "__main__":
    main()

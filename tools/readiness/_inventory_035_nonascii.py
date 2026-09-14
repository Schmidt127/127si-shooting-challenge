#!/usr/bin/env python3
"""Inventory non-ASCII codepoints in 035 source (read-only)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / "airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js"
text = PATH.read_text(encoding="utf-8")
rows = []
for i, ch in enumerate(text):
    if ord(ch) > 127:
        line = text.count("\n", 0, i) + 1
        rows.append(
            {
                "index": i,
                "line": line,
                "codepoint": f"U+{ord(ch):04X}",
                "char": ch,
                "context": text[max(0, i - 50) : i + 50],
            }
        )
out = {"path": str(PATH), "count": len(rows), "rows": rows}
print(json.dumps(out, ensure_ascii=True, indent=2))
Path("docs/audits/readiness-20260914/035-nonascii-inventory.json").write_text(
    json.dumps(out, ensure_ascii=True, indent=2), encoding="utf-8"
)

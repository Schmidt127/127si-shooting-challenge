#!/usr/bin/env python3
import json
import re
from pathlib import Path

root = Path("airtable/automations/shooting-challenge")
rows = []
for p in sorted(root.glob("*.js")):
    if not re.match(r"^\d{3}-", p.name):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"scriptId:\s*['\"]([^'\"]+)['\"]", t)
    v = re.search(r"version:\s*['\"]([^'\"]+)['\"]", t)
    if not v:
        v = re.search(r"Version:\s*([0-9.]+)", t)
    rows.append(
        {
            "file": p.name,
            "scriptId": m.group(1) if m else p.stem.split("-")[0],
            "version": v.group(1) if v else None,
        }
    )
out = Path("docs/audits/readiness-20260914/github-automation-versions.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(f"wrote {len(rows)} -> {out}")

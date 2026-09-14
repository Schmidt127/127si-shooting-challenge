"""Read-only live verification of Automation 057 code header (no paste)."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from season_simulation.airtable_client import AirtableClient  # noqa: E402

GITHUB = (
    ROOT
    / "airtable"
    / "automations"
    / "shooting-challenge"
    / "057-achievements-and-milestones-calculate-perfect-week-eligibility.js"
)


def main() -> int:
    gh = GITHUB.read_text(encoding="utf-8")
    gh_ver = None
    m = re.search(r"^\s*\*\s*Version:\s*([0-9.]+)", gh, re.M)
    if m:
        gh_ver = m.group(1)
    gh_hash = hashlib.sha256(gh.encode("utf-8")).hexdigest()

    client = AirtableClient(allow_writes=False)
    rows = client.list_records(
        "Automations",
        fields=["Name", "Automation Code", "Status"],
    )
    matches = []
    for r in rows:
        f = r.get("fields") or {}
        name = str(f.get("Name") or "")
        if "057" in name and "Perfect Week" in name:
            matches.append(f)

    print("github_version", gh_ver)
    print("github_sha256", gh_hash)
    print("live_matches", len(matches))
    if not matches:
        print("VERDICT BLOCKER_NO_LIVE_057_ROW")
        return 2

    code = str(matches[0].get("Automation Code") or "")
    live_ver = None
    m2 = re.search(r"Version:\s*v?([0-9.]+)", code)
    if m2:
        live_ver = m2.group(1)
    # Prefer SCRIPT metadata if present
    m3 = re.search(r'version:\s*"v?([0-9.]+)"', code)
    if m3:
        live_ver = m3.group(1)
    live_hash = hashlib.sha256(code.encode("utf-8")).hexdigest() if code else ""
    print("live_name", matches[0].get("Name"))
    print("live_status", matches[0].get("Status"))
    print("live_version", live_ver)
    print("live_code_sha256", live_hash)
    print("live_code_len", len(code))
    print("code_preview", code[:240].replace("\n", " | "))

    if live_ver == "2.7" or live_ver == "v2.7":
        print("VERDICT 057_LIVE_V2_7_OK")
        return 0
    print("VERDICT BLOCKER_057_NOT_V2_7")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

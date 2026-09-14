#!/usr/bin/env python3
"""Create 035 v1.7 paste/mirror bundles and prove executable unchanged."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = (
    ROOT
    / "airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js"
)
PASTE = ROOT / "docs/deploy-checklists/035-v1.7-PASTE.txt"
MIRROR = ROOT / "docs/audits/readiness-20260914/035-v1.7-AUTOMATIONS-TABLE-MIRROR.txt"
PROOF = ROOT / "docs/audits/readiness-20260914/035-v1.7-executable-unchanged-proof.json"

UNICODE_REPL = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2192": "->",
}


def strip_block_and_line_comments(source: str) -> str:
    """Remove /* */ and // comments without touching string/template literals."""
    out: list[str] = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        # string or template literal
        if ch in ('"', "'", "`"):
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                c = source[i]
                out.append(c)
                if c == "\\" and i + 1 < n:
                    out.append(source[i + 1])
                    i += 2
                    continue
                # template literal interpolation — skip nested ${ ... }
                if quote == "`" and c == "$" and i + 1 < n and source[i + 1] == "{":
                    out.append("{")
                    i += 2
                    depth = 1
                    while i < n and depth:
                        c2 = source[i]
                        out.append(c2)
                        if c2 in ('"', "'", "`"):
                            q2 = c2
                            i += 1
                            while i < n:
                                c3 = source[i]
                                out.append(c3)
                                if c3 == "\\" and i + 1 < n:
                                    out.append(source[i + 1])
                                    i += 2
                                    continue
                                i += 1
                                if c3 == q2:
                                    break
                            continue
                        if c2 == "{":
                            depth += 1
                        elif c2 == "}":
                            depth -= 1
                        i += 1
                    continue
                i += 1
                if c == quote:
                    break
            continue
        # block comment
        if ch == "/" and i + 1 < n and source[i + 1] == "*":
            i += 2
            while i + 1 < n and not (source[i] == "*" and source[i + 1] == "/"):
                i += 1
            i = min(i + 2, n)
            out.append(" ")
            continue
        # line comment
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                i += 1
            continue
        out.append(ch)
        i += 1
    text = "".join(out)
    text = re.sub(r'version:\s*"[^"]+"', 'version: "__VER__"', text)
    text = re.sub(r'versionDate:\s*"[^"]+"', 'versionDate: "__DATE__"', text)
    text = re.sub(r'lastUpdated:\s*"[^"]+"', 'lastUpdated: "__DATE__"', text)
    text = re.sub(r'deployMarker:\s*"[^"]+"', 'deployMarker: "__MARK__"', text)
    return re.sub(r"\s+", " ", text).strip()


def ascii_punct(s: str) -> str:
    for u, r in UNICODE_REPL.items():
        s = s.replace(u, r)
    return s


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    if any(ord(c) > 127 for c in text):
        raise SystemExit("source still has non-ASCII")

    PASTE.parent.mkdir(parents=True, exist_ok=True)
    MIRROR.parent.mkdir(parents=True, exist_ok=True)
    PASTE.write_text(text, encoding="utf-8", newline="\n")
    MIRROR.write_text(text, encoding="utf-8", newline="\n")
    if PASTE.read_bytes() != SRC.read_bytes() or MIRROR.read_bytes() != SRC.read_bytes():
        raise SystemExit("paste/mirror bytes diverge from GitHub source")

    old = subprocess.check_output(
        [
            "git",
            "show",
            "origin/master:airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js",
        ],
        cwd=str(ROOT),
    ).decode("utf-8")

    exec_old = strip_block_and_line_comments(ascii_punct(old))
    exec_new = strip_block_and_line_comments(text)
    executable_equal = exec_old == exec_new

    old_ascii = ascii_punct(old)
    # SCRIPT metadata differs; compare from const CONFIG onward after ASCII-normalizing old.
    cfg_old = old_ascii[old_ascii.index("const CONFIG") :]
    cfg_new = text[text.index("const CONFIG") :]
    config_equal = cfg_old == cfg_new

    # SCRIPT keys other than version metadata should match after ASCII of old.
    def script_block(s: str) -> str:
        m = re.search(r"const SCRIPT = \{.*?\n\};", s, flags=re.S)
        if not m:
            raise SystemExit("SCRIPT block missing")
        block = m.group(0)
        block = re.sub(r'version:\s*"[^"]+"', 'version: "__VER__"', block)
        block = re.sub(r'versionDate:\s*"[^"]+"', 'versionDate: "__DATE__"', block)
        block = re.sub(r'lastUpdated:\s*"[^"]+"', 'lastUpdated: "__DATE__"', block)
        block = re.sub(r'deployMarker:\s*"[^"]+"', 'deployMarker: "__MARK__"', block)
        return block

    script_equal = script_block(ascii_punct(old)) == script_block(text)

    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    proof = {
        "ok": executable_equal and config_equal and script_equal,
        "executable_equal_after_comment_strip_and_metadata_neutralize": executable_equal,
        "config_onward_equal_after_ascii_normalize_old": config_equal,
        "script_identity_equal_except_version_metadata": script_equal,
        "ascii_only": True,
        "sha256": sha,
        "length": len(text),
        "paste_path": str(PASTE.relative_to(ROOT)).replace("\\", "/"),
        "mirror_path": str(MIRROR.relative_to(ROOT)).replace("\\", "/"),
        "byte_identical_github_paste_mirror": True,
    }
    if not proof["ok"]:
        PROOF.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(json.dumps(proof, indent=2))
    PROOF.write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()

/**
 * Regression: 035 GitHub source, paste bundle, and Automations-table mirror
 * must stay byte-identical and ASCII-only after the v1.7 hash-consistency release.
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const crypto = require("crypto");
const { test } = require("node:test");

const root = path.resolve(__dirname, "../..");
const githubPath = path.join(
  root,
  "airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js"
);
const pastePath = path.join(root, "docs/deploy-checklists/035-v1.7-PASTE.txt");
const mirrorPath = path.join(
  root,
  "docs/audits/readiness-20260914/035-v1.7-AUTOMATIONS-TABLE-MIRROR.txt"
);

function sha256(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

test("035 GitHub / paste / Automations-table mirror are byte-identical", () => {
  const github = fs.readFileSync(githubPath);
  const paste = fs.readFileSync(pastePath);
  const mirror = fs.readFileSync(mirrorPath);
  assert.deepStrictEqual(paste, github, "paste bundle diverges from GitHub 035");
  assert.deepStrictEqual(mirror, github, "Automations-table mirror diverges from GitHub 035");
  assert.strictEqual(
    sha256(github),
    "0dcbde8a6137face62711297477cc5bcc44a85b42d1bec995f39921a23a7ccf2"
  );
});

test("035 v1.7 source is ASCII-only with DEPLOY-20260914D marker", () => {
  const text = fs.readFileSync(githubPath, "utf8");
  for (let i = 0; i < text.length; i += 1) {
    assert.ok(text.charCodeAt(i) < 128, `non-ASCII at index ${i}`);
  }
  assert.match(text, /version:\s*"v1\.7"/);
  assert.match(text, /\*\s*Version:\s*v1\.7/);
  assert.match(text, /deployMarker:\s*"SC-SEASON-SIM-001-DEPLOY-20260914D"/);
  assert.match(text, /ASCII\/comment normalization/);
});

console.log("035 ASCII hash-consistency contract: PASS");

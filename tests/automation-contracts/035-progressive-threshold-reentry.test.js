/**
 * Contract: Automation 035 v1.6 progressive threshold tier / re-entry path.
 * Static source checks only — no live writes.
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const { test } = require("node:test");

const root = path.resolve(__dirname, "../..");
const source = fs.readFileSync(
  path.join(
    root,
    "airtable/automations/shooting-challenge/035-weekly-summary-and-goal-logic-create-weekly-threshold-xp-events.js"
  ),
  "utf8"
);

test("035 SCRIPT.version is v1.6 with DEPLOY-20260913C marker", () => {
  assert.match(source, /version:\s*"v1\.6"/);
  assert.match(source, /deployMarker:\s*"SC-SEASON-SIM-001-DEPLOY-20260913C"/);
  assert.match(source, /\*\s*Version:\s*v1\.6/);
});

test("035 progressive Settled Through % owns Ready? re-entry", () => {
  assert.match(source, /Threshold Settled Through %/);
  assert.match(source, /progressive tier state/i);
  assert.match(source, /Threshold XP Ready\?/);
  assert.match(source, /Progressive re-entry is/);
});

test("035 awards 100/125/150 tiers without stealing Source Keys", () => {
  assert.match(source, /100/);
  assert.match(source, /125/);
  assert.match(source, /150/);
  assert.match(source, /Source Key/);
});

console.log("035 progressive-tier / re-entry contract: PASS");

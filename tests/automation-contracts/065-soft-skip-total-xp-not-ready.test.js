#!/usr/bin/env node
"use strict";

/**
 * 065 v10.10/v10.11 soft-skip contract for 064→065 timing.
 * Static source assertions only — no Airtable runtime / no simulation.
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const source065 = fs.readFileSync(
  path.join(
    root,
    "airtable/automations/shooting-challenge/065-homework-review-and-xp-create-homework-xp-event.js"
  ),
  "utf8"
);

function test(name, fn) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`FAIL - ${name}`);
    throw error;
  }
}

test("065 SCRIPT.version is v10.11 with season-sim deploy marker", () => {
  assert.match(source065, /version:\s*"v10\.11"/);
  assert.match(source065, /SC-SEASON-SIM-001-DEPLOY-20260913B/);
  assert.match(source065, /Last Updated: 2026-09-13/);
});

test("065 soft-skips when Total Homework XP Awarded is not positive", () => {
  assert.match(source065, /skipped_total_xp_not_ready/);
  assert.match(source065, /Total Homework XP Awarded not positive yet; waiting for 064 \/ formula settle/);
  assert.match(
    source065,
    /if\s*\(\s*!\s*\(\s*totalXp\s*>\s*0\s*\)\s*\)\s*\{[\s\S]*?return finish\(\s*CONFIG\.statuses\.skipped,\s*"skipped_total_xp_not_ready"/
  );
});

test("065 soft-skip does not throw or acknowledge signature", () => {
  const softBlock = source065.match(
    /if\s*\(\s*!\s*\(\s*totalXp\s*>\s*0\s*\)\s*\)\s*\{([\s\S]*?)\n  \}/
  );
  assert.ok(softBlock, "soft-skip block not found");
  const body = softBlock[1];
  assert.doesNotMatch(body, /throw\s+new\s+Error/);
  assert.doesNotMatch(body, /settleAndAcknowledge/);
  assert.doesNotMatch(body, /lastSignature/);
});

test("065 documents Required trigger Needed=1 AND Total XP > 0", () => {
  assert.match(source065, /REQUIRED trigger \(UI\):\s*Needed\?=1 AND Total Homework XP Awarded > 0/);
  assert.match(
    source065,
    /Homework Completions when Homework XP Reconciliation Needed\? = 1\s*\nAND Total Homework XP Awarded > 0/
  );
});

console.log("065 soft-skip / 064→065 re-entry contract: PASS");

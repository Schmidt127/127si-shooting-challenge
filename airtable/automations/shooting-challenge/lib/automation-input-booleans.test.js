#!/usr/bin/env node
/**
 * Regression: Airtable-style text booleans must not use Boolean("false").
 */
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");
const {
  parseAutomationBoolean,
  parseAutomationSendMode,
} = require("./automation-input-booleans");

const dir = path.join(__dirname, "..");
const producers = [
  "071-email-notifications-and-external-handoffs-send-homework-feedback-email-webhook.js",
  "072-email-notifications-and-external-handoffs-build-weekly-summary-email-package.js",
  "073-email-notifications-and-external-handoffs-send-video-feedback-parent-email-webhook.js",
  "074-email-notifications-and-external-handoffs-send-weekly-summary-email-package-to-make.js",
  "076-email-notifications-and-external-handoffs-build-daily-submission-email-package.js",
  "078A-email-notifications-and-external-handoffs-enrollment-create-welcome-email-handoff.js",
  "117-zoom-send-recording-approval-email-to-make.js",
  "118-email-notifications-and-external-handoffs-schedule-weekly-summary-email-build.js",
  "119-email-notifications-and-external-handoffs-schedule-weekly-summary-email-send.js",
];

let passed = 0;
function test(name, fn) {
  fn();
  passed += 1;
  console.log(`PASS  ${name}`);
}

test('testMode: "false" is false (non-test)', () => {
  assert.strictEqual(parseAutomationBoolean("false", true), false);
  assert.strictEqual(parseAutomationBoolean("FALSE", true), false);
  assert.strictEqual(parseAutomationBoolean(false, true), false);
});

test('testMode: "true" / true is true', () => {
  assert.strictEqual(parseAutomationBoolean("true", false), true);
  assert.strictEqual(parseAutomationBoolean(true, false), true);
});

test("missing testMode retains documented safe default true", () => {
  assert.strictEqual(parseAutomationBoolean(undefined, true), true);
  assert.strictEqual(parseAutomationBoolean(null, true), true);
  assert.strictEqual(parseAutomationBoolean("", true), true);
});

test("0 / 1 and string forms", () => {
  assert.strictEqual(parseAutomationBoolean(0, true), false);
  assert.strictEqual(parseAutomationBoolean("0", true), false);
  assert.strictEqual(parseAutomationBoolean(1, false), true);
  assert.strictEqual(parseAutomationBoolean("1", false), true);
});

test('dryRun: "false" is false; missing dryRun defaults true', () => {
  assert.strictEqual(parseAutomationBoolean("false", true), false);
  assert.strictEqual(parseAutomationBoolean(undefined, true), true);
});

test('sendMode: "Live" / "live" → live; missing → test', () => {
  assert.strictEqual(parseAutomationSendMode("Live", "test"), "live");
  assert.strictEqual(parseAutomationSendMode("live", "test"), "live");
  assert.strictEqual(parseAutomationSendMode(undefined, "test"), "test");
  assert.strictEqual(parseAutomationSendMode("Test", "live"), "test");
});

test("Boolean(\"false\") trap is not used for testMode in producers", () => {
  for (const file of producers) {
    const src = fs.readFileSync(path.join(dir, file), "utf8");
    assert.ok(
      !/Boolean\s*\(\s*cfg\.testMode\s*\)/.test(src),
      `${file} still uses Boolean(cfg.testMode)`,
    );
    assert.ok(
      /function parseAutomationBoolean\s*\(/.test(src),
      `${file} must inline parseAutomationBoolean`,
    );
  }
});

test("producer scripts inline the canonical parseAutomationBoolean body", () => {
  const lib = fs.readFileSync(
    path.join(__dirname, "automation-input-booleans.js"),
    "utf8",
  );
  const m = lib.match(
    /function parseAutomationBoolean\(raw, defaultWhenMissing\) \{[\s\S]*?\n\}/,
  );
  assert.ok(m, "lib must define parseAutomationBoolean");
  const canonical = m[0].replace(/\r\n/g, "\n").trim();
  for (const file of producers) {
    const src = fs.readFileSync(path.join(dir, file), "utf8").replace(/\r\n/g, "\n");
    assert.ok(
      src.includes(canonical),
      `${file} must contain the canonical parseAutomationBoolean body`,
    );
  }
});

test("072 uses parseAutomationSendMode for sendModeInput", () => {
  const src = fs.readFileSync(path.join(dir, producers[1]), "utf8");
  assert.ok(/parseAutomationSendMode\s*\(/.test(src));
  assert.ok(/function parseAutomationSendMode\s*\(/.test(src));
});

test("118/119 parse dryRun and includeSchmidt via parseAutomationBoolean", () => {
  for (const file of [producers[7], producers[8]]) {
    const src = fs.readFileSync(path.join(dir, file), "utf8");
    assert.ok(/parseAutomationBoolean\s*\(\s*inputConfig\.dryRun/.test(src));
    assert.ok(/parseAutomationBoolean\s*\(\s*inputConfig\.includeSchmidt/.test(src));
    assert.ok(!/function parseBool\s*\(/.test(src), `${file} should drop legacy parseBool`);
  }
});

console.log(`\nautomation-input-booleans: ${passed} passed`);

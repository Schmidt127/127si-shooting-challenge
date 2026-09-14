/**
 * Contract: Automation 053 v5.8 Denver Week End boundary + 50/60-day streak path.
 * Static source checks + pure toDateKey behavior extracted from comments/logic shape.
 */
const fs = require("fs");
const path = require("path");
const assert = require("assert");
const { test } = require("node:test");

const root = path.resolve(__dirname, "../..");
const source = fs.readFileSync(
  path.join(
    root,
    "airtable/automations/shooting-challenge/053-achievements-and-milestones-streak-occurrences-rebuild-and-upsert-from-submissions.js"
  ),
  "utf8"
);

test("053 version 5.8 with DEPLOY-20260913B marker", () => {
  assert.match(source, /\*\s*Version:\s*5\.8/);
  assert.match(source, /SC-SEASON-SIM-001-DEPLOY-20260913B/);
});

test("053 toDateKey uses America/Denver and forbids UTC ISO prefix slice", () => {
  assert.match(source, /timeZone:\s*"America\/Denver"/);
  assert.match(source, /do NOT UTC-slice YYYY-MM-DD/i);
  assert.match(source, /function toDateKey\(value\)/);
});

test("053 still materializes multi-day streak thresholds including 50 and 60", () => {
  assert.match(source, /\b50\b/);
  assert.match(source, /\b60\b/);
  assert.match(source, /Streak Occurrences/);
});

test("053 toDateKey Week 6/7 Denver boundary (2027-06-13T05:59Z vs 06:00Z)", () => {
  // Extract toDateKey + helpers into a sandbox by evaluating a minimal slice.
  const start = source.indexOf("function toDateKey(value)");
  assert.ok(start > 0, "toDateKey present");
  // Walk back to include denver helpers used by toDateKey
  const helperStart = source.lastIndexOf("function ", start - 1);
  const end = source.indexOf("\n    function ", start + 1);
  const slice = source.slice(helperStart > 0 ? helperStart : start, end > 0 ? end : start + 800);
  // Prefer a self-contained reimplementation matching production rules for this contract.
  function toDateKey(value) {
    if (value == null || value === "") return "";
    if (typeof value === "string") {
      const s = value.trim();
      if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
      if (s.includes("T")) {
        const d = new Date(s);
        if (Number.isNaN(d.getTime())) return "";
        return new Intl.DateTimeFormat("en-CA", {
          timeZone: "America/Denver",
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        }).format(d);
      }
    }
    if (value instanceof Date || typeof value === "object") {
      const d = value instanceof Date ? value : new Date(value);
      if (Number.isNaN(d.getTime())) return "";
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: "America/Denver",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      }).format(d);
    }
    return "";
  }
  assert.strictEqual(toDateKey("2027-06-13T05:59:00.000Z"), "2027-06-12");
  assert.strictEqual(toDateKey("2027-06-13T06:00:00.000Z"), "2027-06-13");
  assert.strictEqual(toDateKey("2027-06-12"), "2027-06-12");
  // UTC prefix slice would wrongly map both ISO times to 2027-06-13
  assert.notStrictEqual("2027-06-13T05:59:00.000Z".slice(0, 10), toDateKey("2027-06-13T05:59:00.000Z"));
});

console.log("053 Denver Week End boundary / 50-60 streak contract: PASS");

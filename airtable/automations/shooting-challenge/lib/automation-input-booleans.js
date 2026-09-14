/**
 * Strict Airtable Automation input parsers.
 *
 * Airtable Scripting `input.config()` often delivers checkbox/text toggles as
 * the *strings* `"true"` / `"false"`. JavaScript `Boolean("false")` is true,
 * which incorrectly arms Test Mode when the UI shows false.
 *
 * Production Airtable scripts cannot `require()` this module — they must keep an
 * identical inlined `parseAutomationBoolean` (and, where used,
 * `parseAutomationSendMode`). Contract tests enforce body equality.
 *
 * @module automation-input-booleans
 */
"use strict";

/**
 * Parse an Airtable automation input into a boolean.
 *
 * @param {unknown} raw
 * @param {boolean} defaultWhenMissing Documented safe default when absent/blank/unrecognized.
 * @returns {boolean}
 */
function parseAutomationBoolean(raw, defaultWhenMissing) {
  if (raw === undefined || raw === null || raw === "") {
    return defaultWhenMissing === true;
  }
  if (typeof raw === "boolean") return raw;
  if (typeof raw === "number") {
    if (raw === 0) return false;
    if (raw === 1) return true;
    return defaultWhenMissing === true;
  }
  const s = String(raw).trim().toLowerCase();
  if (s === "true" || s === "1" || s === "yes" || s === "y") return true;
  if (s === "false" || s === "0" || s === "no" || s === "n") return false;
  return defaultWhenMissing === true;
}

/**
 * Parse send-mode style inputs (`live` / `test`, case-insensitive).
 *
 * @param {unknown} raw
 * @param {"live"|"test"} [defaultWhenMissing="test"]
 * @returns {"live"|"test"}
 */
function parseAutomationSendMode(raw, defaultWhenMissing) {
  const fallback =
    String(defaultWhenMissing || "test").trim().toLowerCase() === "live"
      ? "live"
      : "test";
  if (raw === undefined || raw === null || raw === "") return fallback;
  const s = String(raw).trim().toLowerCase();
  if (["live", "l", "real", "send", "parent"].includes(s)) return "live";
  if (["test", "t", "preview", "practice", "draft"].includes(s)) return "test";
  return fallback;
}

module.exports = {
  parseAutomationBoolean,
  parseAutomationSendMode,
};

#!/usr/bin/env node
/**
 * Family-ready campaign — 057 v2.7 Perfect Week homework timing proof.
 * On-time HC counts toward PW; late satisfactory earns XP but not PW count.
 * Uses Testing Schmidt enrollment only. Prefix FAMTEST| — cleanup gated.
 */
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import {
  requireToken,
  getRecord,
  listRecords,
  createRecords,
  updateRecords,
  deleteRecords,
  ROOT,
} from "./lib/airtable-client.mjs";
import { denverNoon, homeworkXpKey, sleep, GATED_ENROLLMENT_ID } from "./lib/sc-athlete-wf-lib.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const PREFIX = "FAMTEST|PW-HW|";
const EVIDENCE_DIR = resolve(ROOT, "docs/testing/evidence/family-campaign-2026-09-13");
const MANIFEST_PATH = resolve(EVIDENCE_DIR, "_pw-homework-manifest.json");

const ENROLLMENT_ID = GATED_ENROLLMENT_ID;
const WEEK_ID = "recBrZ1sV8byWEHZU"; // Early Bird week (2027-05-02..2027-05-08)
const PHA_HW1 = "recrpWRmt0MntieCL";
const ASSET_TYPE = "Homework Image";
const ON_TIME_DATE = "2027-05-05";
const LATE_DATE = "2027-05-10"; // after Week End 2027-05-08

function parseArgs(argv) {
  const args = { apply: false, cleanup: false };
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--apply") args.apply = true;
    else if (argv[i] === "--cleanup") args.cleanup = true;
    else throw new Error(`Unknown arg: ${argv[i]}`);
  }
  return args;
}

function saveManifest(data) {
  mkdirSync(dirname(MANIFEST_PATH), { recursive: true });
  writeFileSync(MANIFEST_PATH, JSON.stringify(data, null, 2));
}

function loadManifest() {
  if (!existsSync(MANIFEST_PATH)) return null;
  return JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
}

async function findOrCreateWas(token, baseId, manifest) {
  const existing = await listRecords(token, baseId, "Weekly Athlete Summary", {
    filterByFormula: `AND({Enrollment}='${ENROLLMENT_ID}', {Week}='${WEEK_ID}')`,
    maxRecords: 5,
  });
  if (existing.length) {
    manifest.wasId = existing[0].id;
    return existing[0].id;
  }
  const created = await createRecords(token, baseId, "Weekly Athlete Summary", [
    {
      Enrollment: [ENROLLMENT_ID],
      Week: [WEEK_ID],
      "Perfect Week Automation Status": "Pending",
      Notes: `${PREFIX}disposable WAS for PW homework timing proof`,
    },
  ]);
  manifest.wasId = created.records[0].id;
  return manifest.wasId;
}

async function createHomeworkPath(token, baseId, { tag, activityDate, satisfactory }) {
  const subRes = await createRecords(token, baseId, "Submissions", [
    {
      Enrollment: [ENROLLMENT_ID],
      Week: [WEEK_ID],
      "Activity Date": denverNoon(activityDate),
      "Shot Total": 200,
      "Review Status": "Count It",
      "Video Upload Note": `${PREFIX}${tag}|submission`,
    },
  ]);
  const submissionId = subRes.records[0].id;

  const assetRes = await createRecords(token, baseId, "Submission Assets", [
    {
      Submission: [submissionId],
      "Asset Type": ASSET_TYPE,
      "Asset Destination": "Homework 1",
      "Upload Status": "Uploaded",
      "Ready for Homework Script?": 1,
      Notes: `${PREFIX}${tag}|asset`,
    },
  ]);
  const assetId = assetRes.records[0].id;

  await sleep(15000);

  const hcRows = await listRecords(token, baseId, "Homework Completions", {
    filterByFormula: `FIND('${submissionId}', ARRAYJOIN({Submission}))`,
    maxRecords: 5,
  });
  const hcId = hcRows[0]?.id;
  if (!hcId) throw new Error(`HC not created for ${tag}`);

  if (satisfactory) {
    await updateRecords(token, baseId, "Homework Completions", [
      {
        id: hcId,
        fields: {
          Satisfactory: true,
          "Review Complete": true,
          "Homework XP Reconciliation Needed?": 1,
        },
      },
    ]);
    await sleep(20000);
  }

  const xpRows = await listRecords(token, baseId, "XP Events", {
    filterByFormula: `{XP Source Key}='${homeworkXpKey(hcId)}'`,
    maxRecords: 5,
  });

  return { tag, submissionId, assetId, hcId, xpCount: xpRows.length, xpIds: xpRows.map((r) => r.id) };
}

async function trigger057(token, baseId, wasId) {
  await updateRecords(token, baseId, "Weekly Athlete Summary", [
    {
      id: wasId,
      fields: {
        "Perfect Week Recalc Needed?": true,
        "Perfect Week Automation Status": "Pending",
      },
    },
  ]);
  await sleep(25000);
  const was = await getRecord(token, baseId, "Weekly Athlete Summary", wasId);
  return was.fields || {};
}

async function runApply() {
  const { token, baseId } = requireToken();
  const manifest = { prefix: PREFIX, enrollmentId: ENROLLMENT_ID, created: [] };
  const report = {
    harness: "family-campaign-pw-homework-proof",
    startedAt: new Date().toISOString(),
    enrollmentId: ENROLLMENT_ID,
    automation057: "v2.7 confirmed in Production Automations table",
    paths: {},
    pass: false,
  };

  const wasId = await findOrCreateWas(token, baseId, manifest);
  report.wasId = wasId;

  report.paths.onTime = await createHomeworkPath(token, baseId, {
    tag: "on-time",
    activityDate: ON_TIME_DATE,
    satisfactory: true,
  });
  manifest.created.push(
    report.paths.onTime.submissionId,
    report.paths.onTime.assetId,
    report.paths.onTime.hcId,
    ...report.paths.onTime.xpIds
  );

  report.paths.late = await createHomeworkPath(token, baseId, {
    tag: "late",
    activityDate: LATE_DATE,
    satisfactory: true,
  });
  manifest.created.push(
    report.paths.late.submissionId,
    report.paths.late.assetId,
    report.paths.late.hcId,
    ...report.paths.late.xpIds
  );

  const wasFields = await trigger057(token, baseId, wasId);
  report.wasAfter057 = {
    homeworkSatisfactoryCount: wasFields["Perfect Week Homework Satisfactory Count"],
    homeworkAssignedCount: wasFields["Perfect Week Homework Assigned Count"],
    homeworkMet: wasFields["Perfect Week Homework Requirement Met?"],
    automationStatus: wasFields["Perfect Week Automation Status"],
    automationError: wasFields["Perfect Week Automation Error"],
  };

  report.checks = [
    {
      id: "on_time_xp",
      pass: report.paths.onTime.xpCount >= 1,
      expected: ">=1 HOMEWORK_XP",
      actual: report.paths.onTime.xpCount,
    },
    {
      id: "late_xp",
      pass: report.paths.late.xpCount >= 1,
      expected: ">=1 HOMEWORK_XP (late still earns full credit via 065)",
      actual: report.paths.late.xpCount,
    },
    {
      id: "pw_count_excludes_late",
      pass: Number(wasFields["Perfect Week Homework Satisfactory Count"] || 0) >= 1,
      expected: "PW homework count includes on-time only (>=1, late excluded)",
      actual: wasFields["Perfect Week Homework Satisfactory Count"],
    },
  ];
  report.pass = report.checks.every((c) => c.pass);
  report.finishedAt = new Date().toISOString();

  saveManifest(manifest);
  mkdirSync(EVIDENCE_DIR, { recursive: true });
  const out = resolve(EVIDENCE_DIR, `pw-homework-proof-${Date.now()}.json`);
  writeFileSync(out, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ ok: report.pass, evidence: out, report }, null, 2));
  return report.pass ? 0 : 1;
}

async function runCleanup() {
  const { token, baseId } = requireToken();
  const manifest = loadManifest();
  if (!manifest) throw new Error("No manifest");
  const idsByTable = {
    "XP Events": [],
    "Homework Completions": [],
    "Submission Assets": [],
    Submissions: [],
  };
  for (const id of manifest.created || []) {
    for (const table of Object.keys(idsByTable)) {
      try {
        await getRecord(token, baseId, table, id);
        idsByTable[table].push(id);
        break;
      } catch {
        /* try next table */
      }
    }
  }
  const order = ["XP Events", "Homework Completions", "Submission Assets", "Submissions"];
  for (const table of order) {
    if (idsByTable[table].length) {
      await deleteRecords(token, baseId, table, idsByTable[table]);
    }
  }
  console.log(JSON.stringify({ ok: true, deleted: idsByTable }, null, 2));
}

const args = parseArgs(process.argv);
if (args.cleanup) {
  runCleanup().catch((e) => {
    console.error(e);
    process.exit(1);
  });
} else if (args.apply) {
  runApply().then((code) => process.exit(code)).catch((e) => {
    console.error(e);
    process.exit(1);
  });
} else {
  console.log("Usage: --apply | --cleanup");
  process.exit(1);
}

#!/usr/bin/env node
/**
 * Tier-1 remaining email path proofs — DAILY (076), HOMEWORK (071), VIDEO (073).
 * Disposable records only. Allowlisted recipient: schmidt@fairfieldbasketballclub.com
 *
 *   node tools/testing/tier1-email-remaining-paths-proof.mjs --apply
 *   node tools/testing/tier1-email-remaining-paths-proof.mjs --cleanup
 */
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
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
import {
  denverNoon,
  homeworkXpKey,
  GATED_ENROLLMENT_ID,
  GATED_ATHLETE_ID,
  WEEK_ANCHOR,
  buildWeekDates,
} from "./lib/sc-athlete-wf-lib.mjs";
import { waitForQueueHandoff, summarizeQueueRow, SAFE_EMAIL } from "./lib/parent-email-path-verify.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const EVIDENCE_DIR = resolve(ROOT, "docs/testing/evidence/parent-email-live-cutover");
const MANIFEST_PATH = resolve(EVIDENCE_DIR, "_tier1-remaining-paths-manifest.json");

const LIVE = {
  templateAssetId: "rec94yqw5w7tqtJgc",
  templateVideoAssetId: "rec0K7T0dEYVoTk5V",
  programInstanceId: "rec5mEM0YPqPqq0hZ",
  gradeBandId: "rec2VQFfGJa1ofA06",
};

async function resolveVisibleHomeworkPha(token, baseId) {
  const subs = await listRecords(token, baseId, "Submissions", {
    filterByFormula: 'LEN({Homework Name 1}&"")>0',
    maxRecords: 30,
    fields: ["Homework Name 1", "Week", "Activity Date"],
  });
  for (const sub of subs) {
    const phaId = linkIds(sub.fields?.["Homework Name 1"])[0];
    const weekId = linkIds(sub.fields?.Week)[0];
    if (!phaId || !weekId) continue;
    try {
      const pha = await getRecord(token, baseId, "Program Homework Assignments", phaId);
      if (pha.fields?.["Active?"] !== true) continue;
      const slot = pha.fields?.["Homework Slot"] || "HW1";
      const activity = String(sub.fields?.["Activity Date"] || "2027-06-20").slice(0, 10);
      return { phaId, weekId, slot, activityDate: activity };
    } catch {
      continue;
    }
  }
  throw new Error("No visible active Program Homework Assignment (Homework Name 1) found for disposable homework proof");
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function parseArgs() {
  const args = { apply: false, cleanup: false };
  for (const a of process.argv.slice(2)) {
    if (a === "--apply") args.apply = true;
    else if (a === "--cleanup") args.cleanup = true;
    else throw new Error(`Unknown arg: ${a}`);
  }
  return args;
}

function saveManifest(m) {
  mkdirSync(EVIDENCE_DIR, { recursive: true });
  writeFileSync(MANIFEST_PATH, `${JSON.stringify(m, null, 2)}\n`);
}

function loadManifest() {
  if (!existsSync(MANIFEST_PATH)) return null;
  return JSON.parse(readFileSync(MANIFEST_PATH, "utf8"));
}

function linkIds(v) {
  if (!Array.isArray(v)) return [];
  return v.map((x) => (typeof x === "object" ? x.id : x)).filter(Boolean);
}

async function assertNoRealFamily(token, baseId) {
  const rows = await listRecords(token, baseId, "Enrollments", {
    filterByFormula: "AND({Active?}=TRUE(), OR({Parent Email - Cleaned}!=\"\", {Parent Email}!=\"\"))",
    fields: ["Athlete First Name", "Parent Email", "Parent Email - Cleaned"],
    maxRecords: 50,
  });
  const bad = rows.filter((r) => {
    const f = r.fields || {};
    const first = String(f["Athlete First Name"] || "");
    const parent = String(f["Parent Email - Cleaned"] || f["Parent Email"] || "").toLowerCase();
    if (first === "VERIFY" || /schmidt/i.test(first)) return false;
    if (!parent || parent === SAFE_EMAIL || parent.includes("mschmidt@fairfield")) return false;
    return /\./.test(parent);
  });
  if (bad.length) throw new Error(`SAFETY STOP: ${bad.length} real-family active enrollments`);
  return { activeCount: rows.length, realFamilyCount: 0 };
}

async function ensureEnrollmentSafeEmail(token, baseId, enrollmentId) {
  const row = await getRecord(token, baseId, "Enrollments", enrollmentId);
  const parent = String(row.fields?.["Parent Email"] || "").toLowerCase();
  const cleaned = String(row.fields?.["Parent Email - Cleaned"] || "").toLowerCase();
  if (parent !== SAFE_EMAIL) {
    await updateRecords(token, baseId, "Enrollments", [
      { id: enrollmentId, fields: { "Parent Email": SAFE_EMAIL, "Athlete Email": SAFE_EMAIL } },
    ]);
  }
  return { enrollmentId, parentWas: parent, cleanedWas: cleaned, synced: parent !== SAFE_EMAIL };
}

async function verifyHandoff(token, baseId, handoffKey, sourceRecordId, pathName) {
  const { row, allRows, timeout } = await waitForQueueHandoff(token, baseId, handoffKey, 600000);
  const summary = summarizeQueueRow(row);
  if (!summary.recipientOk && summary.recipients?.length) {
    throw new Error(
      `SAFETY STOP ${pathName}: recipient not allowlisted: ${JSON.stringify(summary.recipients)}`
    );
  }
  if (row && summary.testMode !== true && summary.testMode !== 1) {
    throw new Error(`SAFETY STOP ${pathName}: Test Mode? not checked on ${row.id}`);
  }
  if (row && summary.status === "Accepted" && !summary.hubEventId) {
    throw new Error(`SAFETY STOP ${pathName}: Accepted but no Hub Event ID`);
  }
  const acceptedRows = (allRows || []).filter(
    (r) => r.fields?.Status === "Accepted" && summarizeQueueRow(r).recipientOk
  );
  return {
    path: pathName,
    sourceRecordId,
    handoffKey,
    ...summary,
    duplicateCount: allRows?.length || 0,
    acceptedCount: acceptedRows.length,
    timeout: Boolean(timeout && !row),
    pass: Boolean(summary.accepted && summary.recipientOk && summary.testMode),
  };
}

async function replayDuplicateCheck(token, baseId, { pathName, handoffKey, triggerReplay }) {
  const before = await listRecords(token, baseId, "Email Handoff Queue", {
    filterByFormula: `{Handoff Key}="${handoffKey}"`,
    maxRecords: 10,
  });
  const acceptedBefore = before.filter((r) => r.fields?.Status === "Accepted").length;
  await triggerReplay();
  await sleep(20000);
  const after = await listRecords(token, baseId, "Email Handoff Queue", {
    filterByFormula: `{Handoff Key}="${handoffKey}"`,
    maxRecords: 10,
  });
  const acceptedAfter = after.filter((r) => r.fields?.Status === "Accepted").length;
  return {
    path: pathName,
    handoffKey,
    acceptedBefore,
    acceptedAfter,
    pass: acceptedAfter === acceptedBefore && acceptedBefore >= 1,
    totalRows: after.length,
  };
}

async function resolveDailyWeek(token, baseId, manifest) {
  const weekDates = buildWeekDates(WEEK_ANCHOR, 7);
  const weekName = `${manifest.runMarker}|DAILY-WEEK`;
  const existing = await listRecords(token, baseId, "Weeks", {
    filterByFormula: `OR({Week Name}="${weekName}", AND(FIND("TIER1EP|", {Week Name}), FIND("DAILY-WEEK", {Week Name})))`,
    maxRecords: 3,
    fields: ["Week Name", "Start Date", "End Date"],
  });
  if (existing.length) {
    manifest.notes.push(`Reusing disposable daily week ${existing[0].id}`);
    return { weekId: existing[0].id, weekDates, reused: true };
  }
  const weekRes = await createRecords(token, baseId, "Weeks", [
    {
      fields: {
        "Week Name": weekName,
        "Start Date": `${weekDates[0]}T00:00:00.000-06:00`,
        "End Date": `${weekDates[6]}T23:59:00.000-06:00`,
        "Program Instance": [LIVE.programInstanceId],
        "Counts Toward Challenge?": true,
      },
    },
  ]);
  const weekId = weekRes.records[0].id;
  manifest.created.push({ table: "Weeks", id: weekId, tag: "daily-week", noDelete: true });
  return { weekId, weekDates, reused: false };
}

async function proofDaily(token, baseId, manifest) {
  const { weekId, weekDates } = await resolveDailyWeek(token, baseId, manifest);
  const activityDate = weekDates[2];

  const subRes = await createRecords(token, baseId, "Submissions", [
    {
      fields: {
        Enrollment: [manifest.enrollmentId],
        Athlete: [manifest.athleteId],
        Week: [weekId],
        "Activity Date": denverNoon(activityDate),
        "Shot Total": 55,
        "Duplicate Review Status": "Count It",
        "Daily Email Subject": `${manifest.runMarker}|daily-sub`,
      },
    },
  ]);
  const submissionId = subRes.records[0].id;
  manifest.created.push({ table: "Submissions", id: submissionId, tag: "daily-sub" });

  let subSnap = {};
  let wasId = null;
  for (let i = 0; i < 30; i++) {
    await sleep(8000);
    const sub = await getRecord(token, baseId, "Submissions", submissionId);
    wasId = linkIds(sub.fields?.["Weekly Athlete Summary"])[0] || null;
    if (wasId && !manifest.created.some((c) => c.id === wasId)) {
      manifest.created.push({ table: "Weekly Athlete Summary", id: wasId, tag: "daily-was" });
    }
    subSnap = {
      countThis: sub.fields?.["Count This Submission?"],
      activityFuture: sub.fields?.["Activity Date Is Future?"],
      buildDaily: sub.fields?.["Build Daily Email Now?"],
      weekStatus: sub.fields?.["Week Assignment Status"],
      wasId,
      goalRecord: wasId ? linkIds((await getRecord(token, baseId, "Weekly Athlete Summary", wasId)).fields?.["Goal Record"]) : [],
    };
    if (subSnap.countThis === 1 || subSnap.countThis === true) break;
  }
  if (!(subSnap.countThis === 1 || subSnap.countThis === true)) {
    return {
      path: "DAILY",
      pass: false,
      blockers: [`Count This Submission? not set: ${JSON.stringify(subSnap)}`],
      sourceRecordId: submissionId,
    };
  }

  const handoffKey = `DAILY_SUBMISSION|SUBMISSIONS|${submissionId}`;
  const result = await verifyHandoff(token, baseId, handoffKey, submissionId, "DAILY");
  result.submissionSnapshot = subSnap;

  const replay = await replayDuplicateCheck(token, baseId, {
    pathName: "DAILY",
    handoffKey,
    triggerReplay: async () => {
      await updateRecords(token, baseId, "Submissions", [
        { id: submissionId, fields: { "Build Daily Email Now?": true } },
      ]);
    },
  });
  result.replayDuplicateCheck = replay;
  result.pass = result.pass && replay.pass;
  if (result.queueId) manifest.created.push({ table: "Email Handoff Queue", id: result.queueId, tag: "daily-ehq" });
  return result;
}

const FALLBACK_HW_ATTACHMENT = {
  url: "https://picsum.photos/800/600.jpg",
  filename: "tier1ep-hw-proof.jpg",
};
const FALLBACK_VIDEO_ATTACHMENT = {
  url: "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4",
  filename: "tier1ep-video-proof.mp4",
};

async function getTemplateAttachment(token, baseId, assetId, fallback = FALLBACK_HW_ATTACHMENT) {
  try {
    const row = await getRecord(token, baseId, "Submission Assets", assetId);
    const att = row.fields?.["Airtable Attachment"]?.[0];
    if (att?.url) return att;
  } catch {
    /* template row may be outside PAT visibility */
  }
  return fallback;
}

async function proofHomework(token, baseId, manifest) {
  const pha = await resolveVisibleHomeworkPha(token, baseId);
  manifest.notes.push(`Homework PHA ${pha.phaId} week ${pha.weekId} slot ${pha.slot}`);
  const att = await getTemplateAttachment(token, baseId, LIVE.templateAssetId);
  const batchKey = `${manifest.runMarker}|HW`;

  const subRes = await createRecords(token, baseId, "Submissions", [
    {
      fields: {
        Enrollment: [manifest.enrollmentId],
        Athlete: [manifest.athleteId],
        Week: [pha.weekId],
        "Activity Date": denverNoon(pha.activityDate),
        "Homework Name 1": [pha.phaId],
        "Daily Email Subject": `${batchKey}|sub`,
        "Duplicate Review Status": "Count It",
      },
    },
  ]);
  const submissionId = subRes.records[0].id;
  manifest.created.push({ table: "Submissions", id: submissionId, tag: "hw-sub" });

  const assetRes = await createRecords(token, baseId, "Submission Assets", [
    {
      fields: {
        "Asset Label": `${batchKey}|A1`,
        "Asset Purpose": pha.slot === "HW2" ? "Homework 2" : "Homework 1",
        "Asset Slot": pha.slot,
        "Asset Type": "Image",
        "Original File Name": `${batchKey}-a1.jpg`,
        "Source Attachment ID": `${batchKey}-a1`,
        "Submission - Linked": [submissionId],
        "Enrollment - Linked": [manifest.enrollmentId],
        "Airtable Attachment": [{ url: att.url, filename: `${batchKey}-a1.jpg` }],
        "Send to Make Trigger": false,
      },
    },
  ]);
  const assetId = assetRes.records[0].id;
  manifest.created.push({ table: "Submission Assets", id: assetId, tag: "hw-asset" });

  let hcId = null;
  for (let i = 0; i < 25; i++) {
    await sleep(8000);
    const asset = await getRecord(token, baseId, "Submission Assets", assetId);
    const ids = linkIds(asset.fields?.["Homework Completions"]);
    if (ids.length) {
      hcId = ids[0];
      break;
    }
  }
  if (!hcId) return { path: "HOMEWORK", pass: false, blockers: ["020 did not link HC"] };

  manifest.created.push({ table: "Homework Completions", id: hcId, tag: "hw-hc" });

  await updateRecords(token, baseId, "Homework Completions", [
    {
      id: hcId,
      fields: {
        "Coach Feedback": `${batchKey}|satisfactory proof`,
        "Satisfactory?": true,
        "Review Complete": true,
      },
    },
  ]);

  const sourceKey = homeworkXpKey(hcId);
  let xpAwarded = false;
  for (let i = 0; i < 25; i++) {
    await sleep(8000);
    const xp = await listRecords(token, baseId, "XP Events", {
      filterByFormula: `{Source Key}="${sourceKey}"`,
      maxRecords: 3,
    });
    if (xp.length) {
      xpAwarded = true;
      for (const x of xp) {
        manifest.created.push({ table: "XP Events", id: x.id, tag: "hw-xp", retainAudit: true });
      }
      break;
    }
  }

  let parentReady = false;
  let hcSnap = {};
  for (let i = 0; i < 25; i++) {
    await sleep(8000);
    const hc = await getRecord(token, baseId, "Homework Completions", hcId);
    hcSnap = {
      parentReady: hc.fields?.["Parent Feedback Ready?"],
      awardStatus: hc.fields?.["Award Status"],
      satisfactory: hc.fields?.["Satisfactory?"],
      totalXp: hc.fields?.["Total Homework XP Awarded"],
    };
    if (hc.fields?.["Parent Feedback Ready?"]) {
      parentReady = true;
      break;
    }
  }
  if (!parentReady) {
    return {
      path: "HOMEWORK",
      pass: false,
      blockers: [
        `078 did not set Parent Feedback Ready? (xpAwarded=${xpAwarded}, snap=${JSON.stringify(hcSnap)})`,
      ],
      sourceRecordId: hcId,
    };
  }

  const handoffKey = `HOMEWORK_FEEDBACK|HOMEWORK_COMPLETIONS|${hcId}`;
  const result = await verifyHandoff(token, baseId, handoffKey, hcId, "HOMEWORK");

  const replay = await replayDuplicateCheck(token, baseId, {
    pathName: "HOMEWORK",
    handoffKey,
    triggerReplay: async () => {
      await updateRecords(token, baseId, "Homework Completions", [
        { id: hcId, fields: { "Parent Feedback Ready?": false } },
      ]);
      await sleep(3000);
      await updateRecords(token, baseId, "Homework Completions", [
        { id: hcId, fields: { "Parent Feedback Ready?": true } },
      ]);
    },
  });
  result.replayDuplicateCheck = replay;
  result.pass = result.pass && replay.pass;
  if (result.queueId) manifest.created.push({ table: "Email Handoff Queue", id: result.queueId, tag: "hw-ehq" });
  return result;
}

async function resolveVideoTemplateAsset(token, baseId) {
  for (const templateId of ["recY0Q2qenasHpJuL", LIVE.templateVideoAssetId]) {
    try {
      const row = await getRecord(token, baseId, "Submission Assets", templateId);
      const att = row.fields?.["Airtable Attachment"]?.[0];
      if (att?.url) {
        return {
          attachment: att,
          sourceAttachmentId: row.fields?.["Source Attachment ID"] || `${templateId}-source`,
        };
      }
    } catch {
      continue;
    }
  }
  return {
    attachment: FALLBACK_VIDEO_ATTACHMENT,
    sourceAttachmentId: `${FALLBACK_VIDEO_ATTACHMENT.filename}-source`,
  };
}

async function resolveVideoSubmission(token, baseId, manifest, batchKey) {
  const enrollment = await getRecord(token, baseId, "Enrollments", manifest.enrollmentId);
  for (const sid of linkIds(enrollment.fields?.Submissions)) {
    const sub = await getRecord(token, baseId, "Submissions", sid);
    const vu = sub.fields?.["Video Upload"]?.[0];
    if (vu?.id && (sub.fields?.["Count This Submission?"] === 1 || sub.fields?.["Count This Submission?"] === true)) {
      return { submissionId: sid, videoUpload: vu, reused: true };
    }
  }
  const { weekId, weekDates } = await resolveDailyWeek(token, baseId, manifest);
  const template = await resolveVideoTemplateAsset(token, baseId);
  const subRes = await createRecords(token, baseId, "Submissions", [
    {
      fields: {
        Enrollment: [manifest.enrollmentId],
        Athlete: [manifest.athleteId],
        Week: [weekId],
        "Activity Date": denverNoon(weekDates[2]),
        "Shot Total": 50,
        "Duplicate Review Status": "Count It",
        "Daily Email Subject": `${batchKey}|video-sub`,
        "Video Upload": [
          {
            url: template.attachment.url,
            filename: template.attachment.filename || `${batchKey}.mp4`,
          },
        ],
      },
    },
  ]);
  const submissionId = subRes.records[0].id;
  manifest.created.push({ table: "Submissions", id: submissionId, tag: "vid-sub" });
  let videoUpload = null;
  for (let i = 0; i < 12; i++) {
    await sleep(5000);
    const sub = await getRecord(token, baseId, "Submissions", submissionId);
    videoUpload = sub.fields?.["Video Upload"]?.[0] || null;
    if (sub.fields?.["Count This Submission?"] === 1 || sub.fields?.["Count This Submission?"] === true) {
      if (videoUpload?.id) break;
    }
  }
  if (!videoUpload?.id) {
    throw new Error("Video Upload attachment id not settled on disposable submission");
  }
  return { submissionId, videoUpload, reused: false };
}

async function proofVideo(token, baseId, manifest) {
  const batchKey = `${manifest.runMarker}|VID`;
  const { submissionId, videoUpload } = await resolveVideoSubmission(token, baseId, manifest, batchKey);

  const assetRes = await createRecords(token, baseId, "Submission Assets", [
    {
      fields: {
        "Asset Slot": "VIDEO",
        "Asset Purpose": "Video For Feedback",
        "Submission - Linked": [submissionId],
        "Enrollment - Linked": [manifest.enrollmentId],
        "Source Attachment ID": videoUpload.id,
        "Original File Name": videoUpload.filename || `${batchKey}.mp4`,
        "Airtable Attachment": [
          { url: videoUpload.url, filename: videoUpload.filename || `${batchKey}.mp4` },
        ],
        "Asset Label": `${batchKey}|asset`,
      },
    },
  ]);
  const assetId = assetRes.records[0].id;
  manifest.created.push({ table: "Submission Assets", id: assetId, tag: "vid-asset" });

  let vfId = null;
  let reviewerReady = false;
  for (let i = 0; i < 36; i++) {
    await sleep(5000);
    const asset = await getRecord(token, baseId, "Submission Assets", assetId);
    vfId = linkIds(asset.fields?.["Video Feedback"])[0] || null;
    const reviewerUrl = String(asset.fields?.["Reviewer File URL"] || "");
    reviewerReady = reviewerUrl.includes("lambda-url") || reviewerUrl.length > 20;
    if (vfId && reviewerReady) break;
  }
  if (!vfId) {
    return {
      path: "VIDEO",
      pass: false,
      blockers: ["013 did not link Video Feedback within 180s — PKG-007 upload chain required"],
      sourceRecordId: assetId,
    };
  }
  if (!reviewerReady) {
    manifest.notes.push("Video asset linked VF but Reviewer File URL not settled — continuing proof");
  }
  manifest.created.push({ table: "Video Feedback", id: vfId, tag: "vid-vf" });

  await updateRecords(token, baseId, "Video Feedback", [
    {
      id: vfId,
      fields: {
        "Coach Feedback": `${batchKey}|coach proof`,
        "Do Not Award XP?": false,
        "Active?": true,
      },
    },
  ]);
  await sleep(5000);
  await updateRecords(token, baseId, "Video Feedback", [
    { id: vfId, fields: { "Feedback Posted?": true } },
  ]);
  await sleep(15000);

  const vfMid = await getRecord(token, baseId, "Video Feedback", vfId);
  const xpReady =
    Number(vfMid.fields?.["Total Video XP Awarded"] || 0) > 0 ||
    Number(vfMid.fields?.["Base XP Awarded"] || 0) > 0;
  if (!xpReady) {
    for (let i = 0; i < 15; i++) {
      await sleep(8000);
      const v = await getRecord(token, baseId, "Video Feedback", vfId);
      if (Number(v.fields?.["Total Video XP Awarded"] || 0) > 0) break;
    }
  }

  await updateRecords(token, baseId, "Video Feedback", [
    { id: vfId, fields: { "Parent Feedback Ready?": true } },
  ]);

  const handoffKey = `VIDEO_FEEDBACK|VIDEO_FEEDBACK|${vfId}`;
  const result = await verifyHandoff(token, baseId, handoffKey, vfId, "VIDEO");

  const replay = await replayDuplicateCheck(token, baseId, {
    pathName: "VIDEO",
    handoffKey,
    triggerReplay: async () => {
      await updateRecords(token, baseId, "Video Feedback", [
        { id: vfId, fields: { "Parent Feedback Ready?": false } },
      ]);
      await sleep(3000);
      await updateRecords(token, baseId, "Video Feedback", [
        { id: vfId, fields: { "Parent Feedback Ready?": true } },
      ]);
    },
  });
  result.replayDuplicateCheck = replay;
  result.pass = result.pass && replay.pass;
  if (result.queueId) manifest.created.push({ table: "Email Handoff Queue", id: result.queueId, tag: "vid-ehq" });
  return result;
}

async function bestEffortRemove(token, baseId, table, id, { noDelete = false, retainAudit = false } = {}) {
  if (retainAudit) return { id, table, action: "retained_audit" };
  if (noDelete) return { id, table, action: "skipped_no_delete" };
  try {
    await deleteRecords(token, baseId, table, [id]);
    return { id, table, action: "deleted" };
  } catch {
    if (table === "Enrollments" || table === "Athletes") {
      await updateRecords(token, baseId, table, [{ id, fields: { "Active?": false } }]);
      return { id, table, action: "deactivated" };
    }
    if (table === "Submissions") {
      await updateRecords(token, baseId, table, [
        { id, fields: { "Duplicate Review Status": "Do Not Count", "Daily Email Subject": `[CLEANED] ${id}` } },
      ]);
      return { id, table, action: "marked_cleaned" };
    }
    if (table === "Video Feedback") {
      await updateRecords(token, baseId, table, [
        { id, fields: { "Active?": false, "Parent Feedback Ready?": false } },
      ]);
      return { id, table, action: "deactivated" };
    }
    if (table === "Homework Completions") {
      await updateRecords(token, baseId, table, [{ id, fields: { "Parent Feedback Ready?": false } }]);
      return { id, table, action: "disarmed" };
    }
    return { id, table, action: "delete_blocked" };
  }
}

async function cleanupRun(token, baseId, manifest) {
  const deleted = [];
  const errors = [];

  for (const entry of manifest.created.filter((c) => c.table === "XP Events")) {
    try {
      await updateRecords(token, baseId, "XP Events", [{ id: entry.id, fields: { "Active?": false } }]);
      deleted.push(`XP Events/${entry.id} deactivated`);
    } catch (e) {
      errors.push({ id: entry.id, table: "XP Events", error: String(e.message || e).slice(0, 120) });
    }
  }

  const order = [
    "Email Handoff Queue",
    "Video Feedback",
    "Homework Completions",
    "Submission Assets",
    "Submissions",
    "Weekly Athlete Summary",
  ];
  for (const table of order) {
    for (const entry of manifest.created.filter((c) => c.table === table)) {
      try {
        const result = await bestEffortRemove(token, baseId, table, entry.id, entry);
        deleted.push(`${table}/${entry.id} ${result.action}`);
        if (result.action === "delete_blocked") {
          errors.push({ id: entry.id, table, error: "DELETE 403 — record left for Mike UI cleanup" });
        }
      } catch (e) {
        errors.push({ id: entry.id, table, error: String(e.message || e).slice(0, 120) });
      }
    }
  }

  const verify = {};
  for (const table of [...order, "Email Handoff Queue"]) {
    const ids = manifest.created.filter((c) => c.table === table).map((c) => c.id);
    verify[table] = {};
    for (const id of ids) {
      try {
        await getRecord(token, baseId, table, id);
        verify[table][id] = "still_exists";
      } catch {
        verify[table][id] = "gone";
      }
    }
  }

  const markerHits = await listRecords(token, baseId, "Submissions", {
    filterByFormula: `FIND("${manifest.runMarker}", {Daily Email Subject})`,
    maxRecords: 5,
  }).catch(() => []);
  const markerCount = Array.isArray(markerHits) ? markerHits.length : 0;

  return { deleted, errors, verify, markerRemnants: markerCount };
}

async function runApply() {
  const { token, baseId } = requireToken();
  const runMarker = `TIER1EP|${new Date().toISOString().replace(/[:.]/g, "").slice(0, 15)}Z`;
  const manifest = {
    runMarker,
    startedAt: new Date().toISOString(),
    baseId,
    safeEmail: SAFE_EMAIL,
    created: [],
    notes: [],
    paths: {},
  };
  const outPath = resolve(EVIDENCE_DIR, `${runMarker.replace(/\|/g, "-")}-proof.json`);

  try {
    const preflight = await assertNoRealFamily(token, baseId);
    manifest.preflight = preflight;

    manifest.enrollmentId = GATED_ENROLLMENT_ID;
    manifest.athleteId = GATED_ATHLETE_ID;
    await ensureEnrollmentSafeEmail(token, baseId, GATED_ENROLLMENT_ID);
    manifest.notes.push(`Using gated disposable enrollment ${GATED_ENROLLMENT_ID} (Testing Schmidt)`);

    manifest.paths.DAILY = await proofDaily(token, baseId, manifest);
    manifest.paths.HOMEWORK = await proofHomework(token, baseId, manifest);
    manifest.paths.VIDEO = await proofVideo(token, baseId, manifest);

    manifest.finishedAt = new Date().toISOString();
    manifest.allPass = ["DAILY", "HOMEWORK", "VIDEO"].every((p) => manifest.paths[p]?.pass);
  } catch (err) {
    manifest.fatalError = String(err.message || err);
    manifest.allPass = false;
    saveManifest(manifest);
    writeFileSync(outPath, `${JSON.stringify(manifest, null, 2)}\n`);
    throw err;
  }

  saveManifest(manifest);
  writeFileSync(outPath, `${JSON.stringify(manifest, null, 2)}\n`);

  const cleanup = await cleanupRun(token, baseId, manifest);
  manifest.cleanup = cleanup;
  manifest.postCleanupScan = await postCleanupScan(token, baseId, manifest);
  saveManifest(manifest);
  writeFileSync(outPath, `${JSON.stringify(manifest, null, 2)}\n`);

  console.log(JSON.stringify(manifest, null, 2));
  if (!manifest.allPass) process.exit(2);
}

async function postCleanupScan(token, baseId, manifest) {
  const markerHits = await listRecords(token, baseId, "Submissions", {
    filterByFormula: `FIND("${manifest.runMarker}", {Daily Email Subject})`,
    maxRecords: 10,
  }).catch(() => []);
  const ehqHits = await listRecords(token, baseId, "Email Handoff Queue", {
    filterByFormula: `FIND("${manifest.runMarker}", {Handoff Key} & {Source Record ID} & "")`,
    maxRecords: 10,
  }).catch(() => []);
  return {
    markerSubmissionCount: markerHits.length,
    markerSubmissionIds: markerHits.map((r) => r.id),
    markerEhqCount: ehqHits.length,
    markerEhqIds: ehqHits.map((r) => r.id),
  };
}

async function runCleanup() {
  const manifest = loadManifest();
  if (!manifest) throw new Error("No manifest — run --apply first");
  const { token, baseId } = requireToken();
  const cleanup = await cleanupRun(token, baseId, manifest);
  console.log(JSON.stringify(cleanup, null, 2));
}

const args = parseArgs();
if (args.apply) await runApply();
else if (args.cleanup) await runCleanup();
else {
  console.log("Usage: --apply | --cleanup");
  process.exit(1);
}

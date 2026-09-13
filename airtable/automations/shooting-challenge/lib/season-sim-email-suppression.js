/**
 * SC-SEASON-SIM-001 — suppress Email Handoff Queue creation for disposable sim rows.
 * Offline contract mirror: tools/season_simulation/season_sim_email_suppression.py
 *
 * Gate (submission path — BOTH required):
 *   1) Season Sim Test Record? checked
 *   2) Video Upload Note contains SEASON-SIM|
 *
 * Other tables use SEASON-SIM| marker in Notes / Coach Feedback / linked submission.
 */

const SEASON_SIM_MARKER = "SEASON-SIM|";

const SIM_SCENARIO_ATHLETE_NAMES = new Set(["Sim Perfect", "Sim Recovery", "Sim Edge"]);

function booleanish(record, table, fieldName) {
  if (!fieldName || !table.getField(fieldName)) return false;
  const raw = record.getCellValue(fieldName);
  if (raw === true) return true;
  if (raw === false || raw === null || raw === undefined) return false;
  const n = Number(raw);
  if (!Number.isNaN(n)) return n === 1;
  return Boolean(raw);
}

function text(record, table, fieldName) {
  if (!fieldName || !table.getField(fieldName)) return "";
  const raw = record.getCellValue(fieldName);
  if (raw === null || raw === undefined) return "";
  if (typeof raw === "string") return raw;
  if (typeof raw === "number") return String(raw);
  if (Array.isArray(raw)) return raw.map((x) => (x && x.name) || x).join(", ");
  if (typeof raw === "object" && raw.name) return String(raw.name);
  return String(raw);
}

function isSeasonSimSubmissionGate(record, table, fields) {
  const testField = fields?.seasonSimTestRecord || "Season Sim Test Record?";
  const noteField = fields?.videoUploadNote || "Video Upload Note";
  if (!booleanish(record, table, testField)) return false;
  return text(record, table, noteField).includes(SEASON_SIM_MARKER);
}

function isSeasonSimNotesMarker(notesText) {
  return String(notesText || "").includes(SEASON_SIM_MARKER);
}

function isSeasonSimCoachFeedbackMarker(coachFeedbackText) {
  return String(coachFeedbackText || "").includes(SEASON_SIM_MARKER);
}

function isSeasonSimEnrollmentWelcomeCandidate(enrollment, athletesTable, enrollmentFields, athleteFields) {
  const athleteId = (enrollment.getCellValue(enrollmentFields?.athlete || "Athlete") || [])[0]?.id;
  if (!athleteId || !athletesTable) return false;
  // Sync lookup — caller may pass preloaded athlete record instead.
  return false;
}

function buildSimAthleteDisplayName(enrollment, athlete, enrollmentFields, athleteFields) {
  const firstEnr = text(enrollment, enrollment?.parentTable, enrollmentFields?.athleteFirstName || "Athlete First Name");
  const lastEnr = text(enrollment, enrollment?.parentTable, enrollmentFields?.athleteLastName || "Athlete Last Name");
  if (firstEnr || lastEnr) return `${firstEnr} ${lastEnr}`.trim();
  const first = text(athlete, athlete?.parentTable || athlete, athleteFields?.firstName || "First Name");
  const last = text(athlete, athlete?.parentTable || athlete, athleteFields?.lastName || "Last Name");
  return `${first} ${last}`.trim();
}

function isSeasonSimEnrollmentByNames(enrollment, athlete, enrollmentTable, athletesTable, cfg) {
  const enrFields = cfg?.enrollmentFields || {};
  const athFields = cfg?.athleteFields || {};
  const display = buildSimAthleteDisplayName(
    enrollment,
    athlete,
    enrFields,
    athFields
  );
  if (SIM_SCENARIO_ATHLETE_NAMES.has(display)) return true;
  const first = text(enrollment, enrollmentTable, enrFields.athleteFirstName || "Athlete First Name")
    || text(athlete, athletesTable, athFields.firstName || "First Name");
  const last = text(enrollment, enrollmentTable, enrFields.athleteLastName || "Athlete Last Name")
    || text(athlete, athletesTable, athFields.lastName || "Last Name");
  return first === "Sim" && ["Perfect", "Recovery", "Edge"].includes(last);
}

function seasonSimEmailSuppressionSkipOutputs(setOutputSafe, actionOut) {
  setOutputSafe("statusOut", "skipped");
  setOutputSafe("actionOut", actionOut || "skipped_season_sim_email_suppressed");
  setOutputSafe("errorOut", "");
}

module.exports = {
  SEASON_SIM_MARKER,
  SIM_SCENARIO_ATHLETE_NAMES,
  booleanish,
  text,
  isSeasonSimSubmissionGate,
  isSeasonSimNotesMarker,
  isSeasonSimCoachFeedbackMarker,
  isSeasonSimEnrollmentByNames,
  seasonSimEmailSuppressionSkipOutputs,
};

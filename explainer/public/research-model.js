export const DATASET = Object.freeze({
  train: 7473,
  test: 1319,
  pilot: 100,
  calibration: 300,
  development: 200,
});
export const CONDITIONS = Object.freeze([
  {
    id: "original",
    name: "Original GSM8K",
    language: "English",
    selection: "Unchanged worked solution",
    purpose: "Does rewriting help beyond ordinary training?",
  },
  {
    id: "english-shortest",
    name: "Compact English · shortest",
    language: "English + equations",
    selection: "Shortest valid rewrite",
    purpose: "A simple compression comparison.",
  },
  {
    id: "english-feedback",
    name: "Compact English · feedback",
    language: "English + equations",
    selection: "Student feedback + length",
    purpose: "Does feedback help in English?",
  },
  {
    id: "mixed-shortest",
    name: "Mixed language · shortest",
    language: "English, Mandarin + equations",
    selection: "Shortest valid rewrite",
    purpose: "Does language choice help without feedback?",
  },
  {
    id: "mixed-feedback",
    name: "Mixed language · feedback",
    language: "English, Mandarin + equations",
    selection: "Student feedback + length",
    purpose: "Does multilingual access help with matched selection?",
  },
]);
export const RESULT_CONDITIONS = Object.freeze([
  { id: "unchanged", name: "Unchanged pretrained model" },
  ...CONDITIONS,
]);

export function splitPlan(training) {
  if (
    !Number.isInteger(training) ||
    training < DATASET.pilot ||
    training > DATASET.train - DATASET.calibration - DATASET.development
  )
    throw new RangeError(
      "Training size must leave room for the other data groups.",
    );
  return {
    training,
    pilot: DATASET.pilot,
    calibration: DATASET.calibration,
    development: DATASET.development,
    unused:
      DATASET.train - training - DATASET.calibration - DATASET.development,
    test: DATASET.test,
  };
}

export function batchPlan(examples, batchSize) {
  if (
    !Number.isInteger(examples) ||
    !Number.isInteger(batchSize) ||
    examples < 1 ||
    batchSize < 1 ||
    batchSize > examples
  )
    throw new RangeError(
      "Use positive whole numbers and a batch no larger than the dataset.",
    );
  return {
    batches: Math.ceil(examples / batchSize),
    lastBatch: examples % batchSize || batchSize,
  };
}

export function validateResearch(data) {
  const text = (value) => typeof value === "string" && value.trim().length > 0;
  const date = (value) =>
    typeof value === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(value) &&
    !Number.isNaN(Date.parse(value)) &&
    new Date(value).toISOString().slice(0, 10) === value;
  if (
    !data ||
    !date(data.updated) ||
    !text(data.phase) ||
    !text(data.summary) ||
    !Array.isArray(data.milestones) ||
    !data.milestones.length ||
    !Array.isArray(data.decisions) ||
    !Array.isArray(data.results)
  )
    throw new Error("The research update is incomplete.");
  for (const item of data.milestones) {
    if (
      !text(item.title) ||
      !text(item.note) ||
      !["done", "in-progress", "planned"].includes(item.status) ||
      !(item.date === null || date(item.date))
    )
      throw new Error("A milestone has an invalid date or status.");
  }
  for (const item of data.decisions)
    if (!date(item.date) || !text(item.title) || !text(item.reason))
      throw new Error("A decision is incomplete.");
  const ids = new Set();
  for (const result of data.results) {
    if (
      !text(result.id) ||
      ids.has(result.id) ||
      !RESULT_CONDITIONS.some((item) => item.id === result.condition) ||
      ![128, 256, 512].includes(result.budget) ||
      !Number.isInteger(result.sampleSize) ||
      result.sampleSize < 1 ||
      !Number.isInteger(result.correct) ||
      result.correct < 0 ||
      result.correct > result.sampleSize ||
      !Number.isFinite(result.meanTokens) ||
      result.meanTokens < 0 ||
      !Number.isFinite(result.meanSeconds) ||
      result.meanSeconds < 0 ||
      !text(result.model) ||
      !Number.isInteger(result.seed) ||
      !date(result.date) ||
      !["development", "official-test", "transfer"].includes(result.split) ||
      !text(result.notes) ||
      !/^\/results\/[a-zA-Z0-9._/-]+$/.test(result.source) ||
      result.source.includes("..")
    )
      throw new Error(
        "A result needs valid measurements and a local evidence file.",
      );
    ids.add(result.id);
  }
  return data;
}

import test from "node:test";
import assert from "node:assert/strict";
import { readFile, access } from "node:fs/promises";
import {
  DATASET,
  CONDITIONS,
  splitPlan,
  batchPlan,
  validateResearch,
} from "./public/research-model.js";

test("the interactive diagram and its local assets are complete", async () => {
  const html = await readFile(
    new URL("./public/index.html", import.meta.url),
    "utf8",
  );
  const css = await readFile(
    new URL("./public/styles.css", import.meta.url),
    "utf8",
  );
  for (const step of ["data", "rewrite", "select", "train", "test"]) {
    assert.equal(
      [...html.matchAll(new RegExp(`data-stage="${step}"`, "g"))].length,
      1,
    );
    const template = html.match(
      new RegExp(`<template id="stage-${step}">([\\s\\S]*?)</template>`),
    );
    assert.ok(template, `Missing ${step} explanation`);
    for (const level of ["plain", "example", "method"])
      assert.ok(template[1].includes(`data-panel="${level}"`));
  }
  for (const source of [...html.matchAll(/(?:src|href)="([^"#]+)"/g)].map(
    (x) => x[1],
  ))
    if (!/^https?:/.test(source))
      await access(new URL(`./public/${source}`, import.meta.url));
  for (const [, source] of css.matchAll(/url\("?([^"\)]+)"?\)/g))
    await access(new URL(`./public/${source}`, import.meta.url));
  assert.ok(!html.includes("\u2014"));
  assert.match(html, /<dialog\b[^>]*\bid="detail-dialog"/);
  assert.ok(html.includes('id="close-detail"'));
  assert.equal([...html.matchAll(/data-open="(?:data|train)"/g)].length, 2);
});

test("the pilot is nested and train-pool groups conserve the official total", () => {
  for (const count of [100, 1000, 6000, 6973]) {
    const plan = splitPlan(count);
    assert.equal(
      plan.training + plan.calibration + plan.development + plan.unused,
      DATASET.train,
    );
    assert.ok(plan.pilot <= plan.training);
    assert.equal(plan.test, 1319);
  }
  assert.equal(splitPlan(1000).unused, 5973);
  for (const count of [0, 99, 6974, 100.5, NaN])
    assert.throws(() => splitPlan(count), RangeError);
});
test("batch arithmetic keeps partial final batches", () => {
  assert.deepEqual(batchPlan(1000, 4), { batches: 250, lastBatch: 4 });
  assert.deepEqual(batchPlan(10, 4), { batches: 3, lastBatch: 2 });
  for (const values of [
    [10, 0],
    [10, 11],
    [-1, 1],
    [10, 1.5],
  ])
    assert.throws(() => batchPlan(...values), RangeError);
});
test("five matched conditions include ordinary training", () => {
  assert.equal(CONDITIONS.length, 5);
  assert.equal(new Set(CONDITIONS.map((item) => item.id)).size, 5);
  assert.equal(CONDITIONS[0].selection, "Unchanged worked solution");
});
test("published state and any result evidence must be valid", async () => {
  const state = validateResearch(
    JSON.parse(
      await readFile(new URL("./public/research.json", import.meta.url)),
    ),
  );
  for (const result of state.results)
    await access(new URL(`./public${result.source}`, import.meta.url));
  const valid = {
    id: "sample",
    condition: "original",
    budget: 128,
    sampleSize: 10,
    correct: 7,
    meanTokens: 120,
    meanSeconds: 1.2,
    model: "example",
    seed: 42,
    date: "2026-10-09",
    split: "development",
    notes: "Synthetic self-check only",
    source: "/results/sample.json",
  };
  assert.doesNotThrow(() => validateResearch({ ...state, results: [valid] }));
  assert.doesNotThrow(() =>
    validateResearch({
      ...state,
      results: [{ ...valid, condition: "unchanged" }],
    }),
  );
  for (const change of [
    { correct: 11 },
    { meanTokens: -1 },
    { sampleSize: 0 },
    { condition: "unknown" },
    { source: "/results/../private.txt" },
    { date: "2026-02-31" },
  ])
    assert.throws(() =>
      validateResearch({ ...state, results: [{ ...valid, ...change }] }),
    );
  assert.throws(() => validateResearch({ ...state, results: [valid, valid] }));
});

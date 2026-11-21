// The trainer (Python) and this engine (TypeScript) must do the same arithmetic.
// Both are tested against the same files in shared/, written by trainer/rps/make_parity.py.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { features, predict, checkBrain, type Brain, type Move, type Round } from "../src/index.ts";

const shared = new URL("../../shared/", import.meta.url);
const read = (name: string) => JSON.parse(readFileSync(new URL(name, shared), "utf8"));
const rounds = (h: [Move, Move][]): Round[] => h.map(([player, ai]) => ({ player, ai }));

test("shared examples: the engine derives the same inputs as the trainer", () => {
  const cases: { history: [Move, Move][]; features: number[] }[] = read("feature_cases.json");
  assert.ok(cases.length > 10);
  for (const c of cases) assert.deepEqual(features(rounds(c.history)), c.features);
});

test("shared brain: the engine predicts exactly what the trainer computed", () => {
  const brain: Brain = read("parity/brain.json");
  checkBrain(brain);
  const cases: { history: [Move, Move][]; expected: number[] }[] = read("parity/cases.json");
  for (const c of cases) {
    const p = predict(brain, rounds(c.history));
    for (let i = 0; i < 3; i++) assert.ok(Math.abs(p[i]! - c.expected[i]!) < 1e-9, `${p} vs ${c.expected}`);
  }
});

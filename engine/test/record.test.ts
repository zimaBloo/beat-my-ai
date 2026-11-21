import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { decode, decodeExtras, encodeExtras, gameFacts, percentile, ENGINE_VERSION, type Brain } from "../src/index.ts";

const shared = new URL("../../shared/", import.meta.url);
const read = (name: string) => JSON.parse(readFileSync(new URL(name, shared), "utf8"));

test("game facts: replaying the stored example gives the stored facts again", () => {
  const brain: Brain = read("parity/brain.json");
  const example = read("record_example.json");
  const facts = gameFacts(brain, decode(example.code), decodeExtras(example.extras));
  assert.deepEqual(facts, example.facts);
  assert.equal(facts.client!.think_ms.length, facts.rounds);
  assert.equal(gameFacts(brain, decode(example.code)).client, null);       // extra info is optional
  assert.equal(facts.engine, ENGINE_VERSION);
  assert.equal(facts.moves.length, facts.rounds);
  assert.equal(facts.score.player + facts.score.ai + facts.score.ties, facts.rounds);
});

test("game facts: a game is refused if it was played against a different brain", () => {
  const brain: Brain = read("parity/brain.json");
  assert.throws(() => gameFacts(brain, decode("v1.someother.7f3a9c02.RPSSRPRPSR")), /played against brain someother/);
  const untrained = gameFacts(null, decode("v1.untrained.00000001.RRRRRRRRRR"));
  assert.equal(untrained.brain, "untrained");
});

test("extra game info: goes there and back, and odd input is refused", () => {
  const info = { think_ms: [1840, 912, 655, 1203, 480, 733, 2950, 611, 540, 1322], input: "touch" as const, nth: 2, page: "1" };
  assert.equal(encodeExtras(info), "t=1840,912,655,1203,480,733,2950,611,540,1322;i=touch;n=2;p=1");
  assert.deepEqual(decodeExtras(encodeExtras(info)), info);
  assert.equal(encodeExtras({ ...info, think_ms: [1.6, -5, 5e9, 1, 1, 1, 1, 1, 1, 1] }).split(";")[0], "t=2,0,999999,1,1,1,1,1,1,1");
  for (const bad of ["", "t=1,2,3;i=touch;n=1;p=1", "t=1,1,1,1,1,1,1,1,1,1;i=brain;n=1;p=1",
                     "t=1,1,1,1,1,1,1,1,1,1;i=key;n=1;p=<b>", "t=1,1,1,1,1,1,1,1,1,x;i=key;n=1;p=1"]) {
    assert.throws(() => decodeExtras(bad), Error, bad);
  }
});

test("percentile: same answers as the Python side", () => {
  const margins = [-4, -2, -2, 0, 1, 3];
  assert.equal(percentile(margins, 3), 91.7);
  assert.equal(percentile(margins, -4), 8.3);
  assert.equal(percentile(margins, -2), 33.3);
  assert.equal(percentile([], 2), null);
});

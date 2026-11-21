import { test } from "node:test";
import assert from "node:assert/strict";
import {
  beats, outcome, counter, MOVES, makeRng, features, predict, checkBrain, chooseMove, expectedGain,
  Game, replay, ROUNDS_PER_GAME, encode, decode, type Move, type Brain,
} from "../src/index.ts";
import { repeatBrain } from "./fixtures.ts";

const ROCK = 0, PAPER = 1, SCISSORS = 2;

test("rules: paper beats rock, scissors beat paper, rock beats scissors, and nothing else", () => {
  const wins = MOVES.flatMap((a) => MOVES.filter((b) => beats(a, b)).map((b) => `${a}>${b}`));
  assert.deepEqual(wins.sort(), ["0>2", "1>0", "2>1"]);
  assert.equal(outcome(ROCK, SCISSORS), "win");
  assert.equal(outcome(ROCK, PAPER), "lose");
  assert.equal(outcome(PAPER, PAPER), "tie");
  for (const m of MOVES) assert.ok(beats(counter(m), m));
});

test("random numbers: same seed gives the same numbers, all in [0, 1)", () => {
  const a = makeRng(42), b = makeRng(42), c = makeRng(43);
  const xs = Array.from({ length: 50 }, () => a());
  assert.deepEqual(xs, Array.from({ length: 50 }, () => b()));
  assert.notDeepEqual(xs, Array.from({ length: 50 }, () => c()));
  assert.ok(xs.every((x) => x >= 0 && x < 1));
});

test("features: what the AI sees before the first round and after two rounds", () => {
  assert.deepEqual(features([]), [3, 7, 11, 15]);
  // round 1: player rock, AI paper (AI won). round 2: player scissors, AI paper (player won).
  const history = [{ player: ROCK as Move, ai: PAPER as Move }, { player: SCISSORS as Move, ai: PAPER as Move }];
  assert.deepEqual(features(history), [SCISSORS, 4 + PAPER, 8 + ROCK, 12 + 0]);
});

test("prediction: an untrained brain has no opinion; a trained one gives probabilities that add up to 1", () => {
  assert.deepEqual(predict(null, []), [1 / 3, 1 / 3, 1 / 3]);
  assert.deepEqual(predict({ ...repeatBrain(), trainedOn: 0 }, []), [1 / 3, 1 / 3, 1 / 3]);
  const p = predict(repeatBrain(), [{ player: PAPER, ai: ROCK }]);
  assert.ok(Math.abs(p[0] + p[1] + p[2] - 1) < 1e-12);
  assert.ok(p[PAPER] > 0.9, "the test brain expects the player to repeat paper");
});

test("brain check: a good brain passes, a brain with the wrong shape is refused", () => {
  checkBrain(repeatBrain());
  const bad: Brain = { version: "x", trainedOn: 1, layers: [{ weights: [[0, 0, 0]], bias: [0, 0, 0] }] };
  assert.throws(() => checkBrain(bad), /expected 16 inputs/);
});

test("policy: when the AI is sure you will play rock, it mostly plays paper; with no clue it plays evenly", () => {
  assert.deepEqual(expectedGain([1, 0, 0]), [0, 1, -1]);
  const rng = makeRng(7);
  const sure = [0, 0, 0], even = [0, 0, 0];
  for (let i = 0; i < 3000; i++) {
    sure[chooseMove([0.98, 0.01, 0.01], rng)]!++;
    even[chooseMove([1 / 3, 1 / 3, 1 / 3], rng)]!++;
  }
  assert.ok(sure[PAPER]! > 2700, `paper chosen ${sure[PAPER]} of 3000 times`);
  for (const n of even) assert.ok(n > 900 && n < 1100, `even split, got ${even}`);
});

test("fair play: the AI picks its move before it can see yours", () => {
  for (let seed = 1; seed <= 20; seed++) {
    const first = MOVES.map((mine) => new Game(repeatBrain(), seed).play(mine).ai);
    assert.ok(first.every((ai) => ai === first[0]), "the AI's move must not depend on the player's move in the same round");
  }
});

test("replay: the same brain, seed and player moves always give the same game", () => {
  const moves: Move[] = [0, 1, 2, 2, 0, 1, 0, 1, 2, 0];
  const live = new Game(repeatBrain(), 123456);
  for (const m of moves) live.play(m);
  const again = replay(repeatBrain(), 123456, moves);
  assert.deepEqual(again.rounds, live.rounds);
  assert.deepEqual(again.score, live.score);
  const s = live.score;
  assert.equal(s.player + s.ai + s.ties, ROUNDS_PER_GAME);
  assert.ok(live.finished);
  assert.throws(() => live.play(ROCK), /already finished/);
});

test("learning pays off: a brain that knows a habit beats a player who has it", () => {
  let ai = 0, player = 0;
  for (let seed = 0; seed < 200; seed++) {
    const g = replay(repeatBrain(), seed, Array<Move>(10).fill(ROCK));   // a player who always repeats rock
    ai += g.score.ai; player += g.score.player;
  }
  assert.ok(ai > player * 4, `AI ${ai} vs player ${player}`);
});

test("game code: goes there and back unchanged", () => {
  const sub = { brainVersion: "b3f9a2c1", seed: 0x7f3a9c02, moves: [0, 1, 2, 2, 0, 1, 0, 1, 2, 0] as Move[] };
  const text = encode(sub);
  assert.equal(text, "v1.b3f9a2c1.7f3a9c02.RPSSRPRPSR");
  assert.deepEqual(decode(text), sub);
  assert.equal(encode({ ...sub, seed: 5 }), "v1.b3f9a2c1.00000005.RPSSRPRPSR");
});

test("game code: anything that is not exactly a game is refused", () => {
  const bad = [
    "", "hello", "v2.b3f9a2c1.7f3a9c02.RPSSRPRPSR", "v1.b3f9a2c1.7f3a9c02.RPSSRPRPS",      // wrong version, too short
    "v1.b3f9a2c1.7f3a9c02.RPSSRPRPSRR", "v1.b3f9a2c1.7f3a9c02.rpssrprpsr",                  // too long, lower case
    "v1.b3f9a2c1.7f3a9c02.RPSSRPRPSX", "v1.b3f9a2c1.7f3a9c0.RPSSRPRPSR",                    // bad letter, short seed
    "v1.b3f9a2c1.7f3a9c02.RPSSRPRPSR <script>", "v1.B3F9.7f3a9c02.RPSSRPRPSR; rm -rf /",    // extra text
  ];
  for (const text of bad) assert.throws(() => decode(text), Error, text);
});

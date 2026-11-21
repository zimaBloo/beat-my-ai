// How the AI turns a prediction into a move.
// It does not always play the single best counter: that would make it easy to trick.
// It leans towards the moves that are likely to win, more strongly the surer it is.

import type { Prediction } from "./brain.ts";
import type { Move } from "./rules.ts";
import type { Rng } from "./rng.ts";

/** How strongly the AI commits to its best guess. 0 = always random, higher = more decisive. */
export const CONFIDENCE = 5;

/** Chance of winning minus chance of losing for each AI move, given the prediction. */
export function expectedGain(p: Prediction): [number, number, number] {
  // move a beats (a + 2) % 3 and loses to (a + 1) % 3
  return [p[2] - p[1], p[0] - p[2], p[1] - p[0]];
}

export function chooseMove(p: Prediction, rng: Rng): Move {
  const weights = expectedGain(p).map((gain) => Math.exp(CONFIDENCE * gain));
  let r = rng() * (weights[0]! + weights[1]! + weights[2]!);
  for (const move of [0, 1] as const) {
    r -= weights[move]!;
    if (r < 0) return move;
  }
  return 2;
}

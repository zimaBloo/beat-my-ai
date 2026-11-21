// What the AI looks at before each round.
// Four facts about the game so far, each written as a one-hot group of 4 inputs:
//   0..3   the player's last move        (rock, paper, scissors, or "no move yet")
//   4..7   the AI's last move
//   8..11  the player's move before that
//   12..15 who won the last round        (player, AI, tie, or "no round yet")

import { beats, type Round } from "./rules.ts";

export const INPUT_SIZE = 16;

/** The indices of the inputs that are switched on (all others are zero). */
export function features(history: readonly Round[]): number[] {
  const last = history[history.length - 1];
  const before = history[history.length - 2];
  const result = !last ? 3 : beats(last.player, last.ai) ? 0 : beats(last.ai, last.player) ? 1 : 2;
  return [last ? last.player : 3, 4 + (last ? last.ai : 3), 8 + (before ? before.player : 3), 12 + result];
}

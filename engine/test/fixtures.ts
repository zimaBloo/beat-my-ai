import type { Brain } from "../src/index.ts";

/** A hand-made brain with one belief: the player will repeat their last move. */
export function repeatBrain(): Brain {
  const weights = Array.from({ length: 16 }, () => [0, 0, 0]);
  for (const move of [0, 1, 2]) weights[move]![move] = 4;
  return { version: "test0001", trainedOn: 100, layers: [{ weights, bias: [0, 0, 0] }] };
}

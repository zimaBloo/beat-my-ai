// The rules of rock-paper-scissors.

/** 0 = rock, 1 = paper, 2 = scissors */
export type Move = 0 | 1 | 2;
export const MOVES: readonly Move[] = [0, 1, 2];
export const MOVE_NAMES = ["rock", "paper", "scissors"] as const;
export const MOVE_LETTERS = "RPS";

export type Outcome = "win" | "lose" | "tie";

/** True when `a` beats `b`: paper beats rock, scissors beat paper, rock beats scissors. */
export function beats(a: Move, b: Move): boolean {
  return (a - b + 3) % 3 === 1;
}

/** The round as seen by the player who threw `mine`. */
export function outcome(mine: Move, theirs: Move): Outcome {
  if (beats(mine, theirs)) return "win";
  if (beats(theirs, mine)) return "lose";
  return "tie";
}

/** The move that beats `m`. */
export function counter(m: Move): Move {
  return ((m + 1) % 3) as Move;
}

/** One finished round: what the player threw and what the AI threw. */
export interface Round {
  player: Move;
  ai: Move;
}

// Playing a game, and replaying one to check it.
// The AI picks its move before it sees the player's move, from the history, the brain and the seed alone.
// So anyone holding the same brain and seed can replay the player's moves and get the same game.

import { predict, type Brain, type Prediction } from "./brain.ts";
import { chooseMove } from "./policy.ts";
import { makeRng, type Rng } from "./rng.ts";
import { beats, type Move, type Round } from "./rules.ts";

/** Rounds in one game. A setting, not a law: change it here and everything follows. */
export const ROUNDS_PER_GAME = 10;

export interface Score {
  player: number;
  ai: number;
  ties: number;
}

export interface PlayedRound extends Round {
  /** What the AI expected the player to throw, before the round. */
  expected: Prediction;
}

/** A game in progress. Call `play` once per round with the player's move. */
export class Game {
  readonly rounds: PlayedRound[] = [];
  private readonly rng: Rng;
  private readonly brain: Brain | null;
  readonly length: number;

  constructor(brain: Brain | null, seed: number, length: number = ROUNDS_PER_GAME) {
    this.brain = brain;
    this.rng = makeRng(seed);
    this.length = length;
  }

  get finished(): boolean {
    return this.rounds.length >= this.length;
  }

  play(player: Move): PlayedRound {
    if (this.finished) throw new Error("the game is already finished");
    const expected = predict(this.brain, this.rounds);
    const ai = chooseMove(expected, this.rng);       // chosen without looking at `player`
    const round = { player, ai, expected };
    this.rounds.push(round);
    return round;
  }

  get score(): Score {
    const score = { player: 0, ai: 0, ties: 0 };
    for (const r of this.rounds) {
      if (beats(r.player, r.ai)) score.player++;
      else if (beats(r.ai, r.player)) score.ai++;
      else score.ties++;
    }
    return score;
  }
}

/** Plays the player's moves again with the same brain and seed. The result is the game that really happened. */
export function replay(brain: Brain | null, seed: number, playerMoves: readonly Move[]): Game {
  const game = new Game(brain, seed, playerMoves.length);
  for (const move of playerMoves) game.play(move);
  return game;
}

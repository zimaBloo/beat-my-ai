// The short text a finished game is sent as, for example:  v1.b3f9a2c1.7f3a9c02.RPSSRPRPSR
//   v1         format version
//   b3f9a2c1   which brain the game was played against
//   7f3a9c02   the seed, as 8 hex digits
//   RPSSRPRPSR the player's moves
// Only the player's moves are trusted. The AI's moves and the score are worked out again by replaying.

import { ROUNDS_PER_GAME } from "./game.ts";
import { MOVE_LETTERS, type Move } from "./rules.ts";

export interface Submission {
  brainVersion: string;
  seed: number;
  moves: Move[];
}

const PATTERN = /^v1\.([a-z0-9]{1,16})\.([0-9a-f]{8})\.([RPS]+)$/;

export function encode(s: Submission): string {
  const seed = (s.seed >>> 0).toString(16).padStart(8, "0");
  return `v1.${s.brainVersion}.${seed}.${s.moves.map((m) => MOVE_LETTERS[m]).join("")}`;
}

/** Returns the submission, or throws with a plain reason. Nothing else in the text is ever read or shown. */
export function decode(text: string, rounds: number = ROUNDS_PER_GAME): Submission {
  const match = PATTERN.exec(text.trim());
  if (!match) throw new Error("not a valid game code");
  const [, brainVersion, seedHex, letters] = match as unknown as [string, string, string, string];
  if (letters.length !== rounds) throw new Error(`a game has ${rounds} rounds, this one has ${letters.length}`);
  return {
    brainVersion,
    seed: parseInt(seedHex, 16),
    moves: [...letters].map((c) => MOVE_LETTERS.indexOf(c) as Move),
  };
}

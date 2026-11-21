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

/** Extra facts the game page reports about how a game was played. They cannot be checked, so nothing depends on them yet. */
export interface ClientInfo {
  /** how long the player took before each move, in milliseconds */
  think_ms: number[];
  /** how the moves were entered */
  input: "mouse" | "touch" | "key";
  /** which game this was in this browser: 1 for the first, counting games that were never sent */
  nth: number;
  /** version of the game page it was played on */
  page: string;
}

const EXTRA = /^t=(\d{1,6}(?:,\d{1,6})*);i=(mouse|touch|key);n=(\d{1,4});p=([a-z0-9.]{1,12})$/;

/** One short line, for example:  t=812,455,1290;i=touch;n=2;p=1 */
export function encodeExtras(c: ClientInfo): string {
  const times = c.think_ms.map((t) => Math.max(0, Math.min(999999, Math.round(t))));
  return `t=${times.join(",")};i=${c.input};n=${Math.max(1, Math.min(9999, c.nth))};p=${c.page}`;
}

/** Returns the extra facts, or throws. One thinking time per round is required. */
export function decodeExtras(text: string, rounds: number = ROUNDS_PER_GAME): ClientInfo {
  const match = EXTRA.exec(text.trim());
  if (!match) throw new Error("not valid extra game info");
  const think_ms = match[1]!.split(",").map(Number);
  if (think_ms.length !== rounds) throw new Error(`expected ${rounds} thinking times, got ${think_ms.length}`);
  return { think_ms, input: match[2] as ClientInfo["input"], nth: Number(match[3]), page: match[4]! };
}

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

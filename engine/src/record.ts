// The facts of one finished game, exactly as they are stored.
// With these facts and the archived brain, the game can be replayed move for move at any time in the future.
// The storage side (trainer/rps/records.py) adds: a running number, the time, where it came from and who played.

import type { Brain } from "./brain.ts";
import { replay, type Score } from "./game.ts";
import { MOVE_LETTERS } from "./rules.ts";
import type { ClientInfo, Submission } from "./codec.ts";

/** Raise this if the rules, the features or the way the AI picks a move ever change. Old games keep their number. */
export const ENGINE_VERSION = 1;

export interface GameFacts {
  /** record format version */
  v: 1;
  engine: number;
  /** which brain the game was played against */
  brain: string;
  /** the seed, as 8 hex digits */
  seed: string;
  rounds: number;
  /** the player's moves, e.g. "RPSSRPRPSR" */
  moves: string;
  /** the AI's moves in the same rounds */
  ai: string;
  score: Score;
  /** what the game page reported about how it was played (thinking times and so on), or null */
  client: ClientInfo | null;
}

/** Replays a submitted game against its brain and returns the facts to store. Throws if the brain does not match. */
export function gameFacts(brain: Brain | null, submission: Submission, client: ClientInfo | null = null): GameFacts {
  const version = brain ? brain.version : "untrained";
  if (version !== submission.brainVersion) throw new Error(`game was played against brain ${submission.brainVersion}, got ${version}`);
  const game = replay(brain, submission.seed, submission.moves);
  const letters = (pick: (r: { player: number; ai: number }) => number) => game.rounds.map((r) => MOVE_LETTERS[pick(r)]).join("");
  return {
    v: 1,
    engine: ENGINE_VERSION,
    brain: version,
    seed: (submission.seed >>> 0).toString(16).padStart(8, "0"),
    rounds: game.rounds.length,
    moves: letters((r) => r.player),
    ai: letters((r) => r.ai),
    score: game.score,
    client,
  };
}

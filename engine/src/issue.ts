// Reading a submitted game out of the text of a GitHub form.
// The text is written by a stranger, so only three things are ever taken from it, each by an exact pattern:
// the game code, the optional extra line, and a yes/no for showing the name. Everything else is ignored.

import { decode, decodeExtras, type ClientInfo, type Submission } from "./codec.ts";

export interface ParsedIssue {
  submission: Submission;
  client: ClientInfo | null;
  showName: boolean;
}

const MAX_LENGTH = 4000;
const GAME_LINE = /^v1\.[a-z0-9]{1,16}\.[0-9a-f]{8}\.[RPS]+$/;
const EXTRA_LINE = /^t=[0-9,]+;i=[a-z]+;n=[0-9]+;p=[a-z0-9.]+$/;

/** Throws with a plain reason if the text holds no valid game. */
export function parseIssue(body: string): ParsedIssue {
  if (body.length > MAX_LENGTH) throw new Error("the form text is too long");
  const lines = body.split(/\r?\n/).map((l) => l.trim());
  const games = lines.filter((l) => GAME_LINE.test(l));
  if (games.length !== 1) throw new Error(games.length ? "more than one game in the form" : "no game found in the form");
  const submission = decode(games[0]!);
  let client: ClientInfo | null = null;
  const extra = lines.find((l) => EXTRA_LINE.test(l));
  if (extra) {
    try { client = decodeExtras(extra, submission.moves.length); } catch { client = null; }   // extras are optional: bad ones are dropped, the game still counts
  }
  // the answer sits on the line after the question about the name
  const q = lines.findIndex((l) => l.startsWith("### Show my GitHub name"));
  const answer = q >= 0 ? lines.slice(q + 1).find((l) => l !== "") ?? "" : "";
  return { submission, client, showName: answer.toLowerCase() === "yes" };
}

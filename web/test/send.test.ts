// The send link must produce a form that the automatic job reads back correctly.
// GitHub turns the link's fields into the form text below; the job reads that text with parseIssue.
import { test } from "node:test";
import assert from "node:assert/strict";
import { sendUrl } from "../src/config.ts";
import { parseIssue } from "../../engine/src/index.ts";

const GAME = "v1.untrained.7f3a9c02.RPSSRPRPSR";
const EXTRA = "t=1840,912,655,1203,480,733,2950,611,540,1322;i=touch;n=2;p=1";

/** The form text GitHub creates from a ready-filled link (same labels as .github/ISSUE_TEMPLATE/game.yml). */
function formFrom(url: string): string {
  const q = new URL(url).searchParams;
  return `### Game\n\n${q.get("game")}\n\n### Extra\n\n${q.get("extras")}\n\n### Show my GitHub name on the profile? (yes or no)\n\n${q.get("name")}\n`;
}

test("send: the link opens the game form of the game repo", () => {
  const url = new URL(sendUrl(GAME, EXTRA, false)!);
  assert.equal(url.origin + url.pathname, "https://github.com/zimaBloo/beat-my-ai/issues/new");
  assert.equal(url.searchParams.get("template"), "game.yml");
});

test("send: the ticked box shows the name, the empty box keeps the player anonymous", () => {
  assert.equal(parseIssue(formFrom(sendUrl(GAME, EXTRA, true)!)).showName, true);
  assert.equal(parseIssue(formFrom(sendUrl(GAME, EXTRA, false)!)).showName, false);
});

test("send: the game and the extras arrive intact", () => {
  const p = parseIssue(formFrom(sendUrl(GAME, EXTRA, false)!));
  assert.equal(p.submission.moves.length, 10);
  assert.equal(p.client!.input, "touch");
});

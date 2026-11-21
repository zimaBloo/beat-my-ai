import { test } from "node:test";
import assert from "node:assert/strict";
import { parseIssue } from "../src/index.ts";

const form = (game: string, extra: string, name: string) =>
  `### Game\n\n${game}\n\n### Extra\n\n${extra}\n\n### Show my GitHub name on the profile? (yes or no)\n\n${name}\n`;
const GAME = "v1.untrained.7f3a9c02.RPSSRPRPSR";
const EXTRA = "t=1840,912,655,1203,480,733,2950,611,540,1322;i=touch;n=2;p=1";

test("form: a normal submission is read", () => {
  const p = parseIssue(form(GAME, EXTRA, "yes"));
  assert.equal(p.submission.brainVersion, "untrained");
  assert.equal(p.submission.moves.length, 10);
  assert.equal(p.client!.input, "touch");
  assert.equal(p.showName, true);
});

test("form: the name is shown only on an exact yes", () => {
  for (const answer of ["no", "", "_No response_", "yes please", "maybe"]) assert.equal(parseIssue(form(GAME, EXTRA, answer)).showName, false, answer);
  assert.equal(parseIssue(form(GAME, EXTRA, "YES")).showName, true);
  assert.equal(parseIssue(`${GAME}\nyes`).showName, false, "a stray yes outside the question does not count");
});

test("form: missing or broken extras do not lose the game", () => {
  assert.equal(parseIssue(form(GAME, "_No response_", "no")).client, null);
  assert.equal(parseIssue(form(GAME, "t=1,2,3;i=touch;n=1;p=1", "no")).client, null);      // wrong number of times
  assert.equal(parseIssue(GAME).client, null);
});

test("form: anything without exactly one valid game is refused", () => {
  for (const body of ["", "hello", form("v1.untrained.7f3a9c02.RPS", EXTRA, "no"), `${GAME}\n${GAME}`,
                      form("v1.untrained.7f3a9c02.RPSSRPRPSR; rm -rf /", EXTRA, "no"), "x".repeat(5000)]) {
    assert.throws(() => parseIssue(body), Error, body.slice(0, 40));
  }
});

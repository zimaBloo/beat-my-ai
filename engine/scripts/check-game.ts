// Step 1 of the automatic job: read the submitted form, replay the game, print what to store.
//   ISSUE_BODY="..." node engine/scripts/check-game.ts
// Always prints one line of JSON: {"ok": true, "facts": {...}, "showName": false} or {"ok": false, "reason": "..."}.
// The form text only ever arrives through the ISSUE_BODY environment variable, never as part of a command.
import { existsSync, readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { checkBrain, gameFacts, parseIssue, type Brain } from "../src/index.ts";

// every version of the AI is kept in data/brains; DATA_DIR points somewhere else only in tests
const brains = process.env.DATA_DIR ? pathToFileURL(`${process.env.DATA_DIR}/brains/`) : new URL("../../data/brains/", import.meta.url);

function check(body: string) {
  const { submission, client, showName } = parseIssue(body);
  let brain: Brain | null = null;
  if (submission.brainVersion !== "untrained") {
    const file = new URL(`${submission.brainVersion}.json`, brains);
    if (!existsSync(file)) throw new Error("this game was played against a version of the AI that does not exist");
    brain = JSON.parse(readFileSync(file, "utf8")) as Brain;
    checkBrain(brain);
  }
  return { ok: true, facts: gameFacts(brain, submission, client), showName };
}

let result: unknown;
try { result = check(process.env.ISSUE_BODY ?? ""); }
catch (e) { result = { ok: false, reason: e instanceof Error ? e.message : "could not read the game" }; }
console.log(JSON.stringify(result));

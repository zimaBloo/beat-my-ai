// Writes shared/record_example.json: one real game replayed against the shared test brain.
// The storage tests (Python) and the engine tests both check against it.
//   node scripts/make-record-example.ts
import { readFileSync, writeFileSync } from "node:fs";
import { decode, decodeExtras, gameFacts, type Brain } from "../src/index.ts";

const shared = new URL("../../shared/", import.meta.url);
const brain: Brain = JSON.parse(readFileSync(new URL("parity/brain.json", shared), "utf8"));
const code = `v1.${brain.version}.7f3a9c02.RPSSRPRPSR`;
const extras = "t=1840,912,655,1203,480,733,2950,611,540,1322;i=touch;n=2;p=1";
const facts = gameFacts(brain, decode(code), decodeExtras(extras));
writeFileSync(new URL("record_example.json", shared), JSON.stringify({ code, extras, facts }, null, 1) + "\n");
console.log(code, "→", facts.ai, facts.score);

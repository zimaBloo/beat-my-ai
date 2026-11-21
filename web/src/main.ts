import "./style.css";
import {
  Game, ROUNDS_PER_GAME, MOVE_NAMES, checkBrain, encode, encodeExtras, outcome, percentile,
  type Brain, type ClientInfo, type Move, type PlayedRound,
} from "../../engine/src/index.ts";
import { PAGE_VERSION, sendUrl } from "./config.ts";
import { Stage, type Sprites } from "./stage.ts";
import bundledBrain from "../../data/brain.json";
import bundledStats from "../../data/stats.json";
import humanRock from "./gloves/human-rock.webp";
import humanPaper from "./gloves/human-paper.webp";
import humanScissors from "./gloves/human-scissors.webp";
import aiRock from "./gloves/ai-rock.webp";
import aiPaper from "./gloves/ai-paper.webp";
import aiScissors from "./gloves/ai-scissors.webp";

interface Stats { games: number; moves: number; margins: number[]; }

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const sprites: Sprites = { human: [humanRock, humanPaper, humanScissors], ai: [aiRock, aiPaper, aiScissors] };
const stage = new Stage({
  stage: $("stage"), armYou: $("armYou"), armAi: $("armAi"), imgYou: $<HTMLImageElement>("imgYou"), imgAi: $<HTMLImageElement>("imgAi"),
  burst: document.getElementById("burst") as unknown as SVGSVGElement, verdict: $("verdict"),
}, sprites);
sprites.human.forEach((src, i) => ($<HTMLImageElement>(`btn${i}`).src = src));

let brain: Brain | null = null;
let stats: Stats = bundledStats as Stats;
let game: Game;
let seed = 0;
let busy = false;
let readyAt = 0;
let lastInput: ClientInfo["input"] = "mouse";
let thinkMs: number[] = [];
let nth = 1;

/** The newest brain and statistics if they can be fetched, otherwise the ones packed with the page. */
async function loadData(): Promise<void> {
  const usable = (b: Brain): Brain | null => { checkBrain(b); return b.trainedOn > 0 ? b : null; };
  brain = usable(bundledBrain as unknown as Brain);
  try {
    const [b, s] = await Promise.all([fetch("./data/brain.json", { cache: "no-store" }), fetch("./data/stats.json", { cache: "no-store" })]);
    if (b.ok && s.ok) { brain = usable(await b.json() as Brain); stats = await s.json() as Stats; }
  } catch { /* opened from disk or offline: the packed data is fine */ }
  $("brainLine").textContent = brain
    ? `So far it has studied ${stats.moves} moves from ${stats.games} games.`
    : "Nobody has played yet, so right now it is guessing.";
}

function newGame(): void {
  seed = crypto.getRandomValues(new Uint32Array(1))[0]!;
  game = new Game(brain, seed);
  thinkMs = [];
  try { nth = Number(localStorage.getItem("bma.games") ?? "0") + 1; localStorage.setItem("bma.games", String(nth)); } catch { nth = 1; }
  $("rounds").textContent = String(ROUNDS_PER_GAME);
  $("end").hidden = true;
  $("moves").hidden = false;
  $<HTMLInputElement>("showName").checked = false;
  stage.rest(); stage.clearVerdict();
  $("think").textContent = brain ? "Pick a move. The AI has already chosen its own." : "Pick a move. The AI is untrained, so it is guessing.";
  showScore(); setBusy(false);
}

function setBusy(on: boolean): void {
  busy = on;
  document.querySelectorAll<HTMLButtonElement>(".move").forEach((b) => (b.disabled = on));
  if (!on) readyAt = performance.now();
}

function showScore(): void {
  const s = game.score;
  $("round").textContent = String(Math.min(ROUNDS_PER_GAME, game.rounds.length + 1));
  $("sYou").textContent = String(s.player); $("sAi").textContent = String(s.ai); $("sTie").textContent = String(s.ties);
}

function explain(round: PlayedRound): void {
  if (!brain) { $("think").textContent = "It guessed at random. It has nothing to learn from yet."; return; }
  const best = ([0, 1, 2] as Move[]).reduce((a, b) => (round.expected[b] > round.expected[a] ? b : a));
  const sure = Math.round(round.expected[best] * 100);
  $("think").innerHTML = `It expected you to play <b>${MOVE_NAMES[best]}</b> (${sure}% sure). ${best === round.player ? "It read you." : "It was wrong."}`;
}

async function play(move: Move): Promise<void> {
  if (busy || game.finished) return;
  thinkMs.push(performance.now() - readyAt);
  setBusy(true);
  $("think").textContent = "";
  const round = game.play(move);                       // the AI's move was fixed before this call could reveal yours
  await stage.playRound(round.player, round.ai, outcome(round.player, round.ai));
  showScore(); explain(round);
  if (game.finished) finish(); else setBusy(false);
}

function finish(): void {
  const s = game.score;
  $("moves").hidden = true;
  $("endTitle").textContent = s.player > s.ai ? `You beat it, ${s.player} to ${s.ai}.` : s.ai > s.player ? `The AI won, ${s.ai} to ${s.player}.` : `A draw, ${s.player} all.`;
  const rank = percentile(stats.margins, s.player - s.ai);
  $("endRank").innerHTML = rank === null || stats.games < 5
    ? "You are among the first to play. Rankings appear after a few more games."
    : `That is better than <b>${Math.round(rank)}%</b> of the ${stats.games} games played so far.`;
  $("end").hidden = false;
  updateSend();
  $("end").scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function updateSend(): void {
  const code = encode({ brainVersion: brain ? brain.version : "untrained", seed, moves: game.rounds.map((r) => r.player) });
  const extras = encodeExtras({ think_ms: thinkMs, input: lastInput, nth, page: PAGE_VERSION });
  const url = sendUrl(code, extras, $<HTMLInputElement>("showName").checked);
  const send = $<HTMLAnchorElement>("send");
  if (url) { send.href = url; send.removeAttribute("aria-disabled"); $("sendNote").textContent = "This opens a ready-filled form on GitHub. Press Create there. You need a GitHub account."; }
  else { send.removeAttribute("href"); send.setAttribute("aria-disabled", "true"); $("sendNote").textContent = `Sending opens when the game goes live. Your game: ${code}`; }
}

$("moves").addEventListener("pointerdown", (e) => { lastInput = e.pointerType === "touch" ? "touch" : "mouse"; });
$("moves").addEventListener("click", (e) => {
  const button = (e.target as HTMLElement).closest<HTMLButtonElement>(".move");
  if (button) void play(Number(button.dataset.move) as Move);
});
document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey || $("moves").hidden) return;
  const move = "rps".indexOf(e.key.toLowerCase());
  if (move >= 0) { lastInput = "key"; void play(move as Move); }
});
$("showName").addEventListener("change", updateSend);
$("again").addEventListener("click", newGame);

await loadData();
newGame();

// For automatic checks: ?auto=RPSRPS plays those moves without waiting for the motion.
const auto = new URLSearchParams(location.search).get("auto");
if (auto) {
  if (!new URLSearchParams(location.search).has("motion")) stage.frameMs = 0;
  for (const letter of auto.toUpperCase()) { const m = "RPS".indexOf(letter); if (m >= 0) await play(m as Move); }
}

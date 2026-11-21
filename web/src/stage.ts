// The two gloves on stage. The pictures are still images; this file moves them the way the 3D loop does:
// each glove swings from an elbow off screen, stretches when it moves fast and squashes when it stops,
// twelve drawings a second. The numbers below are the same pose keys the Blender animation uses.

import type { Move, Outcome } from "../../engine/src/index.ts";
import { FPS } from "./config.ts";

/** One drawing: swing in degrees, stretch along the arm, 0 = fist / 1 = thrown pose, slide along the arm. */
type Key = readonly [swing: number, stretch: number, thrown: number, slide: number];

const SHAKE: Key[] = [[12, 1.12, 0, 0], [30, 1.14, 0, 0], [38, 0.94, 0, 0], [35, 1.0, 0, 0], [10, 1.2, 0, 0], [-8, 0.78, 0, 0]];
const THROW: Key[] = [[-5, 0.9, 0, 0], [16, 1.06, 0, -0.2], [3, 1.3, 0.75, 0.18], [-3, 0.88, 1.12, 0.1], [0, 1.05, 1, 0.03]];
const HOLD: Key[] = [[0, 1, 1, 0], [1, 1, 1, 0], [0, 1, 1, 0]];
const WIN: Key[] = [[-3, 0.84, 1, 0.04], [17, 1.2, 1, 0.1], [25, 0.98, 1, 0.12], [22, 1.02, 1, 0.12], [6, 1.16, 1, 0.08], [-5, 0.84, 1, 0.04], [0, 1.06, 1, 0.02], [0, 1, 1, 0]];
const LOSE: Key[] = [[0, 1, 1, 0], [7, 1.1, 1, -0.04], [-5, 0.92, 1, -0.1], [-10, 0.84, 1, -0.15], [-13, 0.8, 1, -0.18], [-11.5, 0.8, 1, -0.18], [-14.5, 0.8, 1, -0.18], [-11.5, 0.8, 1, -0.18]];
const TIE: Key[] = [[0, 1, 1, 0], [6, 1.08, 1, 0], [0, 0.94, 1, 0], [0, 1, 1, 0], [6, 1.08, 1, 0], [0, 0.94, 1, 0], [0, 1, 1, 0], [0, 1, 1, 0]];
const CLOSE: Key[] = [[-4, 0.95, 0.7, -0.05], [2, 1.06, 0.3, 0], [0, 0.97, 0, 0], [0, 1, 0, 0]];
const SHAKES = 2;
const REACTION = { win: WIN, lose: LOSE, tie: TIE } as const;
const REST: Key = [0, 1, 0, 0];

export interface Sprites { human: readonly [string, string, string]; ai: readonly [string, string, string]; }
export interface StageParts { stage: HTMLElement; armYou: HTMLElement; armAi: HTMLElement; imgYou: HTMLImageElement; imgAi: HTMLImageElement; burst: SVGSVGElement; verdict: HTMLElement; }

const sleep = (ms: number) => new Promise<void>((done) => setTimeout(done, ms));
const VERDICT = { win: ["You win", "you"], lose: ["AI wins", "ai"], tie: ["Tie", "tie"] } as const;

export class Stage {
  /** Milliseconds per drawing. Zero skips the motion (used for automatic checks). */
  frameMs = 1000 / FPS;
  private readonly still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  private readonly p: StageParts;
  private readonly sprites: Sprites;
  /** The last throw stays on stage, with its verdict, until the next round starts. */
  private shown: { you: Move; ai: Move } | null = null;

  constructor(parts: StageParts, sprites: Sprites) {
    this.p = parts;
    this.sprites = sprites;
    this.rest();
  }

  /** Both gloves as fists, waiting. */
  rest(): void {
    this.pose(this.p.armYou, this.p.imgYou, this.sprites.human, REST, 0);
    this.pose(this.p.armAi, this.p.imgAi, this.sprites.ai, REST, 0);
    this.p.burst.replaceChildren();
    this.shown = null;
  }

  clearVerdict(): void {
    this.p.verdict.textContent = "";
    this.p.verdict.className = "verdict";
  }

  /** Plays one round: close the last throw, shake, throw, show who won, react. The throw then stays on stage.
   *  Resolves when the next round may start. */
  async playRound(you: Move, ai: Move, result: Outcome): Promise<void> {
    this.clearVerdict();
    this.p.burst.replaceChildren();
    if (this.shown && !this.still) {                    // fold the previous throw back into fists first
      for (const key of CLOSE) {
        this.pose(this.p.armYou, this.p.imgYou, this.sprites.human, key, this.shown.you);
        this.pose(this.p.armAi, this.p.imgAi, this.sprites.ai, key, this.shown.ai);
        if (this.frameMs > 0) await sleep(this.frameMs);
      }
    }
    const mirror: Outcome = result === "win" ? "lose" : result === "lose" ? "win" : "tie";
    const lead: Key[] = this.still ? [] : [...Array.from({ length: SHAKES }, () => SHAKE).flat(), ...THROW];
    const mine = [...lead, ...HOLD, ...(this.still ? [] : REACTION[result])];
    const theirs = [...lead, ...HOLD, ...(this.still ? [] : REACTION[mirror])];
    const reveal = lead.length, react = lead.length + HOLD.length;
    for (let i = 0; i < mine.length; i++) {
      if (i === reveal) this.showVerdict(result);
      const a = mine[i]!, b = theirs[i]!;
      this.pose(this.p.armYou, this.p.imgYou, this.sprites.human, a, you);
      this.pose(this.p.armAi, this.p.imgAi, this.sprites.ai, b, ai);
      if (i >= react && result !== "tie") this.drawBurst(result === "win" ? "you" : "ai", result === "win" ? a : b, i - react);
      if (this.frameMs > 0) await sleep(this.frameMs);
    }
    this.p.burst.replaceChildren();
    this.shown = { you, ai };
  }

  private showVerdict(result: Outcome): void {
    const [text, cls] = VERDICT[result];
    this.p.verdict.textContent = text;
    this.p.verdict.className = `verdict ${cls} pop`;
  }

  private pose(arm: HTMLElement, img: HTMLImageElement, set: readonly [string, string, string], key: Key, move: Move): void {
    const [swing, stretch, thrown, slide] = key;
    arm.style.setProperty("--swing", String(swing));
    arm.style.setProperty("--stretch", String(stretch));
    arm.style.setProperty("--squash", String(1 / Math.sqrt(stretch)));      // thinner when longer: the volume stays the same
    arm.style.setProperty("--slide", String(slide));
    const src = thrown >= 0.5 ? set[move] : set[0];
    if (img.getAttribute("src") !== src) img.src = src;
  }

  /** Lines and stars popping around the winner, redrawn every second drawing so they boil. */
  private drawBurst(who: "you" | "ai", key: Key, r: number): void {
    const box = this.p.stage.getBoundingClientRect();
    const u = box.width / 7.03;
    const side = who === "you" ? -1 : 1;
    const th = (key[0] * Math.PI) / 180, reach = 1.85 + key[3];
    const cx = box.width / 2 + side * (3.35 - reach * Math.cos(th)) * u - side * 0.25 * u;
    const cy = box.height / 2 + (0.51 - reach * Math.sin(th) - 0.1) * u;
    const grow = Math.min(1, 0.55 + 0.25 * r), boil = Math.floor(r / 2) % 2;
    const colour = who === "you" ? "#eef2fa" : "#96beff";
    let shapes = "";
    const n = 14;
    for (let i = 0; i < n; i++) {
      const a = (2 * Math.PI * (i + 0.5 * boil)) / n;
      if (Math.abs(Math.cos(a)) > 0.93 && Math.cos(a) > 0 === (who === "you")) continue;        // keep the middle clear
      const inner = 1.2 * u * grow, len = (i % 2 === boil ? 0.4 : 0.2) * u * grow, w = 0.045 * u;
      const ax = Math.cos(a), ay = Math.sin(a) * 0.86;
      const x0 = cx + ax * inner, y0 = cy + ay * inner, x1 = cx + ax * (inner + len), y1 = cy + ay * (inner + len);
      shapes += `<polygon points="${x0 - ay * w},${y0 + ax * w} ${x0 + ay * w},${y0 - ax * w} ${x1},${y1}"/>`;
    }
    this.p.burst.setAttribute("viewBox", `0 0 ${box.width} ${box.height}`);
    this.p.burst.innerHTML = `<g fill="${colour}">${shapes}</g>`;
  }
}

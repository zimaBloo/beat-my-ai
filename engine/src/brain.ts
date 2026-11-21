// The AI's "brain": a small neural network stored as plain numbers in a JSON file.
// Training happens elsewhere (Python). This file only reads a brain and asks it for a prediction.

import { features, INPUT_SIZE } from "./features.ts";
import type { Round } from "./rules.ts";

export interface Layer {
  /** weights[input][output] */
  weights: number[][];
  bias: number[];
}

export interface Brain {
  /** Changes every time the AI is retrained. A game is always checked against the brain it was played with. */
  version: string;
  /** How many moves the brain has learned from. Zero means untrained. */
  trainedOn: number;
  layers: Layer[];
}

/** Probabilities for the player's next move: [rock, paper, scissors]. They add up to 1. */
export type Prediction = [number, number, number];

/** Throws if the brain's shape is wrong, so a broken file is caught before a game starts. */
export function checkBrain(brain: Brain): void {
  if (!brain.layers.length) throw new Error("brain has no layers");
  let width = INPUT_SIZE;
  for (const [i, layer] of brain.layers.entries()) {
    if (layer.weights.length !== width) throw new Error(`layer ${i}: expected ${width} inputs, got ${layer.weights.length}`);
    const outputs = layer.bias.length;
    if (layer.weights.some((row) => row.length !== outputs)) throw new Error(`layer ${i}: uneven weight rows`);
    width = outputs;
  }
  if (width !== 3) throw new Error(`last layer must have 3 outputs, got ${width}`);
}

/** What the brain expects the player to throw next. An untrained brain has no opinion: one third each. */
export function predict(brain: Brain | null, history: readonly Round[]): Prediction {
  if (!brain || brain.trainedOn === 0) return [1 / 3, 1 / 3, 1 / 3];
  // first layer: the inputs are one-hot, so we only add up the rows that are switched on
  const first = brain.layers[0]!;
  let values = first.bias.slice();
  for (const index of features(history)) {
    const row = first.weights[index]!;
    for (let j = 0; j < values.length; j++) values[j]! += row[j]!;
  }
  for (let l = 1; l < brain.layers.length; l++) {
    const layer = brain.layers[l]!;
    const input = values.map(Math.tanh);
    values = layer.bias.slice();
    for (let i = 0; i < input.length; i++) {
      const row = layer.weights[i]!;
      for (let j = 0; j < values.length; j++) values[j]! += input[i]! * row[j]!;
    }
  }
  const top = Math.max(...values);
  const exp = values.map((v) => Math.exp(v - top));
  const sum = exp.reduce((a, b) => a + b, 0);
  return [exp[0]! / sum, exp[1]! / sum, exp[2]! / sum];
}

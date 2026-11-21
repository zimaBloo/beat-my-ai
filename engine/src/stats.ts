// Small statistics shared with the game page. Kept identical to trainer/rps/stats.py.

/** Share of stored games this result is better than, counting equal results as half. Null if there are no games yet. */
export function percentile(margins: readonly number[], mine: number): number | null {
  if (margins.length === 0) return null;
  const below = margins.filter((m) => m < mine).length;
  const equal = margins.filter((m) => m === mine).length;
  return Math.round((1000 * (below + 0.5 * equal)) / margins.length) / 10;
}

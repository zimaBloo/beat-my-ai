"""Everything shown to people, rebuilt from the stored games. Nothing here is stored as the only copy.

    python -m rps.stats --games ../data/games.jsonl --out ../data/stats.json

Change this file, run it again, and every number is recomputed from the very first game.
"""
import argparse
import json
import statistics
from pathlib import Path

from .features import MOVE_LETTERS, beats
from .records import load_records


def margin(record: dict) -> int:
    """Rounds the player won minus rounds the AI won."""
    return record["score"]["player"] - record["score"]["ai"]


def percentile(margins: list[int], mine: int) -> float | None:
    """Share of stored games this result is better than, counting equal results as half. None if there are no games."""
    if not margins:
        return None
    below = sum(m < mine for m in margins)
    equal = sum(m == mine for m in margins)
    return round(100 * (below + 0.5 * equal) / len(margins), 1)


def rebuild(records: list[dict]) -> dict:
    humans = sum(margin(r) > 0 for r in records)
    ai = sum(margin(r) < 0 for r in records)
    openings = [0, 0, 0]
    after_win = [0, 0]                                   # [repeated the move, times the player had just won]
    for r in records:
        openings[MOVE_LETTERS.index(r["moves"][0])] += 1
        for i in range(1, r["rounds"]):
            p, a = MOVE_LETTERS.index(r["moves"][i - 1]), MOVE_LETTERS.index(r["ai"][i - 1])
            if beats(p, a):
                after_win[1] += 1
                after_win[0] += r["moves"][i] == r["moves"][i - 1]
    # how often the AI won a decided round, averaged over the last 8 games, one point per game
    line = []
    for i in range(len(records)):
        window = records[max(0, i - 7): i + 1]
        w, l = sum(r["score"]["ai"] for r in window), sum(r["score"]["player"] for r in window)
        line.append(round(w / (w + l), 3) if w + l else 0.5)
    think = [t for r in records if r["client"] for t in r["client"]["think_ms"]]
    last = records[-1] if records else None
    return {
        "games": len(records),
        "moves": sum(r["rounds"] for r in records),
        "players": len({r["player"] for r in records}),
        "humans_won": humans, "ai_won": ai, "draws": len(records) - humans - ai,
        "opening": {name: openings[i] for i, name in enumerate(("rock", "paper", "scissors"))},
        "repeat_after_win": {"repeated": after_win[0], "of": after_win[1]},
        "median_think_ms": round(statistics.median(think)) if think else None,
        "ai_round_win_rate": line,
        "margins": sorted(margin(r) for r in records),      # the game page works out a visitor's percentile from this
        "last": None if last is None else {"name": last["name"], "score": last["score"], "at": last["at"]},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    stats = rebuild(load_records(args.games))
    Path(args.out).write_text(json.dumps(stats, indent=1) + "\n")
    print(f"{stats['games']} games → {args.out}")


if __name__ == "__main__":
    main()

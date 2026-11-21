"""Retrain the AI on all collected games and write the new brain and its report.

    python -m rps.train --games ../data/games.jsonl --brain ../data/brain.json --archive ../data/brains --report ../data/report.json
"""
import argparse
import json

from .data import examples, load_games, split_by_time
from .evaluate import evaluate
from .model import export_brain, save_brain, train


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--games", required=True)
    ap.add_argument("--brain", required=True)
    ap.add_argument("--archive", help="folder that keeps every brain version")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    games = load_games(args.games)
    older, newest = split_by_time(games)
    report = evaluate(train(examples(older)), older, newest)      # judged on games it has not seen
    rows = examples(games)
    brain = export_brain(train(rows), trained_on=len(rows))        # the brain that plays learns from everything
    report.update({"games": len(games), "moves": len(rows), "brain": brain["version"]})
    save_brain(brain, args.brain, args.archive)
    with open(args.report, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"{len(games)} games, {len(rows)} moves → brain {brain['version']}")


if __name__ == "__main__":
    main()

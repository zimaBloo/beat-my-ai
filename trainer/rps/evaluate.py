"""Measuring how well the AI predicts people, against simple yardsticks.

The question is always: on games it has NOT learned from, how often does it guess the player's next move?
Pure guessing gets one in three. Two simple rules of thumb are measured alongside, so a good number means something.
"""
import math

from .data import Example, Game, examples
from .model import predict


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% range for a share measured on n tries. Wide when n is small, which is the honest answer."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def _share(hits: int, n: int) -> dict:
    low, high = wilson(hits, n)
    return {"accuracy": hits / n if n else None, "low": low, "high": high}


def evaluate(model, train_games: list[Game], test_games: list[Game]) -> dict:
    test: list[Example] = examples(test_games)
    n = len(test)
    report: dict = {"train_games": len(train_games), "test_games": len(test_games), "test_moves": n}
    if n == 0:
        report["note"] = "Not enough games yet to measure anything."
        return report
    probs = predict(model, test)
    hits = sum(int(probs[i].argmax()) == move for i, (_x, move) in enumerate(test))
    log_loss = -sum(math.log(max(float(probs[i][move]), 1e-12)) for i, (_x, move) in enumerate(test)) / n
    # yardstick 1: always guess the move people made most often in the older games
    counts = [0, 0, 0]
    for _x, move in examples(train_games):
        counts[move] += 1
    favourite = counts.index(max(counts))
    # yardstick 2: guess that the player repeats their last move (rock on the first round)
    repeat_hits = sum((x[0] if x[0] < 3 else 0) == move for x, move in test)
    report.update({
        "ai": {**_share(hits, n), "log_loss": log_loss},
        "guessing": {"accuracy": 1 / 3, "log_loss": math.log(3)},
        "most_common_move": _share(sum(move == favourite for _x, move in test), n),
        "repeat_last_move": _share(repeat_hits, n),
    })
    if n < 100:
        report["note"] = f"Only {n} test moves so far: the ranges are wide and the numbers can still swing."
    return report

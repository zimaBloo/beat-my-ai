"""What the AI looks at before each round. Must stay identical to engine/src/features.ts.

Both sides are tested against the same examples in shared/feature_cases.json.
Moves: 0 = rock, 1 = paper, 2 = scissors. A round is (player, ai).
"""
INPUT_SIZE = 16
MOVE_LETTERS = "RPS"


def beats(a: int, b: int) -> bool:
    return (a - b + 3) % 3 == 1


def features(history: list[tuple[int, int]]) -> list[int]:
    """Indices of the inputs that are switched on (all others are zero)."""
    last = history[-1] if history else None
    before = history[-2] if len(history) > 1 else None
    if last is None:
        result = 3
    elif beats(last[0], last[1]):
        result = 0
    elif beats(last[1], last[0]):
        result = 1
    else:
        result = 2
    return [last[0] if last else 3, 4 + (last[1] if last else 3), 8 + (before[0] if before else 3), 12 + result]

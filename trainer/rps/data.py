"""Reading the collected games.

data/games.jsonl holds one game per line, oldest first:
    {"moves": "RPSSRPRPSR", "ai": "PRSSRSPRPS"}
`moves` are the player's throws, `ai` the AI's throws in the same rounds. Nothing about who played is stored here.
"""
import json
from pathlib import Path

from .features import MOVE_LETTERS, features

Game = list[tuple[int, int]]            # rounds as (player, ai)
Example = tuple[list[int], int]         # (switched-on inputs, the move the player then made)


def parse_game(moves: str, ai: str) -> Game:
    if len(moves) != len(ai) or not moves or set(moves + ai) - set(MOVE_LETTERS):
        raise ValueError(f"bad game: {moves!r} / {ai!r}")
    return [(MOVE_LETTERS.index(m), MOVE_LETTERS.index(a)) for m, a in zip(moves, ai)]


def load_games(path: str | Path) -> list[Game]:
    p = Path(path)
    if not p.exists():
        return []
    games = []
    for line in p.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            games.append(parse_game(row["moves"], row["ai"]))
    return games


def examples(games: list[Game]) -> list[Example]:
    """Every round of every game becomes one lesson: given the game so far, what did the player throw?"""
    out = []
    for game in games:
        for i, (player, _ai) in enumerate(game):
            out.append((features(game[:i]), player))
    return out


def split_by_time(games: list[Game], test_share: float = 0.2) -> tuple[list[Game], list[Game]]:
    """Older games for learning, the newest for testing: the AI is always judged on people it has not seen yet."""
    n_test = max(1, round(len(games) * test_share)) if len(games) >= 5 else 0
    return games[: len(games) - n_test], games[len(games) - n_test:]

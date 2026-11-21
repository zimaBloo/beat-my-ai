"""Pretend players with typical human habits. For tests and demos only: never mixed into the real games."""
import random

from .data import Game
from .features import beats


def habit_player(rng: random.Random):
    """A player who opens with rock a bit too often, tends to repeat a win, and tends to switch after a loss."""
    stay = 0.12 + rng.random() * 0.30
    shift = 0.10 + rng.random() * 0.28

    def move(history: Game) -> int:
        if not history:
            return rng.choices([0, 1, 2], weights=[0.40, 0.32, 0.28])[0]
        player, ai = history[-1]
        r = rng.random()
        if beats(player, ai):
            return player if r < stay else rng.randrange(3)
        if beats(ai, player):
            return (ai + 1) % 3 if r < shift else rng.randrange(3)
        return (player + 1) % 3 if r < 0.2 else rng.randrange(3)

    return move


def pretend_games(n: int, seed: int, rounds: int = 10) -> list[Game]:
    """n games against an opponent that throws at random (like the untrained AI)."""
    rng = random.Random(seed)
    games = []
    for _ in range(n):
        player = habit_player(rng)
        game: Game = []
        for _ in range(rounds):
            game.append((player(game), rng.randrange(3)))
        games.append(game)
    return games

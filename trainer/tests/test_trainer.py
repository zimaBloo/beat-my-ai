import json
import math
from pathlib import Path

from rps.data import examples, load_games, parse_game, split_by_time
from rps.evaluate import evaluate, wilson
from rps.features import features
from rps.model import brain_predict, export_brain, predict, train
from rps.simulate import pretend_games

SHARED = Path(__file__).resolve().parents[2] / "shared"


def test_features_match_the_shared_examples():
    cases = json.loads((SHARED / "feature_cases.json").read_text())
    assert len(cases) > 10
    for case in cases:
        assert features([tuple(r) for r in case["history"]]) == case["features"]


def test_games_file_is_read_and_bad_lines_are_refused(tmp_path):
    f = tmp_path / "games.jsonl"
    f.write_text('{"moves": "RPS", "ai": "PPS"}\n\n{"moves": "SS", "ai": "RR"}\n')
    assert load_games(f) == [[(0, 1), (1, 1), (2, 2)], [(2, 0), (2, 0)]]
    assert load_games(tmp_path / "missing.jsonl") == []
    for moves, ai in (("RPX", "RPS"), ("RP", "RPS"), ("", "")):
        try:
            parse_game(moves, ai)
            assert False, "should have been refused"
        except ValueError:
            pass


def test_every_round_becomes_one_lesson():
    rows = examples([[(0, 1), (2, 2)]])
    assert rows == [([3, 7, 11, 15], 0), ([0, 5, 11, 13], 2)]


def test_newest_games_are_kept_for_testing():
    games = pretend_games(10, seed=1)
    older, newest = split_by_time(games)
    assert older == games[:8] and newest == games[8:]
    assert split_by_time(games[:3]) == (games[:3], [])


def test_the_ai_learns_habits_and_beats_guessing_on_new_players():
    older, newest = pretend_games(400, seed=3), pretend_games(150, seed=4)
    report = evaluate(train(examples(older)), older, newest)
    assert report["test_moves"] == 1500
    assert report["ai"]["accuracy"] > 0.38, report["ai"]                 # guessing gets 0.333
    assert report["ai"]["low"] > 1 / 3, "even the cautious end of the range beats guessing"
    assert report["ai"]["log_loss"] < math.log(3)
    assert report["ai"]["accuracy"] >= report["most_common_move"]["accuracy"]


def test_no_games_gives_an_untrained_brain_and_an_honest_report():
    brain = export_brain(train([]), trained_on=0)
    assert brain["version"] == "untrained" and brain["trainedOn"] == 0
    report = evaluate(train([]), [], [])
    assert report["test_moves"] == 0 and "note" in report


def test_same_games_give_the_same_brain():
    rows = examples(pretend_games(40, seed=5))
    a, b = export_brain(train(rows), len(rows)), export_brain(train(rows), len(rows))
    assert a == b and len(a["version"]) == 8
    assert [len(layer["weights"]) for layer in a["layers"]] == [16, 12]
    assert [len(layer["bias"]) for layer in a["layers"]] == [12, 3]


def test_saved_brain_predicts_like_the_trained_network():
    rows = examples(pretend_games(40, seed=6))
    model = train(rows)
    brain = export_brain(model, len(rows))
    torch_probs = predict(model, rows[:25])
    for i, (indices, _move) in enumerate(rows[:25]):
        for a, b in zip(brain_predict(brain, indices), torch_probs[i].tolist()):
            assert abs(a - b) < 1e-4            # the saved numbers are rounded to 6 decimals


def test_range_is_wide_for_few_tries_and_narrow_for_many():
    low, high = wilson(4, 10)
    assert high - low > 0.4
    low, high = wilson(400, 1000)
    assert high - low < 0.07 and low < 0.4 < high

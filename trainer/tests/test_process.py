import json
from datetime import datetime, timezone
from pathlib import Path

from rps.process import DAILY_LIMIT, process
from rps.records import load_records

SHARED = Path(__file__).resolve().parents[2] / "shared"
FACTS = json.loads((SHARED / "record_example.json").read_text())["facts"]
NOON = datetime(2026, 11, 22, 12, 0, 0, tzinfo=timezone.utc)


def game(i: int) -> dict:
    """A different valid game each time (the seed differs; the score stays consistent with the moves)."""
    return {"ok": True, "showName": False, "facts": {**FACTS, "seed": f"{i:08x}"}}


def run(tmp_path, check, issue=1, user_id=583231, login="octocat", now=NOON):
    return process(check, tmp_path, issue=issue, user_id=user_id, login=login, salt="test-salt", now=now)


def test_a_good_game_is_stored_and_everything_is_rebuilt(tmp_path):
    status, reply = run(tmp_path, game(1))
    assert status == "stored" and "Game 1 is in" in reply and "@octocat" in reply and "not shown" in reply
    assert len(load_records(tmp_path / "games.jsonl")) == 1
    brain = json.loads((tmp_path / "brain.json").read_text())
    assert brain["trainedOn"] == 10 and (tmp_path / "brains" / f"{brain['version']}.json").exists()
    assert json.loads((tmp_path / "stats.json").read_text())["games"] == 1
    assert json.loads((tmp_path / "report.json").read_text())["brain"] == brain["version"]


def test_a_refused_game_changes_nothing(tmp_path):
    status, reply = run(tmp_path, {"ok": False, "reason": "no game found in the form"})
    assert status == "refused" and "no game found" in reply
    assert not (tmp_path / "games.jsonl").exists() and not (tmp_path / "brain.json").exists()


def test_the_same_game_counts_once(tmp_path):
    assert run(tmp_path, game(1), issue=1)[0] == "stored"
    assert run(tmp_path, game(1), issue=1)[0] == "already"                     # the job ran twice on one form
    status, reply = run(tmp_path, game(1), issue=2, user_id=7, login="mona")    # someone resends the same game
    assert status == "refused" and "already been counted" in reply
    assert len(load_records(tmp_path / "games.jsonl")) == 1


def test_one_person_cannot_flood_the_data(tmp_path):
    for i in range(DAILY_LIMIT):
        assert run(tmp_path, game(i), issue=i + 1)[0] == "stored"
    status, reply = run(tmp_path, game(99), issue=50)
    assert status == "refused" and "limit" in reply
    assert run(tmp_path, game(100), issue=51, user_id=7, login="mona")[0] == "stored"       # another person still can
    tomorrow = datetime(2026, 11, 23, 0, 5, 0, tzinfo=timezone.utc)
    assert run(tmp_path, game(101), issue=52, now=tomorrow)[0] == "stored"                  # and so can they, the next day


def test_the_name_appears_only_with_a_yes(tmp_path):
    _, reply = run(tmp_path, {**game(1), "showName": True})
    assert "is shown on the profile" in reply and load_records(tmp_path / "games.jsonl")[0]["name"] == "octocat"


def test_ranking_appears_after_five_games(tmp_path):
    replies = [run(tmp_path, game(i), issue=i + 1, user_id=100 + i, login=f"p{i}")[1] for i in range(5)]
    assert "better than" not in replies[3] and "better than" in replies[4]

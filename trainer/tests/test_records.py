import json
from pathlib import Path

import pytest

from rps.data import examples, load_games
from rps.model import export_brain, save_brain, train
from rps.records import add_record, load_records, player_key, validate
from rps.stats import percentile, rebuild

SHARED = Path(__file__).resolve().parents[2] / "shared"
FACTS = json.loads((SHARED / "record_example.json").read_text())["facts"]
WHO = dict(user_id=583231, login="octocat", salt="test-salt")


def add(path, issue=1, show_name=False, facts=None, **who):
    facts = facts or {**FACTS, "seed": f"{issue:08x}"}          # a different game per form, since a game counts once
    return add_record(path, facts, issue=issue, show_name=show_name, at="2026-11-22T10:15:00Z", **{**WHO, **who})


def test_a_game_is_stored_with_everything_needed_to_replay_it(tmp_path):
    f = tmp_path / "games.jsonl"
    r = add(f, facts=FACTS)
    assert r["n"] == 1 and r["moves"] == FACTS["moves"] and r["ai"] == FACTS["ai"] and r["seed"] == FACTS["seed"]
    assert r["brain"] == FACTS["brain"] and r["score"] == FACTS["score"] and r["at"] == "2026-11-22T10:15:00Z"
    assert r["client"] == FACTS["client"] and len(r["client"]["think_ms"]) == r["rounds"]      # thinking time per move is kept
    assert add(tmp_path / "bare.jsonl", facts={**FACTS, "client": None})["client"] is None      # and is optional
    assert load_records(f) == [r]
    assert load_games(f) == [[("RPS".index(m), "RPS".index(a)) for m, a in zip(r["moves"], r["ai"])]]   # the trainer reads the same file


def test_names_are_stored_only_with_consent(tmp_path):
    f = tmp_path / "games.jsonl"
    hidden, shown = add(f, issue=1), add(f, issue=2, show_name=True)
    assert hidden["name"] is None and shown["name"] == "octocat"
    assert "octocat" not in f.read_text().splitlines()[0]
    assert hidden["player"] == shown["player"]                      # same person, same scrambled number
    assert add(f, issue=3, user_id=99)["player"] != hidden["player"]
    assert player_key(583231, "another-salt") != hidden["player"]   # useless without the secret salt
    with pytest.raises(ValueError):
        player_key(583231, "")


def test_the_same_submission_is_never_counted_twice(tmp_path):
    f = tmp_path / "games.jsonl"
    assert add(f, issue=7) is not None
    assert add(f, issue=7) is None
    with pytest.raises(ValueError, match="already been counted"):
        add(f, issue=8, facts={**FACTS, "seed": f"{7:08x}"})       # the same game sent again through another form
    assert len(load_records(f)) == 1


def test_earlier_records_are_never_rewritten(tmp_path):
    f = tmp_path / "games.jsonl"
    add(f, issue=1)
    before = f.read_text()
    add(f, issue=2, show_name=True)
    assert f.read_text().startswith(before) and [r["n"] for r in load_records(f)] == [1, 2]


def test_broken_or_tampered_records_are_refused(tmp_path):
    good = add(tmp_path / "g.jsonl")
    for change in ({"score": {"player": 10, "ai": 0, "ties": 0}}, {"moves": "RPS"}, {"ai": good["ai"].lower()},
                   {"seed": "xyz"}, {"name": "<script>"}, {"player": "octocat"}, {"at": "yesterday"}, {"v": 2},
                   {"client": {**good["client"], "think_ms": [1, 2, 3]}}, {"client": {**good["client"], "input": "mind"}},
                   {"client": {**good["client"], "page": "<b>"}}, {"client": {"think_ms": good["client"]["think_ms"]}}):
        with pytest.raises(ValueError):
            validate({**good, **change})
    with pytest.raises(ValueError):
        validate({**good, "extra": 1})
    f = tmp_path / "gap.jsonl"
    f.write_text(json.dumps({**good, "n": 5}) + "\n")
    with pytest.raises(ValueError):
        load_records(f)


def test_statistics_are_rebuilt_from_the_stored_games(tmp_path):
    f = tmp_path / "games.jsonl"
    assert rebuild([])["games"] == 0 and rebuild([])["last"] is None
    add(f, issue=1); add(f, issue=2, show_name=True, user_id=7, login="mona")
    stats = rebuild(load_records(f))
    assert stats["games"] == 2 and stats["moves"] == 20 and stats["players"] == 2
    assert stats["humans_won"] + stats["ai_won"] + stats["draws"] == 2
    assert sum(stats["opening"].values()) == 2 and stats["opening"]["rock"] == 2      # both games open with R
    assert stats["last"]["name"] == "mona" and len(stats["ai_round_win_rate"]) == 2
    assert stats["median_think_ms"] == 822 and rebuild([])["median_think_ms"] is None
    assert stats == rebuild(load_records(f))                                            # same games, same numbers


def test_percentile_tells_a_player_where_they_stand():
    margins = [-4, -2, -2, 0, 1, 3]
    assert percentile(margins, 3) == pytest.approx(91.7)      # better than five of six, level with itself
    assert percentile(margins, -4) == pytest.approx(8.3)
    assert percentile(margins, -2) == pytest.approx(33.3)
    assert percentile([], 2) is None


def test_every_brain_version_is_kept(tmp_path):
    rows = examples([[(0, 1), (2, 2), (1, 0)]] * 5)
    brain = export_brain(train(rows), len(rows))
    save_brain(brain, tmp_path / "brain.json", tmp_path / "brains")
    assert json.loads((tmp_path / "brains" / f"{brain['version']}.json").read_text()) == brain
    assert json.loads((tmp_path / "brain.json").read_text()) == brain

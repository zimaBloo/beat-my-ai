import xml.etree.ElementTree as ET

from rps.scoreboard import lines_for, scoreboard, write_all
from rps.stats import rebuild

EMPTY = rebuild([])


def stats(**change):
    base = {**EMPTY, "games": 16, "moves": 160, "players": 12, "humans_won": 7, "ai_won": 8, "draws": 1,
            "opening": {"rock": 7, "paper": 5, "scissors": 4}, "ai_round_win_rate": [0.5, 0.48, 0.52, 0.55, 0.53, 0.57, 0.58, 0.6],
            "last": {"name": None, "score": {"player": 4, "ai": 5, "ties": 1}, "at": "2026-11-22T10:15:00Z"}}
    return {**base, **change}


def test_before_anyone_has_played_it_says_so():
    svg = scoreboard(EMPTY, "dark")
    assert "Nobody has played yet. Be the first." in svg and ">0</text>" in svg
    assert "rounds the AI wins" not in svg                       # no line chart without games
    ET.fromstring(svg)                                            # a valid picture


def test_the_numbers_and_sentences_come_from_the_statistics():
    svg = scoreboard(stats(), "light")
    assert ">7</text>" in svg and ">8</text>" in svg
    assert "The AI has studied 160 moves from 16 games." in svg
    assert "What it noticed: 44% of people open with rock." in svg
    assert "rounds the AI wins" in svg and "60%" in svg
    ET.fromstring(svg)


def test_one_game_is_written_in_the_singular():
    assert lines_for(stats(games=1, moves=10))[0] == "The AI has studied 10 moves from 1 game."


def test_a_name_appears_only_when_the_record_has_one():
    few = dict(games=2, moves=20)
    assert not any("@" in line for line in lines_for(stats(**few)))
    shown = stats(**few, last={"name": "mona", "score": {"player": 4, "ai": 5, "ties": 1}, "at": "2026-11-22T10:15:00Z"})
    assert "Latest player: @mona" in lines_for(shown)


def test_both_themes_and_the_button_are_written(tmp_path):
    files = write_all(stats(), tmp_path)
    assert sorted(f.name for f in files) == ["play-dark.svg", "play-light.svg", "scoreboard-dark.svg", "scoreboard-light.svg"]
    for f in files:
        ET.parse(f)
    assert (tmp_path / "scoreboard-dark.svg").read_text() != (tmp_path / "scoreboard-light.svg").read_text()

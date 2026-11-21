"""Step 2 of the automatic job: store a checked game, retrain the AI, rebuild the statistics, write the reply.

    python -m rps.process --check check.json --data ../data --issue 31 --user-id 583231 --login octocat --reply reply.md

`check.json` is what engine/scripts/check-game.ts printed. The secret salt comes from the PLAYER_SALT environment variable.
Whatever happens, a reply for the player is written. The data only changes when a game is really stored.
"""
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .data import examples, load_games, split_by_time
from .evaluate import evaluate
from .model import export_brain, save_brain, train
from .records import add_record, games_today, load_records, player_key
from .stats import margin, percentile, rebuild

DAILY_LIMIT = 5          # games one person can add per day
GAME_URL = os.environ.get("GAME_URL", "")


def process(check: dict, data: Path, *, issue: int, user_id: int, login: str, salt: str, now: datetime | None = None) -> tuple[str, str]:
    """Returns (status, reply). Status is "stored", "refused" or "already"."""
    now = now or datetime.now(timezone.utc)
    again = f"\n\n[Play again]({GAME_URL})" if GAME_URL else ""
    if not check.get("ok"):
        return "refused", f"Sorry @{login}, I could not count this one: {check.get('reason', 'the game could not be read')}.{again}"
    games_file = data / "games.jsonl"
    records = load_records(games_file)
    key = player_key(user_id, salt)
    if games_today(records, key, now.strftime("%Y-%m-%d")) >= DAILY_LIMIT:
        return "refused", f"Thanks @{login}! You have reached today's limit of {DAILY_LIMIT} games, so this one is not counted. Come back tomorrow."
    try:
        record = add_record(games_file, check["facts"], issue=issue, user_id=user_id, login=login,
                            show_name=bool(check.get("showName")), salt=salt, at=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    except ValueError as e:
        return "refused", f"Sorry @{login}, I could not count this one: {e}.{again}"
    if record is None:
        return "already", f"This game is already counted, @{login}."

    # retrain on everything, measure on the newest games, rebuild every number shown
    games = load_games(games_file)
    older, newest = split_by_time(games)
    report = evaluate(train(examples(older)), older, newest)
    rows = examples(games)
    brain = export_brain(train(rows), trained_on=len(rows))
    save_brain(brain, data / "brain.json", data / "brains")
    report.update({"games": len(games), "moves": len(rows), "brain": brain["version"]})
    (data / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    stats = rebuild(load_records(games_file))
    (data / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")

    s = record["score"]
    result = (f"You beat the AI {s['player']} to {s['ai']}" if s["player"] > s["ai"]
              else f"The AI beat you {s['ai']} to {s['player']}" if s["ai"] > s["player"] else f"A draw, {s['player']} all")
    rank = percentile(stats["margins"], margin(record))
    standing = f" That is better than {round(rank)}% of all games so far." if stats["games"] >= 5 and rank is not None else ""
    learned = "the first game" if stats["games"] == 1 else f"all {stats['games']} games"
    name = "Your name is shown on the profile." if record["name"] else "Your name is not shown on the profile."
    reply = (f"Thanks @{login}! Game {record['n']} is in. {result}.{standing}\n\n"
             f"The AI has just relearned from {learned} ({stats['moves']} moves). {name}{again}")
    return "stored", reply


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--user-id", type=int, required=True)
    ap.add_argument("--login", required=True)
    ap.add_argument("--reply", required=True)
    args = ap.parse_args()
    try:
        check = json.loads(Path(args.check).read_text())
    except (OSError, ValueError):
        check = {"ok": False, "reason": "the game could not be read"}
    status, reply = process(check, Path(args.data), issue=args.issue, user_id=args.user_id, login=args.login,
                            salt=os.environ.get("PLAYER_SALT", ""))
    Path(args.reply).write_text(reply + "\n")
    print(status)                                    # the job reads this word to decide whether to save and publish


if __name__ == "__main__":
    main()

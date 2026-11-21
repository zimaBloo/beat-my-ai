"""Safe storage of every game: data/games.jsonl, one game per line, oldest first.

Rules of this file:
- Records are only ever ADDED. Nothing is edited or removed, and git keeps every past state.
- Each record holds the raw facts of the game, enough to replay it exactly against its archived brain.
  Scores, statistics and anything shown on the profile are worked out from these records and can be rebuilt at any time.
- No names unless the player ticked the box. `player` is a scrambled number: the same person always gets
  the same one, but it cannot be turned back into a name without the secret salt.

A record:
  {"v": 1, "n": 12, "at": "2026-11-22T10:15:00Z", "issue": 31, "engine": 1, "brain": "c6d4120b", "seed": "7f3a9c02",
   "rounds": 10, "moves": "RPSSRPRPSR", "ai": "SPRSPRSSRS", "score": {"player": 4, "ai": 4, "ties": 2},
   "client": {"think_ms": [1840, 912, ...], "input": "touch", "nth": 2, "page": "1"},
   "player": "p3f9a2c1b7d", "name": null}

`client` is what the game page reported about how the game was played: thinking time before each move,
how the moves were entered, which game it was in that browser, and the page version. It cannot be checked,
so it is kept for later study and nothing depends on it. It is null when the page sent nothing.

    python -m rps.records add --games ../data/games.jsonl --facts facts.json --issue 31 --user-id 583231 --login octocat [--show-name]
"""
import argparse
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .features import MOVE_LETTERS, beats

FIELDS = ("v", "n", "at", "issue", "engine", "brain", "seed", "rounds", "moves", "ai", "score", "client", "player", "name")
CLIENT_FIELDS = ("think_ms", "input", "nth", "page")


def player_key(user_id: int, salt: str) -> str:
    """The scrambled player number. Same person and salt give the same key; the key reveals nothing about the person."""
    if not salt:
        raise ValueError("a secret salt is required")
    return "p" + hmac.new(salt.encode(), str(int(user_id)).encode(), hashlib.sha256).hexdigest()[:10]


def score_of(moves: str, ai: str) -> dict:
    s = {"player": 0, "ai": 0, "ties": 0}
    for m, a in zip(moves, ai):
        p, q = MOVE_LETTERS.index(m), MOVE_LETTERS.index(a)
        s["player" if beats(p, q) else "ai" if beats(q, p) else "ties"] += 1
    return s


def validate(r: dict) -> None:
    """Raises ValueError with a plain reason if a record is not exactly right."""
    if tuple(r) != FIELDS:
        raise ValueError(f"fields must be exactly {FIELDS}, got {tuple(r)}")
    if r["v"] != 1:
        raise ValueError("unknown record version")
    if not (isinstance(r["n"], int) and r["n"] >= 1 and isinstance(r["issue"], int) and r["issue"] >= 1):
        raise ValueError("n and issue must be positive whole numbers")
    datetime.strptime(r["at"], "%Y-%m-%dT%H:%M:%SZ")
    if not (isinstance(r["engine"], int) and re.fullmatch(r"[a-z0-9]{1,16}", r["brain"]) and re.fullmatch(r"[0-9a-f]{8}", r["seed"])):
        raise ValueError("bad engine, brain or seed")
    for key in ("moves", "ai"):
        if not re.fullmatch(r"[RPS]+", r[key]) or len(r[key]) != r["rounds"]:
            raise ValueError(f"{key} must be {r['rounds']} letters of R, P, S")
    if r["score"] != score_of(r["moves"], r["ai"]):
        raise ValueError("the score does not match the moves")
    c = r["client"]
    if c is not None:
        if not isinstance(c, dict) or tuple(c) != CLIENT_FIELDS:
            raise ValueError(f"client must be null or have exactly {CLIENT_FIELDS}")
        times = c["think_ms"]
        if not (isinstance(times, list) and len(times) == r["rounds"] and all(type(t) is int and 0 <= t <= 999999 for t in times)):
            raise ValueError("think_ms must be one whole number of milliseconds per round")
        if c["input"] not in ("mouse", "touch", "key") or not (type(c["nth"]) is int and 1 <= c["nth"] <= 9999):
            raise ValueError("bad input or nth")
        if not (isinstance(c["page"], str) and re.fullmatch(r"[a-z0-9.]{1,12}", c["page"])):
            raise ValueError("bad page version")
    if not re.fullmatch(r"p[0-9a-f]{10}", r["player"]):
        raise ValueError("bad player key")
    if r["name"] is not None and not re.fullmatch(r"[A-Za-z0-9-]{1,39}", r["name"]):
        raise ValueError("bad name")


def load_records(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    records = [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    for i, r in enumerate(records, start=1):
        validate(r)
        if r["n"] != i:
            raise ValueError(f"record numbers must run 1, 2, 3, …; line {i} has n={r['n']}")
    return records


def add_record(path: str | Path, facts: dict, *, issue: int, user_id: int, login: str, show_name: bool,
               salt: str, at: str | None = None) -> dict | None:
    """Adds one game to the end of the file. Returns the stored record, or None if this submission is already stored."""
    records = load_records(path)
    if any(r["issue"] == issue for r in records):
        return None                                   # running the job twice must not count a game twice
    record = {
        "v": 1, "n": len(records) + 1,
        "at": at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue": issue, "engine": facts["engine"], "brain": facts["brain"], "seed": facts["seed"],
        "rounds": facts["rounds"], "moves": facts["moves"], "ai": facts["ai"], "score": facts["score"],
        "client": facts.get("client"),
        "player": player_key(user_id, salt), "name": login if show_name else None,
    }
    validate(record)
    with open(path, "a") as f:                         # append only: earlier lines are never rewritten
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    return record


def main() -> None:
    ap = argparse.ArgumentParser(description="Add one checked game to the games file.")
    ap.add_argument("command", choices=["add"])
    ap.add_argument("--games", required=True)
    ap.add_argument("--facts", required=True, help="JSON file written by the engine after replaying the game")
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--user-id", type=int, required=True)
    ap.add_argument("--login", required=True)
    ap.add_argument("--show-name", action="store_true")
    args = ap.parse_args()
    facts = json.loads(Path(args.facts).read_text())
    record = add_record(args.games, facts, issue=args.issue, user_id=args.user_id, login=args.login,
                        show_name=args.show_name, salt=os.environ.get("PLAYER_SALT", ""))
    print("already stored" if record is None else f"stored game {record['n']}")


if __name__ == "__main__":
    main()

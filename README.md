# beat-my-ai

Rock-paper-scissors against a small AI that learns from the people who play it.

Work in progress. This repo will hold the game, the AI's training code and the art for my GitHub profile.

## What is here so far

- `art/` builds the animated gloves. Everything is made by script in Blender, no manual modelling.
  - `glove.py`: the gloved hand, posed by joint angles (rock, paper, scissors).
  - `animate.py`: the loop. Two gloves shake, throw and react, timed like an old cartoon.
  - `assemble.py`: draws the overlay layers (winner burst, YOU / AI labels) and builds the final animation.
- `engine/` is the game itself: the rules, what the AI looks at, how it picks a move, and a way to replay any game from the player's moves alone. That replay is how a submitted score gets checked. Run the tests with `cd engine && npm install && npm test`.
- `trainer/` teaches the AI. It reads the collected games, trains a small neural network with PyTorch, measures it on the newest games it has not seen, and saves the brain for the engine. Run the tests with `cd trainer && python -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m pytest`.
- `shared/` holds examples that both the trainer and the engine are tested against, so the two always compute the same thing.
- `data/` is the memory of the project. `games.jsonl` keeps every game ever played, one per line, with everything needed to replay it. Records are only added, never changed. `brains/` keeps every version of the AI. `stats.json` and `report.json` are worked out from the games and can be rebuilt at any time. Empty for now: nobody has played yet.
- `media/rps-loop.webp`: the finished loop.
- `hooks/pre-commit`: blocks a commit with the wrong author email or a `.env` file.

## Rebuild the loop

Needs Blender and Python with Pillow.

```
blender -b -P art/animate.py -- art
python3 art/assemble.py art media
```

The first step renders the 3D frames (about 9 minutes). The second takes seconds, so changing a label or the burst does not need a new render.

## After cloning

```
git config core.hooksPath hooks
```

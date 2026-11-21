# beat-my-ai

Rock-paper-scissors against a small AI that learns from the people who play it.

Work in progress. This repo will hold the game, the AI's training code and the art for my GitHub profile.

## What is here so far

- `art/` builds the animated gloves. Everything is made by script in Blender, no manual modelling.
  - `glove.py`: the gloved hand, posed by joint angles (rock, paper, scissors).
  - `animate.py`: the loop. Two gloves shake, throw and react, timed like an old cartoon.
  - `assemble.py`: draws the overlay layers (winner burst, YOU / AI labels) and builds the final animation.
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

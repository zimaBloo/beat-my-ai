"""Writes the files that prove the Python trainer and the TypeScript engine agree.

    python -m rps.make_parity ../shared

- shared/feature_cases.json: game histories and the inputs both sides must derive from them.
- shared/parity/brain.json + cases.json: a small trained brain and the exact predictions it must give.
The engine's tests read these files. Re-run this only if the features or the brain format change.
"""
import json
import random
import sys
from pathlib import Path

from .data import examples
from .features import features
from .model import brain_predict, export_brain, save_brain, train
from .simulate import pretend_games


def main(shared: str) -> None:
    out = Path(shared)
    (out / "parity").mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    histories = [[]] + [[(rng.randrange(3), rng.randrange(3)) for _ in range(n)] for n in (1, 1, 2, 2, 3, 5, 9) for _ in range(3)]
    cases = [{"history": [list(r) for r in h], "features": features(h)} for h in histories]
    (out / "feature_cases.json").write_text(json.dumps(cases, indent=1) + "\n")
    rows = examples(pretend_games(60, seed=2))
    brain = export_brain(train(rows), trained_on=len(rows))
    save_brain(brain, out / "parity" / "brain.json")
    parity = [{"history": c["history"], "expected": brain_predict(brain, c["features"])} for c in cases]
    (out / "parity" / "cases.json").write_text(json.dumps(parity, indent=1) + "\n")
    print(len(cases), "cases, brain", brain["version"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../shared")

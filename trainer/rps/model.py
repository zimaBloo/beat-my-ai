"""The AI's brain: a small neural network, its training, and saving it for the game engine."""
import hashlib
import json
import math
from pathlib import Path

import torch
from torch import nn

from .data import Example
from .features import INPUT_SIZE

HIDDEN = 12
STEPS = 300
LEARNING_RATE = 0.01
WEIGHT_DECAY = 1e-3          # keeps the network modest when there is little data
SEED = 0


def new_model() -> nn.Sequential:
    return nn.Sequential(nn.Linear(INPUT_SIZE, HIDDEN), nn.Tanh(), nn.Linear(HIDDEN, 3))


def to_tensors(rows: list[Example]) -> tuple[torch.Tensor, torch.Tensor]:
    x = torch.zeros(len(rows), INPUT_SIZE)
    for i, (indices, _move) in enumerate(rows):
        x[i, indices] = 1.0
    y = torch.tensor([move for _indices, move in rows], dtype=torch.long)
    return x, y


def train(rows: list[Example]) -> nn.Sequential:
    """Trains from scratch on all the lessons. Same data in, same brain out."""
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)
    model = new_model()
    if not rows:
        return model
    x, y = to_tensors(rows)
    optimiser = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(STEPS):
        optimiser.zero_grad()
        loss_fn(model(x), y).backward()
        optimiser.step()
    return model


def predict(model: nn.Sequential, rows: list[Example]) -> torch.Tensor:
    """Probabilities for rock, paper, scissors for each lesson."""
    x, _ = to_tensors(rows)
    with torch.no_grad():
        return torch.softmax(model(x), dim=1)


def export_brain(model: nn.Sequential, trained_on: int) -> dict:
    """The brain as plain numbers, in the format engine/src/brain.ts reads."""
    layers = []
    for module in model:
        if isinstance(module, nn.Linear):
            weights = [[round(v, 6) for v in row] for row in module.weight.detach().T.tolist()]   # weights[input][output]
            layers.append({"weights": weights, "bias": [round(v, 6) for v in module.bias.detach().tolist()]})
    digest = hashlib.sha256(json.dumps(layers, separators=(",", ":")).encode()).hexdigest()[:8]
    return {"version": digest if trained_on else "untrained", "trainedOn": trained_on, "layers": layers}


def save_brain(brain: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(brain, separators=(",", ":")) + "\n")


def brain_predict(brain: dict, indices: list[int]) -> list[float]:
    """The same arithmetic the game engine does, in plain Python. Used to prove both sides agree."""
    first = brain["layers"][0]
    values = list(first["bias"])
    for i in indices:
        values = [v + w for v, w in zip(values, first["weights"][i])]
    for layer in brain["layers"][1:]:
        inputs = [math.tanh(v) for v in values]
        values = list(layer["bias"])
        for a, row in zip(inputs, layer["weights"]):
            values = [v + a * w for v, w in zip(values, row)]
    top = max(values)
    exp = [math.exp(v - top) for v in values]
    return [e / sum(exp) for e in exp]

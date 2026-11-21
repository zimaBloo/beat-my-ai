"""Draws the pictures the GitHub profile shows: the scoreboard and the Play button.

    python -m rps.scoreboard --stats ../data/stats.json --out ../media

Makes scoreboard-dark.svg and scoreboard-light.svg (one per GitHub theme) and play-dark.svg / play-light.svg.
The automatic job runs this after every game, so the profile always shows the current numbers.
Everything is drawn from data/stats.json. The pictures use the reader's own system font, so they need no font files.
"""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

W, H = 1200, 400
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(bg="#060a13", panel="#0b1b36", ink="#eef2fa", muted="#9aa8c2", ai="#96beff", line="#4f8cff", rule="#18346a", button="#2a66e0", on_button="#ffffff"),
    "light": dict(bg="#f3f6fb", panel="#e3eaf5", ink="#0b1b36", muted="#4b5d7a", ai="#1d4fc4", line="#2a66e0", rule="#b9c7dc", button="#2a66e0", on_button="#ffffff"),
}


def _plural(n: int, word: str) -> str:
    return f"{n:,} {word}" + ("" if n == 1 else "s")


def lines_for(stats: dict) -> list[str]:
    """The one or two sentences under the score."""
    if stats["games"] == 0:
        return ["Nobody has played yet. Be the first."]
    out = [f"The AI has studied {_plural(stats['moves'], 'move')} from {_plural(stats['games'], 'game')}."]
    if stats["games"] >= 5:
        rock = round(100 * stats["opening"]["rock"] / stats["games"])
        out.append(f"What it noticed: {rock}% of people open with rock.")
    elif stats["last"] and stats["last"]["name"]:
        out.append(f"Latest player: @{stats['last']['name']}")
    return out


def scoreboard(stats: dict, theme: str) -> str:
    c = THEMES[theme]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d" font-family="{FONT}">',
         f'<title id="t">Scoreboard: humans {stats["humans_won"]}, the AI {stats["ai_won"]}</title>',
         f'<desc id="d">{escape(" ".join(lines_for(stats)))}</desc>',
         f'<rect width="{W}" height="{H}" rx="28" fill="{c["bg"]}"/>']
    # the score
    o.append(f'<text x="64" y="84" font-size="34" fill="{c["muted"]}">humans won</text>')
    o.append(f'<text x="64" y="224" font-size="150" font-weight="800" letter-spacing="-5" fill="{c["ink"]}">{stats["humans_won"]}</text>')
    o.append(f'<text x="400" y="84" font-size="34" fill="{c["muted"]}">the AI won</text>')
    o.append(f'<text x="400" y="224" font-size="150" font-weight="800" letter-spacing="-5" fill="{c["ai"]}">{stats["ai_won"]}</text>')
    # how often the AI wins a round, over time (appears once there is something to show)
    rate = stats["ai_round_win_rate"]
    if len(rate) >= 8:
        x0, x1, top, bottom = 760, 1050, 104, 214
        y = lambda v: bottom - (min(0.8, max(0.3, v)) - 0.3) / 0.5 * (bottom - top)
        pts = " ".join(f"{x0 + (x1 - x0) * i / (len(rate) - 1):.1f},{y(v):.1f}" for i, v in enumerate(rate))
        o.append(f'<text x="{x0}" y="84" font-size="34" fill="{c["muted"]}">rounds the AI wins</text>')
        o.append(f'<line x1="{x0}" x2="{x1}" y1="{y(0.5):.1f}" y2="{y(0.5):.1f}" stroke="{c["rule"]}" stroke-width="3" stroke-dasharray="8 8"/>')
        o.append(f'<polyline points="{pts}" fill="none" stroke="{c["line"]}" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>')
        o.append(f'<circle cx="{x1}" cy="{y(rate[-1]):.1f}" r="9" fill="{c["ai"]}"/>')
        o.append(f'<text x="{x1 + 22}" y="{y(rate[-1]) + 12:.1f}" font-size="34" font-weight="700" fill="{c["ink"]}">{round(rate[-1] * 100)}%</text>')
    # the sentences
    for i, line in enumerate(lines_for(stats)):
        o.append(f'<text x="64" y="{300 + i * 52}" font-size="36" fill="{c["ink"] if i == 0 else c["muted"]}">{escape(line)}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def play_button(theme: str) -> str:
    c = THEMES[theme]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="520" height="120" role="img" aria-label="Play a game" font-family="{FONT}">\n'
            f'<rect width="520" height="120" rx="28" fill="{c["button"]}"/>\n'
            f'<text x="260" y="77" text-anchor="middle" font-size="48" font-weight="800" fill="{c["on_button"]}">Play a game  →</text>\n</svg>\n')


def write_all(stats: dict, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for theme in THEMES:
        for name, svg in ((f"scoreboard-{theme}.svg", scoreboard(stats, theme)), (f"play-{theme}.svg", play_button(theme))):
            (out / name).write_text(svg)
            files.append(out / name)
    return files


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stats", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    files = write_all(json.loads(Path(args.stats).read_text()), Path(args.out))
    print("wrote", ", ".join(f.name for f in files))


if __name__ == "__main__":
    main()

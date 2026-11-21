// Settings of the game page.

/** Version of this page, stored with every game so later analysis knows which page a game was played on. */
export const PAGE_VERSION = "1";

/** The GitHub repository that receives finished games, as "owner/name". Empty until the game goes live. */
export const REPO = "";

/** Drawings per second. Old cartoons were drawn "on twos": 12 a second. */
export const FPS = 12;

/** The link that opens a ready-filled GitHub form for a finished game, or null while sending is switched off. */
export function sendUrl(code: string, extras: string, showName: boolean): string | null {
  if (!REPO) return null;
  const q = new URLSearchParams({ template: "game.yml", title: "I played against the AI", game: code, extras, name: showName ? "Yes, show my name" : "No, keep me anonymous" });
  return `https://github.com/${REPO}/issues/new?${q}`;
}

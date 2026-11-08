# Game catalogue metadata

`tools/build_games_registry.py` validates every game's metadata and builds the
catalogue list; `tools/pack.py` writes that list into the catalogue page
(`games/index.html`) in the packed release. Nothing generated is committed, and
games are never rewritten to register them.

## Authored sources and precedence

Each immediate game directory with `index.html`, `index.source.html`, or `game.json`
is discovered once. Sources, in order of precedence:

1. `game.json`: a JSON object with the fields below. This replaces the metadata
   comment as a whole, rather than merging two authored blocks.
2. Without a sidecar, a `bl-game-meta` comment in `index.source.html`, if that
   authored compiled entrypoint exists.
3. Otherwise, a `bl-game-meta` comment in the standalone `index.html`.

If `index.source.html` exists, its HTML supplies fallback title/description even
when a sidecar overrides its metadata. A sidecar without an authored HTML source
uses slug-based fallbacks. Generated `index.html` is never read for a sidecar game.
`metadata.json` is unrelated and is never read. Dungeon Crawler uses `game.json`;
its legacy source comment remains for compatibility, but the sidecar wins.

```html
<!-- bl-game-meta
title: Neon Drift
emoji: 🚀
order: 70
description: Survive the Neon Drift Zone. Made by <model> in <tool> on <hardware>.
-->
```

Equivalent compiled-game `game.json`:

```json
{
  "title": "Neon Drift",
  "emoji": "🚀",
  "order": 70,
  "description": "Survive the Neon Drift Zone."
}
```

`title`, `emoji`, and `description` are strings. `order` is an integer (an integer
string is accepted for legacy comments). Lower orders appear first; ties sort by
title, then retain sorted directory discovery order. Equal titles/orders across
games are permitted. Paths always derive from the directory name. One more,
optional field, `games-link`, places the game's "← Games" link (below).

Missing or empty fields preserve the initial fallback behavior: title from the
HTML title with the Benson Labs suffix removed, else title-cased slug;
description from its meta description, else `Browser game: <title>.`; emoji `🎮`;
order `999`. Missing comments are allowed with a notice. Unknown fields/lines,
duplicate comment blocks or field names, malformed JSON/comments, non-string
text fields, null values in JSON, and non-integer orders fail validation. An
ignored legacy source comment is still checked for malformed/duplicate syntax.

## Meta description

Every published page also needs exactly one `<meta name="description">` in its
`<head>`: search results and link previews show it, and `tools/pack.py` fails
a page without one. Use the first sentence of the card's description (what you
do in the game), without "Made by ...". Write it in the page's own source:
`index.source.html` for a compiled game, otherwise the page itself; nothing
adds it at pack time. Extra pages in a game's folder (other versions) need one
too, and so does the catalogue.

## The "← Games" link

`tools/pack.py` puts a small fixed "← Games" link to `/projects/games/` just
before `</body>` of each game page that doesn't already link there (an `<a>` to
`/projects/games/`, `../` or the full address). It's about 80x28 px, a
translucent dark pill with inline styles and no id or class, 8px from the
top-left corner. An optional field, in the comment or in `game.json`, moves it
for every page of the game (it isn't part of the card): for example
`games-link: bottom-right`, `games-link: top-left 68px` or `games-link: off`.

The value is a corner (`top-left`, `top-right`, `bottom-left`, `bottom-right`),
optionally followed by its distance in px from the top or bottom edge (8px by
default) to clear the game's own controls, or `off` for a game with its own way
back. Pick the spot that covers no controls, score, menus or touch areas at
desktop (1280x800) and phone (390x844) sizes. A page whose Content-Security-Policy
blocks inline styles fails the pack, since the link couldn't be styled.

## Standalone pages

Games are standalone documents with no front matter or shared header. Do not add
snippets, canonical markers, auto-hide scripts, or space for a site menu button.
Game controls, navigation, audio, fullscreen, and saved state remain game-owned.

# Site-integration addendum for game-build prompts

Build a standalone game at `games/<slug>/index.html` (published at
`/projects/games/<slug>/` on bensonlabs.org) with its own complete
HTML document, styles, and scripts. Do not add Jekyll front matter, a site-header
snippet, canonical markers, or navigation auto-hide machinery. No screen corner
is reserved for the website: place game controls where they work best on desktop
and mobile. Preserve game navigation, fullscreen behavior, audio, and saved state.
An optional back-to-games link is allowed. Choose CSP for your actual game assets;
in a `<meta>` CSP leave out `frame-ancestors`: browsers ignore it there and log an
error on every page load.

Author one `bl-game-meta` comment in the head, with `title`, `emoji`, `order: 999`,
and a one-line `description`. When applicable, end the description with
`Made by <model> in <tool> on <hardware>.` Do not guess a curated sort position.
For compiled games use `game.json`, as described in `GAME_METADATA.md`. Keep Vite's
source input and deployed base path; generated HTML is output, not metadata input.

Run `python3 tools/pack.py` to validate the metadata and build the packed site in
`dist/projects/games/`, where the catalogue is generated; nothing generated is
committed. Files a browser never needs (docs, sources, lockfiles) are left out of
a release; list a game's other development files in its `.publishignore`. Keep
each published file under 750 KB and the whole game under 1 MB: size images to
how they're drawn and save pictures as WebP.

The catalogue page (`games/index.html`) is the one page that gets the site
header: the blog wraps it when it assembles bensonlabs.org. Keep it a complete
standalone HTML document, and keep its games-list placeholder.

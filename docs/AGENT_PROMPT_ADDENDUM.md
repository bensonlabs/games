# Site-integration addendum for game-build prompts

Build a standalone game at `games/<slug>/index.html` (published at
`/projects/games/<slug>/` on bensonlabs.org) with its own complete
HTML document, styles, and scripts. Do not add Jekyll front matter, a site-header
snippet, canonical markers, or navigation auto-hide machinery. Place game
controls where they work best on desktop and mobile. Preserve game navigation,
fullscreen behavior, audio, and saved state. The release adds a small
"← Games" link (about 80x28 px, 8px from the top-left corner) to each page
that doesn't link to `/projects/games/` itself: keep that corner free, or name
a free spot with `games-link` in the metadata (`GAME_METADATA.md`). A page can
have its own link to `/projects/games/` instead.

Choose CSP for your actual game assets, and allow inline styles
(`style-src 'unsafe-inline'`) for that link. In a `<meta>` CSP leave out
`frame-ancestors`: browsers ignore it there and log an error on every page load.
Keep the scripts the game needs in its folder, with their license; one too big
to copy is loaded at an exact version (`three@0.160.0`, never `@latest` or an
unversioned URL).

Author one `bl-game-meta` comment in the head, with `title`, `emoji`, `order: 999`,
and a one-line `description`. When applicable, end the description with
`Made by <model> in <tool> on <hardware>.` Do not guess a curated sort position.
Also give the page a `<meta name="description">` with the description's first
sentence, without "Made by ...": every published page needs one.
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

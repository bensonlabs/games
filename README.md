# Games

The games published at [bensonlabs.org/projects/games/](https://bensonlabs.org/projects/games/),
and the catalogue page that lists them.

- **Owns:** every game under `/projects/games/`, and the catalogue. The
  [blog](https://github.com/bensonlabs/blog) owns the rest of bensonlabs.org, including the
  site header.
- **Lifecycle stage:** project. Split out of the blog on 2026-11-07, history included.
- **Guidance:** `CLAUDE.md` (rules for AI agents, from architectureOS),
  `docs/GAME_METADATA.md`, `docs/AGENT_PROMPT_ADDENDUM.md` and `docs/decisions/`.

## How a change reaches the site

By itself, within a few minutes:

1. A push to `main` (adding a game goes straight there) runs the Release workflow: it tests the
   tools, packs every game and compares the pack with the latest release. Packs are reproducible,
   so if nothing the site shows changed, it stops there.
2. Otherwise it publishes the next release (`v1.0.3` -> `v1.0.4`): `games-<version>.tar.gz` and
   its sha256, and asks the blog to publish it.
3. The blog's Update components workflow pins that release in `_data/components.json`, builds the
   whole site with it, runs its page checks and deploys. If a check fails, the site keeps the
   previous release.

The blog unpacks the release into `/projects/games/` and wraps only the catalogue page in the site
header. Game pages are published exactly as packed. Why: `docs/decisions/0002` and `0003`.

## Working on it

- Pack and check everything: `python3 tools/pack.py`
- Preview: `python3 -m http.server -d dist`, then open http://localhost:8000/projects/games/
- Tests: `python3 -m unittest discover -s tools -p 'test_*.py'`
- The dungeon crawler is a Vite and React app in `games/dungeon-crawler/`. `tools/pack.py`
  builds it with npm (Node 22 in CI); its build output is never committed.

## Adding a game

Tell Claude "add this game" with the HTML file (or paste it, or give a link). The `add-game` skill
puts it in `games/<slug>/`, writes its catalogue card (title, emoji, one-line description) and
checks it, then pushes it to `main`. It's on bensonlabs.org a few minutes later.

By hand, from anywhere (GitHub's website works, phone included):

1. Add `games/<slug>/index.html`: one standalone page with no front matter and no site header.
2. For the card, put a `bl-game-meta` comment in its `<head>` (`docs/GAME_METADATA.md`). Without
   one, the card uses the page's `<title>` and its description.
3. Commit it to `main`.

## What a release contains

Everything a browser needs to play each game, and nothing else:

- each game folder, minus Markdown, Rust, TOML, TypeScript, shell scripts, lockfiles, package
  and metadata files, hidden files, and anything listed in the game's `.publishignore`;
- for a game with a `package.json`, only its build output;
- the catalogue, with the games list written in.

No published file may be over 750 KB, and no game over 1 MB in all. Releases are reproducible:
the same files always give the same sha256.

## What the games expect from the site

- They're served at `/projects/games/<slug>/`; the dungeon crawler is built for that path.
- The site provides `/favicon.svg`, which a couple of games use.
- Only `index.html` (the catalogue) gets the site header; every game stays standalone.

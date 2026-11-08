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

1. Changes land on `main` through PRs. CI tests the tools and packs every game.
2. A tag such as `v1.2.0` runs the Release workflow. It packs the games and publishes
   `games-v1.2.0.tar.gz` and its sha256 as a GitHub release.
3. In the blog, `python3 .github/scripts/components.py bump games v1.2.0` pins that release
   (version and sha256) in `_data/components.json`. Merging that PR deploys bensonlabs.org.

The blog unpacks the release into `/projects/games/` and wraps only the catalogue page in
the site header. Game pages are published exactly as packed.

## Working on it

- Pack and check everything: `python3 tools/pack.py`
- Preview: `python3 -m http.server -d dist`, then open http://localhost:8000/projects/games/
- Tests: `python3 -m unittest discover -s tools -p 'test_*.py'`
- The dungeon crawler is a Vite and React app in `games/dungeon-crawler/`. `tools/pack.py`
  builds it with npm (Node 22 in CI); its build output is never committed.

## Adding a game

1. Make a folder `games/<slug>/` with a standalone `index.html`: its own complete document,
   with no front matter and no site header.
2. Describe it in a `bl-game-meta` comment (or a `game.json` for a built game), as
   `docs/GAME_METADATA.md` explains. That's what puts it in the catalogue.
3. Run `python3 tools/pack.py`, preview it, and open a PR.

## What a release contains

Everything a browser needs to play each game, and nothing else:

- each game folder, minus Markdown, Rust, TOML, TypeScript, shell scripts, lockfiles, package
  and metadata files, hidden files, and anything listed in the game's `.publishignore`;
- for a game with a `package.json`, only its build output;
- the catalogue, with the games list written in.

No published file may be over 750 KB. Releases are reproducible: the same files always give
the same sha256.

## What the games expect from the site

- They're served at `/projects/games/<slug>/`; the dungeon crawler is built for that path.
- The site provides `/favicon.svg`, which a couple of games use.
- Only `index.html` (the catalogue) gets the site header; every game stays standalone.

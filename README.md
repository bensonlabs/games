# Projects

Everything published under [bensonlabs.org/projects/](https://bensonlabs.org/projects/): the
Projects page, Games, Workouts, Bootstraps and each project.

- **Owns:** `/projects/` and everything under it. The [blog](https://github.com/bensonlabs/blog)
  owns the rest of bensonlabs.org (posts, About) and the site header.
- **Lifecycle stage:** project. Split out of the blog on 2026-11-07 as bensonlabs/games; everything
  under /projects/ since 2026-11-08, with the workout plans from bensonlabs/workouts. History included.
- **Guidance:** `CLAUDE.md` (rules for AI agents, from architectureOS), `tools/sections.py` (cards),
  `docs/GAME_METADATA.md`, `docs/AGENT_PROMPT_ADDENDUM.md` and `docs/decisions/`.

## Adding something

Tell Claude "add this" with the HTML file (or paste it, or give a link). The `add` skill picks the
section, writes the card, checks it and pushes it to `main`. It's on bensonlabs.org a few minutes
later.

By hand, from anywhere (GitHub's website works, phone included):

1. Add one standalone page (no front matter, no site header) in its section's folder:

   | Section | Folder | Address |
   |---|---|---|
   | Projects | `site/<slug>/index.html` | /projects/<slug>/ |
   | Games | `site/games/<slug>/index.html` | /projects/games/<slug>/ |
   | Workouts | `site/workouts/<slug>/index.html` | /projects/workouts/<slug>/ |
   | Bootstraps | `site/bootstraps/<slug>/index.html` | /projects/bootstraps/<slug>/ |

   A write-up can be an `index.md` with front matter instead. A new section is a folder with a
   `section.json` (title, emoji, description, intro).
2. For its card, put a `bl-card` comment at the top of its `<head>` (title, emoji, order,
   description; the fields are in `tools/sections.py`). Without one, the card uses the page's
   `<title>` and description.
3. Commit it to `main`.

## How a change reaches the site

By itself, within a few minutes:

1. A push to `main` runs the Release workflow: it tests the tools, packs everything and compares
   the pack with the latest release. Packs are reproducible, so if nothing the site shows changed,
   it stops there.
2. Otherwise it publishes the next release (`v1.0.3` -> `v1.0.4`): `projects-<version>.tar.gz` and
   its sha256, and asks the blog to publish it.
3. The blog's Update components workflow pins that release in `_data/components.json`, builds the
   whole site with it, runs its page checks and deploys. If a check fails, the site keeps the
   previous release.

## Working on it

- Pack and check everything: `python3 tools/pack.py`
- Preview: `python3 -m http.server -d dist`, then open http://localhost:8000/projects/ (pages that
  get the site header show without it here; Jekyll adds it on the site).
- Tests: `python3 -m unittest discover -s tools -p 'test_*.py'`
- The dungeon crawler is a Vite and React app in `site/games/dungeon-crawler/`. `tools/pack.py`
  builds it with npm (Node 22 in CI); its build output is never committed.

## What a release contains

- Everything under `site/`, minus what a browser never needs: Markdown (except `index.md` pages,
  which Jekyll renders), Rust, TOML, TypeScript, shell scripts, lockfiles, package, card and
  metadata files, hidden files, and anything a folder's `.publishignore` lists.
- The dungeon crawler's build output.
- Every section page with its cards written in, and the games catalogue with its games list.
- `.components-wrap.json`: the pages the blog wraps in the site header (every standalone page
  except games and cards marked `header: no`).

No published file may be over 750 KB. Releases are reproducible: the same files always give the
same sha256.

## What the pages expect from the site

- They're served under `/projects/`; the dungeon crawler is built for
  `/projects/games/dungeon-crawler/`.
- The site provides `/favicon.svg`, and the `project`, `default` and `post` layouts that pages with
  front matter use.
- Only the pages in `.components-wrap.json` get the site header; games stay standalone.

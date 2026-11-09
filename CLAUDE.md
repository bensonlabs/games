# Games: instructions for AI agents

<!-- Only the governance blocks below come from architectureOS; /sync-governance updates them. Everything outside them belongs to this project and is never changed by a sync. -->

<!-- BEGIN governance:scaffold -->
## How this file works

- **Personal preferences** come from the person's own `~/.claude/CLAUDE.md`, never from this file.
- **Core rules** (the next block) come from the architectureOS repo and are the same in every
  project. To change one, change it there; `/sync-governance` keeps this file in step.
- **Project rules** (at the bottom) belong to this project: what it owns, its commands, what must
  never move, and its own checks. Give a non-obvious one a date and who decided ("owner decision,
  2026-11-07").
- **Apps with users** add the product rules (architectureOS doc `product-rules.md`) to their
  project rules when they reach the "product" stage.
- **Background:** each core rule names a doc in the architectureOS repo (`source_repo` in
  `.governance-sync.json`). It's private; read a doc with
  `gh api repos/<owner>/<repo>/contents/docs/<name>.md -H "Accept: application/vnd.github.raw"`.
<!-- END governance:scaffold -->

<!-- BEGIN governance:core-rules -->
## Core rules

1. **Record decisions that aren't obvious.** A choice someone could reasonably have made the other
   way, or one that's costly to undo, gets `docs/decisions/NNNN-<slug>.md` from `TEMPLATE.md`.
   Reversing one is a new record that supersedes it; the old one gets only a "superseded by" line.
   Doc: `decision-records.md`.
2. **Docs change in the same commit as the code they describe,** so undoing the commit undoes both.
   When code, docs and memory disagree, the source wins (the running system, the spec, the data),
   then the code, then the docs: fix the lower one while you're there.
   Docs: `same-commit.md`, `trust-order.md`.
3. **Report each work state as its own fact:** built, checked (the check ran and passed, and you saw
   it), approved, merged, live. Never infer a later state from an earlier one.
   Doc: `work-states.md`.
4. **Never start or re-run a deploy or CI run without a go for that run.** A go to merge isn't a go
   to start a run. To find out whether something is reachable or allowed, use read-only calls.
   Doc: `conventions.md`.
5. **Secrets and people's data never go in git:** not in code, commits, PRs, issues, logs, test data
   or screenshots. Committed config holds placeholders. If one slips in, tell the person at once.
   Doc: `conventions.md`.
6. **A mistake that happens twice becomes a check that fails.** Mechanical facts (a path exists,
   copies match, a page is published) get a test or CI check, not a reminder. Judgment calls stay
   with people. Doc: `checks-over-reminders.md`.
<!-- END governance:core-rules -->

## Project rules

### About this project

- What it owns: every game published at bensonlabs.org/projects/games/, and the games
  catalogue page there. bensonlabs/projects owns the rest of /projects/. The blog
  (bensonlabs/blog) owns its own pages and the site header it wraps around the catalogue,
  and assembles and deploys the site.
- Lifecycle stage (experiment, project, maintained, product, archived): project. A
  personal games collection with one user; split out of the blog on 2026-11-07.

### Games

| When | Do |
|---|---|
| Adding or changing a game | Use the `add-game` skill; it pushes straight to `main` and the game goes live by itself. Keep it a standalone page in `games/<slug>/`: its own complete HTML document, no front matter, no site header (`bl-nav`). Give it metadata as `docs/GAME_METADATA.md` describes; `docs/AGENT_PROMPT_ADDENDUM.md` is the brief for building one. |
| A game needs a file the site shouldn't publish (dev scripts, sources) | Add a glob to the game's `.publishignore`. Docs, Rust, TOML, TypeScript, shell scripts, lockfiles, package and metadata files are never published anyway. |
| Adding images, sounds or fonts | No published file may be over 750 KB, and no game over 1 MB in all: size images to how they're drawn, and use WebP (or JPEG) for pictures rather than PNG. |
| A game page needs its way back to the catalogue | `tools/pack.py` adds a small "← Games" link in the top-left corner of every game page that doesn't link to `/projects/games/` (owner decision, 2026-11-08). If it covers controls, score, menus or touch areas at 1280x800 or 390x844, set `games-link` in the game's metadata to a free corner, with a distance from the edge if needed (`top-left 68px`), or `off` when the game has its own way back (`docs/GAME_METADATA.md`). |
| Changing how a game saves progress | Keep existing saves loading: read the old format or migrate it. Never silently reset a player's saved progress or high scores. |
| The dungeon crawler | Its build output (`index.html`, `assets/`) is made by `tools/pack.py` and never committed. Vite's `base` must stay `/projects/games/dungeon-crawler/`. |

Shortcut: if `python3 tools/pack.py` passes, the release will build; it applies every rule above.

### Files shared with other repos

- Identical in bensonlabs/games, bensonlabs/projects and bensonlabs/bootstraps:
  `.github/workflows/release.yml`, `tools/next_version.py`, `tools/check_shared.py`,
  `tools/test_check_shared.py`, and three functions in `tools/pack.py` (`read_publishignore`,
  `publishable`, `write_release`).
- Identical in games and projects: `.github/workflows/ci.yml` and `tools/html_checks.py`.
- What differs per repo comes from the repository's name (`github.event.repository.name`): the
  component, its release notes, and the steps that have an `if:` for games. Keep it that way: no
  per-repo edits inside a shared file.
- `tools/check_shared.py` runs on every pull request and fails when a copy differs; its list of
  shared files is at its top. To change a shared file, make the same change in every repo that
  shares it on one branch name, push all those branches, then open the pull requests: each check
  compares against the other repos' branch of that name, or main if there's none.
- Why copies rather than a shared package: the repos are small and separate on purpose (site
  review P11, owner default 2026-11-08). The check replaced "change both" notes in the files
  (owner decision 2026-11-08: checks, not reminders).

### Commands

On Windows, `python3` isn't on the PATH: run the same commands with `py`.

- Install: nothing for most games. `tools/pack.py` runs `npm ci` for the dungeon crawler when
  its `node_modules` wasn't installed from the current `package.json` and `package-lock.json`,
  and always in CI.
- Run locally: `python3 tools/pack.py`, then `python3 -m http.server -d dist` and open
  http://localhost:8000/projects/games/ (games use their real addresses; `/favicon.svg` comes
  from the blog, so it's missing here).
- Tests, type check, lint (wrap-up runs these): `python3 -m unittest discover -s tools -p 'test_*.py'`,
  `python3 tools/pack.py`, `python3 tools/check_dungeon_build.py`. The tests include
  `tools/test_docs.py`: every repo path the docs cite in backticks must exist.

### Environments

- Sandbox for testing: a local pack in `dist/`, served as above. There is no shared test site.
- Live, and who changes it: bensonlabs.org shows the release pinned in the blog's
  `_data/components.json`. A push to `main` that changes what the site shows goes live within
  minutes; the blog deploys only after its own checks pass.

### Branches, review and release

- PRs go to (target branch): `main`. Adding, changing or removing a game goes straight to `main`
  (owner decision, 2026-11-07); tools and workflows go through a PR.
- Branch names (default `feature/<short-name>`): the default.
- Bring a branch up to date by (merge or rebase): merge.
- Reviewer: with no second reviewer, the person reviews the whole diff themselves before it merges.
- How changes reach users, and who runs it: nobody runs anything. Every push to `main` that changes
  what the site shows makes the Release workflow publish the next version (`games-vX.Y.Z.tar.gz`
  and its sha256) and ask the blog to pin it; the blog's Update components workflow runs its checks,
  pins the release and deploys (ADR 3).

### Checks this project relies on

Each stops a mistake that happened once or would break the site (core rule 6):

- `tools/pack.py` refuses a pack when a game breaks the Games rules: no `index.html`, front matter
  or the site header inside a game, a game over 1 MB in all, or one file over 750 KB.
- `tools/test_docs.py`: every repo path the docs cite in backticks exists.
- `tools/check_shared.py` (pull request job "Shared files match the other repos"): the files shared
  with bensonlabs/projects and bensonlabs/bootstraps match their copies.
- "Packing changes no committed file" (`git diff --exit-code` after packing, in the PR check):
  generated files are committed up to date.
- actionlint (pull request job "Lint the workflows"): the workflow files are valid, and their
  scripts pass shellcheck.
- The release publishes only main's current head (ADR 4), and the blog deploys a release only
  after its own page checks pass.

### Where things live

- Pages and navigation: one folder per game in `games/<slug>/` (published at
  `/projects/games/<slug>/`); the catalogue is `games/index.html`. Site navigation belongs to the blog.
- Help or user docs: `README.md`; `docs/GAME_METADATA.md`; `docs/AGENT_PROMPT_ADDENDUM.md`.
- Starter docs: none yet.
- API endpoints: none; the games are static files.

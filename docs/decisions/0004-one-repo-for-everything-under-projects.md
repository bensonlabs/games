# ADR 4: One repo for everything under /projects/

**Date:** 2026-11-08
**Status:** accepted

## Context

Justin wants to add a game, a project, a workout plan or anything else that is a single HTML page,
with its card on the right index, in one step, for every section in the site menu (2026-11-08).
Games lived here, the workout plans in bensonlabs/workouts and the other project pages in the blog,
each published a different way.

## Decision

- This repo (renamed from bensonlabs/games) owns everything under /projects/; `site/` mirrors it.
  The blog's project pages and bensonlabs/workouts moved in with their history.
- A section is the Projects page or any folder with a `section.json`; it lists cards for the
  folders inside it. A card comes from `card.json`, a `bl-card` comment or front matter
  (`tools/sections.py`). Workouts and Bootstraps became sections: Justin's plan moved to
  /projects/workouts/justin/ and /projects/workouts/ is now the index of plans; the Bootstraps post
  became the first guide at /projects/bootstraps/workstations/ (Justin's choices, 2026-11-08).
- The release lists the pages that get the site header (`.components-wrap.json`), so a new page
  gets it without a change in the blog. One `add` skill handles every section.
- Blog posts and About stay in the blog.

## Alternatives considered

- Keep games here and add the same flow to the blog for projects: two places that work the same.
- One repo per kind: three copies of the same tooling.

## Consequences

- One place, one skill and one pipeline for anything under /projects/.
- Two addresses changed: Justin's workout plan and the Bootstraps post; the blog redirects the old
  /bootstraps/ address.
- bensonlabs/workouts is archived.

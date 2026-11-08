# ADR 4: Release only main's head, from a job that runs no third-party code

**Date:** 2026-11-08
**Status:** accepted (changes how ADR 3's Release workflow runs; its decision stands)

## Context

The site review on the night of 2026-11-07 found that the Release workflow (ADR 3) could publish the wrong thing
or expose its tokens:

- Started by hand on another branch, it released that branch to the live site, without a review.
- Re-running an old run (for example after renewing an expired token) released that run's older
  content as the newest version, and the blog deployed it.
- One job held the write token and the blog's dispatch token while `tools/pack.py` ran `npm ci` and
  the dungeon crawler's build, which is a few hundred npm packages, some with install scripts.
- Without `pipefail`, a failed sha256 download looked like "no release yet", so the same pack was
  published again as a new version.

Justin approved the fixes the same morning.

## Decision

- Two jobs. **build** tests and packs with read-only access and no token left in the clone.
  **publish** downloads the pack and releases it. It holds `contents: write` and
  `BLOG_DISPATCH_TOKEN`, and runs only this repo's own Python and `gh`.
- Only main is released (`if:` on the build job). The publish job also checks that the run's
  commit is still main's head, so an old or re-run run publishes nothing.
- The publish job runs in the `release` environment, which only main may use. When the token is
  next renewed, saving it there instead of as a repository secret keeps it from every other job
  and branch.
- The scripts run with `pipefail`. The job fails when a release exists but its sha256 can't be
  read, and when the blog refuses the token, with a message saying the release is out and the
  blog's daily run pins it.
- The blog is asked to update every component to its newest release, not just this one, so a
  request that replaces one still queued in the blog loses nothing.
- `.github/workflows/release.yml` is shared with bensonlabs/projects: change both.

## Alternatives considered

- Keep one job, and drop the npm build from the release: the dungeon crawler is built from source,
  and a committed build would drift from it.
- Pin the release's version in the blog request, as before: a request that replaces one still
  queued in the blog would lose that release until the daily run.

## Consequences

- A release takes one more job (about 15 s) to hand the pack over.
- Re-running a failed old run is safe; it publishes nothing unless its commit is still main's head.
- Each release shows as a deployment to the `release` environment on the repo page.

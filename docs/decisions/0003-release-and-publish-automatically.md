# ADR 3: Release and publish automatically

**Date:** 2026-11-08
**Status:** accepted (changes the consequences of ADR 2; its decision stands)

## Context

After the split (ADR 2), adding a game took about eight steps across two repos: a PR, a merge, a
tag, the release, a pin change in the blog, its PR and its merge. Justin's main wish is an
effortless way to add a game and its catalogue card. He is the site's only user, and he chose to
have a new game live within minutes (2026-11-08).

## Decision

- Adding, changing or removing a game goes straight to `main`, usually through the `add-game`
  skill.
- Every push to `main` runs the Release workflow. Packs are reproducible, so it compares the fresh
  pack's sha256 with the latest release's: unchanged means no release; changed means the next
  patch version is published by the workflow itself, with no tag pushed by hand.
- The workflow then asks the blog to pin it (`gh workflow run update-components.yml` with a
  fine-grained token, `BLOG_DISPATCH_TOKEN`, that may only run the blog's workflows). The blog
  builds the whole site with the new release, runs its checks and only then pins and deploys. A
  daily run in the blog catches any release whose request didn't arrive.

## Alternatives considered

- The blog checks for new releases on a schedule only: no token, but up to 30 minutes' wait.
- Keep the manual tag and pin change: the review point stays, and so do the eight steps.
- Let the blog fetch the newest release at every build without pinning: no record of what the
  site shows, and a broken release would go live without a check.

## Consequences

- One step for Justin; the checks here (tests, pack, size and header rules) and the blog's page
  checks are the gate.
- Pins still record exactly what the site shows, now committed by the blog's workflow.
- The token expires: GitHub emails a reminder, and until it's renewed the daily run still
  publishes new games, a day late at worst.

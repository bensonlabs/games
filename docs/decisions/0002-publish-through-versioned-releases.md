# ADR 2: Publish the games through versioned releases

**Date:** 2026-11-07
**Status:** accepted; its first consequence (a release and a pin change by hand for every
change) was replaced by ADR 3, which releases and pins automatically. The decision stands.

## Context

The games lived inside the blog repo, which built them as part of every site deploy: the
blog carried npm tooling for one game, Dependabot PRs for packages the blog doesn't use,
16 MB of images and the games' source and tooling files, all published on the site. Justin
decided to break the blog into components that each own their part of the site.

## Decision

This repo owns everything under `/projects/games/`, including the catalogue page. It
publishes the games as a versioned GitHub release: one `games-vX.Y.Z.tar.gz`, built in CI
by `tools/pack.py`, holding only what a browser needs, plus its sha256. The blog pins a
release by version and sha256 in `_data/components.json`, unpacks it at the same address,
and wraps only the catalogue page in the site header.

## Alternatives considered

- The blog keeps the catalogue page and the games publish only data: less work, but one
  folder on the site would then have two owners.
- The blog checks out this repo's `main` at deploy time (as it did for workouts): any merge
  would go live on the next blog deploy without a deliberate step, and a deploy couldn't be
  reproduced later.
- Each repo publishes its own GitHub Pages site: every address would change to
  `/<repo-name>/`, and the catalogue would have to gather data from several repos.

## Consequences

- A game change reaches the site only after a release and a one-line pin change in the
  blog. That's one more step, and also the point where the change gets reviewed.
- The release is the contract: the games are built for `/projects/games/` and rely on the
  site for `/favicon.svg`; the blog decides which pages get its header.
- The blog's ADR on assembling components describes the other side.

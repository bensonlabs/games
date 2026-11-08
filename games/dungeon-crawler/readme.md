<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# Mythic Dungeon Crawler

React and TypeScript roguelike built with Vite. It is published as a static game at `/projects/games/dungeon-crawler/`.

## Run Locally

Prerequisite: Node.js 22 or later.

```bash
npm ci
npm run dev
```

`npm run lint` type-checks it with TypeScript.

## Build and Publish

```bash
npm run build
```

Vite uses `index.source.html` as its source entrypoint and emits `dist/index.source.html` plus hashed assets. The repo's `tools/pack.py` builds the game (`npm ci`, then `npm run build`) and packs only `dist/` into the games release, with `dist/index.source.html` renamed to `index.html`; the Release workflow publishes that release and the blog serves it. Locally, `tools/pack.py` skips `npm ci` while `node_modules` was installed from the current `package.json` and `package-lock.json`; in CI it always runs it. The build output is never committed: edit `index.source.html`, never a generated `index.html`.

`GEMINI_API_KEY` is only needed for Gemini API features. Copy `.env.example` to a local `.env` file if those features are enabled; never commit the key.

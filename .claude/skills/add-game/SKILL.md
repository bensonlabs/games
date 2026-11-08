---
name: add-game
description: Add a new game to bensonlabs.org - put its HTML in games/<slug>/, write its catalogue card, check it, and push it; it goes live by itself within minutes. Use whenever Justin hands over a game (an HTML file, pasted HTML or a link) and wants it on the site, or asks to change an existing game's card.
---

# Add a game

Adding a game is one push to `main`: the Release workflow publishes the next release and the
blog pins it and deploys after its checks (owner decision, 2026-11-08). Do the steps below without
asking, except where they say to show Justin something.

1. **Get the game.** An HTML file, pasted HTML, or a link to download. It must be one complete,
   standalone page: its own `<html>`, `<head>` and `<body>`, no front matter, no site header
   (`docs/AGENT_PROMPT_ADDENDUM.md`). If it loads other files (images, sounds, scripts), bring them
   into the same folder and keep their relative paths. Keep every file under 750 KB: shrink images
   to the size they're drawn.
2. **Choose the slug**: short, lowercase, words joined by hyphens, from the game's title. It becomes
   `bensonlabs.org/projects/games/<slug>/`. Make sure `games/<slug>/` doesn't exist yet.
3. **Write the card** as a `bl-game-meta` comment at the top of the page's `<head>`
   (`docs/GAME_METADATA.md`):

   ```html
   <!-- bl-game-meta
   title: Game Title
   emoji: 🎮
   order: 999
   description: One sentence on what you do in the game. Made by <model> in <tool>.
   -->
   ```

   Pick an emoji that fits. Write the description from the game itself; end it with
   "Made by <model> in <tool>." only when Justin says or the file shows how it was made. Keep
   `order: 999` unless he gives a place. Show him the card in one line; change it if he asks.
4. **Check it**: `python3 tools/pack.py` must pass. It catches a missing page, a site header, front
   matter and files over 750 KB.
5. **Commit and push** only the game's folder: `git add games/<slug>` then a commit "Add <title>"
   and `git push` to `main`. If the push reminder says something, answer it in the commit message as
   it asks.
6. **Confirm it went live.** Watch the Release run (`gh run watch` on the newest Release run), then
   the blog's Update components run. When both pass, check
   `https://bensonlabs.org/projects/games/<slug>/` answers 200 and the catalogue lists the card.
   Report the link. If a check fails, the site keeps the previous release: say what failed.

## Changing a card or a game

Same steps from 3: edit the game's `bl-game-meta` comment (or its files), check, commit, push.
Removing a game: delete its folder, check, commit "Remove <title>", push.

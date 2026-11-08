# Echoes of Eternity

Echoes of Eternity is a static browser game: plain HTML, CSS and JavaScript, with no build step.
It's published at https://bensonlabs.org/projects/games/echoes-of-eternity/ as part of the games
release, which `tools/pack.py` packs (this readme isn't published).

## How it runs

- No backend server
- No database
- No npm build step
- Persistent best score and echo trails stored in `localStorage`

## Files

- `index.html` - the game page, linked from the games catalogue
- `style.css`
- `main.js`

## Controls

- `W` / `S` or `↑` / `↓` to steer
- `Space` or mouse hold to boost
- On mobile, use the on-screen `↑` / `↓` buttons to steer and `BOOST` to surge
- On touch devices, you can also drag on the playfield to line up your route without boosting
- `Enter` to restart after a collapse

#!/usr/bin/env python3
"""Build the games and pack them exactly as bensonlabs.org serves them.

    python3 tools/pack.py                    # build and check dist/projects/games/
    python3 tools/pack.py --version v1.2.0   # also write dist/games-v1.2.0.tar.gz + .sha256

What a release contains:
- each game folder in games/, minus files a browser never needs: Markdown, Rust,
  TOML, TypeScript, shell scripts, lockfiles, package and metadata files, hidden
  files, and anything listed in the game's own .publishignore (glob patterns);
- for a game with a package.json, only its npm build output (dist/);
- games/index.html, the catalogue, with the games list written in twice: as data
  for the script that draws the cards, and as plain links for visitors without
  JavaScript.

No published file may be over 750 KB, and no game over 1 MB in all. Every page
needs a <meta name="description">.

A game with a package.json is built with `npm ci` and `npm run build`. Locally,
`npm ci` is skipped while the game's node_modules was installed from its current
package.json and package-lock.json; in CI (the CI variable set) it always runs.

The blog (bensonlabs/blog) downloads the release, checks its sha256, unpacks it
into /projects/games/ and wraps the catalogue in the site header. Game pages stay
standalone documents.
"""
from __future__ import annotations

import argparse
import fnmatch
import gzip
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import build_games_registry as registry
from html_checks import Page

GAMES_DIR = registry.GAMES_DIR
DIST = registry.REPO_ROOT / "dist"
OUT = DIST / "projects" / "games"
PLACEHOLDER = "[] /* games list: filled in by tools/pack.py */"
NOSCRIPT_PLACEHOLDER = "<!-- games list without JavaScript: filled in by tools/pack.py -->"
MAX_FILE_BYTES = 750 * 1024
# Source: site review E1, approved by Justin 2026-11-08. Sparky's Run had grown to 1.3 MB of
# PNGs drawn at a third of their size; the limit stops a game creeping back up.
MAX_GAME_BYTES = 1024 * 1024
VERSION_RE = re.compile(r"v\d+\.\d+\.\d+")

NEVER_PUBLISHED_SUFFIXES = {".md", ".rs", ".toml", ".ts", ".tsx", ".sh", ".lock"}
NEVER_PUBLISHED_NAMES = {"package.json", "package-lock.json", "tsconfig.json",
                         "game.json", "metadata.json", "index.source.html"}
NEVER_PUBLISHED_DIRS = {"node_modules", "dist"}
# Written into node_modules after a successful `npm ci`: what it was installed from.
INSTALL_MARKER = ".pack-installed-from"


def read_publishignore(game_dir: Path) -> list[str]:
    path = game_dir / ".publishignore"
    if not path.is_file():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def publishable(game_dir: Path, path: Path, ignore: list[str]) -> bool:
    rel = path.relative_to(game_dir)
    if any(part.startswith(".") for part in rel.parts):
        return False
    if any(part in NEVER_PUBLISHED_DIRS for part in rel.parts[:-1]):
        return False
    if path.suffix.lower() in NEVER_PUBLISHED_SUFFIXES or path.name in NEVER_PUBLISHED_NAMES:
        return False
    return not any(fnmatch.fnmatch(rel.as_posix(), pattern) for pattern in ignore)


def copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def run(command: list[str], cwd: Path) -> None:
    executable = shutil.which(command[0]) or command[0]
    subprocess.run([executable, *command[1:]], cwd=cwd, check=True)


def install_fingerprint(game_dir: Path) -> str:
    """The sha256 of what `npm ci` installs from: package.json and package-lock.json."""
    digest = hashlib.sha256()
    for name in ("package.json", "package-lock.json"):
        digest.update(hashlib.sha256((game_dir / name).read_bytes()).digest())
    return digest.hexdigest()


def needs_npm_ci(game_dir: Path, environ=os.environ) -> bool:
    """Always in CI; locally, only when node_modules wasn't installed from the current files.

    `npm ci` took 17-21 s of a 20 s local pack, reinstalling the same packages every time
    (site review E4, 2026-11-08). CI always installs afresh."""
    if environ.get("CI"):
        return True
    try:
        marker = (game_dir / "node_modules" / INSTALL_MARKER).read_text(encoding="utf-8")
    except OSError:
        return True
    return marker.strip() != install_fingerprint(game_dir)


def pack_built_game(game_dir: Path, dest: Path) -> None:
    """A game with a package.json is built with npm; only its dist/ is published."""
    if needs_npm_ci(game_dir):
        run(["npm", "ci", "--no-audit", "--no-fund"], game_dir)
        (game_dir / "node_modules" / INSTALL_MARKER).write_text(
            install_fingerprint(game_dir) + "\n", encoding="utf-8", newline="\n")
    else:
        print(f"{game_dir.name}: node_modules matches package-lock.json, so no npm ci (CI always runs it)",
              flush=True)
    run(["npm", "run", "build"], game_dir)
    built = game_dir / "dist"
    for path in sorted(p for p in built.rglob("*") if p.is_file()):
        rel = path.relative_to(built)
        copy(path, dest / ("index.html" if rel.as_posix() == "index.source.html" else rel))


def pack_static_game(game_dir: Path, dest: Path) -> None:
    ignore = read_publishignore(game_dir)
    for path in sorted(p for p in game_dir.rglob("*") if p.is_file()):
        if publishable(game_dir, path, ignore):
            copy(path, dest / path.relative_to(game_dir))


def noscript_list(games: list[dict]) -> str:
    """The games as plain links (the same list the cards show), for visitors and crawlers
    that don't run JavaScript. Source: site review L10, approved by Justin 2026-11-08.

    The blog runs the catalogue's body through Liquid, so braces are written as character
    references: no title or description can turn into a Liquid tag."""
    def escape(value: str) -> str:
        return html.escape(value).replace("{", "&#123;").replace("}", "&#125;")
    return "\n      ".join(
        f'<li><a href="{escape(game["path"])}">{escape(game["title"])}</a><br>{escape(game["description"])}</li>'
        for game in games)


def write_catalogue(games: list[dict]) -> None:
    template = (GAMES_DIR / "index.html").read_text(encoding="utf-8")
    for placeholder in (PLACEHOLDER, NOSCRIPT_PLACEHOLDER):
        if template.count(placeholder) != 1:
            sys.exit(f"games/index.html must contain {placeholder!r} exactly once")
    # Compact JSON, as Jekyll's jsonify wrote it before the split, with "</" escaped
    # so no title or description can end the <script> early.
    data = json.dumps(games, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = template.replace(PLACEHOLDER, data).replace(NOSCRIPT_PLACEHOLDER, noscript_list(games))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8", newline="\n")


def game_sizes() -> dict[str, int]:
    """Bytes each packed game publishes, by folder name (the catalogue isn't a game)."""
    sizes: dict[str, int] = {}
    for path in OUT.rglob("*"):
        rel = path.relative_to(OUT)
        if path.is_file() and len(rel.parts) > 1:
            sizes[rel.parts[0]] = sizes.get(rel.parts[0], 0) + path.stat().st_size
    return sizes


def check(games: list[dict]) -> list[str]:
    errors = []
    for game in games:
        if not (DIST / game["path"].strip("/") / "index.html").is_file():
            errors.append(f"{game['path']}: no index.html")
    for slug, size in sorted(game_sizes().items()):
        if size > MAX_GAME_BYTES:
            errors.append(f"{slug}: {size // 1024} KB in all, over the {MAX_GAME_BYTES / 1048576:g} MB limit "
                          "for one game: shrink its images, sounds or fonts")
    for path in sorted(p for p in OUT.rglob("*") if p.is_file()):
        rel = path.relative_to(OUT).as_posix()
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            errors.append(f"{rel}: {size // 1024} KB, over the {MAX_FILE_BYTES // 1024} KB limit for one file")
        if path.suffix != ".html":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        page = Page(text)
        # Source: site review L8, approved by Justin 2026-11-08: search results and link previews
        # show it; the card's first sentence (without "Made by ...") is the usual choice.
        if len(page.descriptions) != 1 or not page.descriptions[0]:
            found = f"found {len(page.descriptions)}" if len(page.descriptions) != 1 else "it's empty"
            errors.append(f'{rel}: needs exactly one <meta name="description"> with text ({found}); for a game, '
                          "the first sentence of its card's description, in index.source.html if it has one")
        if "/" in rel:  # a game page, not the catalogue
            if text.startswith("---\n"):
                errors.append(f"{rel}: games are standalone pages: no front matter")
            if page.site_header:
                errors.append(f"{rel}: games are standalone pages: no site header (found {page.site_header[0]})")
    return errors


def write_release(version: str) -> Path:
    """Pack OUT reproducibly (sorted entries, fixed times and modes): the same files
    always give the same sha256."""
    name = f"games-{version}.tar.gz"
    files = sorted((p for p in OUT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(OUT).as_posix())
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for path in files:
            info = tarfile.TarInfo(path.relative_to(OUT).as_posix())
            info.size = path.stat().st_size
            info.mode = 0o644
            info.mtime = 0
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    archive = DIST / name
    with archive.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
        gz.write(buffer.getvalue())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (DIST / f"{name}.sha256").write_text(f"{digest}  {name}\n", encoding="utf-8", newline="\n")
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the games and pack them for bensonlabs.org.")
    parser.add_argument("--version", help="release version such as v1.2.0; also writes the release file")
    args = parser.parse_args()
    if args.version and not VERSION_RE.fullmatch(args.version):
        sys.exit(f"--version must look like v1.2.0, not {args.version!r}")

    if DIST.exists():
        shutil.rmtree(DIST)
    games = registry.build_games_array()
    for game_dir in registry.find_game_dirs():
        dest = OUT / game_dir.name
        if (game_dir / "package.json").is_file():
            pack_built_game(game_dir, dest)
        else:
            pack_static_game(game_dir, dest)
    write_catalogue(games)

    errors = check(games)
    if errors:
        print("Pack FAILED:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)
    files = [p for p in OUT.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"Packed {len(games)} games: {len(files)} files, {size / 1048576:.1f} MB in dist/projects/games/")
    largest = max(game_sizes().items(), key=lambda item: item[1], default=None)
    if largest:
        print(f"Largest game: {largest[0]}, {largest[1] // 1024} KB of the {MAX_GAME_BYTES // 1024} KB limit")
    if args.version:
        archive = write_release(args.version)
        print((DIST / f"{archive.name}.sha256").read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    main()

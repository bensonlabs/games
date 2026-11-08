#!/usr/bin/env python3
"""Build the games and pack them exactly as bensonlabs.org serves them.

    python3 tools/pack.py                    # build and check dist/projects/games/
    python3 tools/pack.py --version v1.2.0   # also write dist/games-v1.2.0.tar.gz + .sha256

What a release contains:
- each game folder in games/, minus files a browser never needs: Markdown, Rust,
  TOML, TypeScript, shell scripts, lockfiles, package and metadata files, hidden
  files, and anything listed in the game's own .publishignore (glob patterns);
- for a game with a package.json, only its npm build output (dist/);
- games/index.html, the catalogue, with the games list written in.

No published file may be over 750 KB, and no game over 1 MB in all.

The blog (bensonlabs/blog) downloads the release, checks its sha256, unpacks it
into /projects/games/ and wraps the catalogue in the site header. Game pages stay
standalone documents.
"""
from __future__ import annotations

import argparse
import fnmatch
import gzip
import hashlib
import io
import json
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
MAX_FILE_BYTES = 750 * 1024
# Source: site review E1, approved by Justin 2026-11-08. Sparky's Run had grown to 1.3 MB of
# PNGs drawn at a third of their size; the limit stops a game creeping back up.
MAX_GAME_BYTES = 1024 * 1024
VERSION_RE = re.compile(r"v\d+\.\d+\.\d+")

NEVER_PUBLISHED_SUFFIXES = {".md", ".rs", ".toml", ".ts", ".tsx", ".sh", ".lock"}
NEVER_PUBLISHED_NAMES = {"package.json", "package-lock.json", "tsconfig.json",
                         "game.json", "metadata.json", "index.source.html"}
NEVER_PUBLISHED_DIRS = {"node_modules", "dist"}


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


def pack_built_game(game_dir: Path, dest: Path) -> None:
    """A game with a package.json is built with npm; only its dist/ is published."""
    run(["npm", "ci", "--no-audit", "--no-fund"], game_dir)
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


def write_catalogue(games: list[dict]) -> None:
    template = (GAMES_DIR / "index.html").read_text(encoding="utf-8")
    if template.count(PLACEHOLDER) != 1:
        sys.exit("games/index.html must contain the games-list placeholder exactly once")
    # Compact JSON, as Jekyll's jsonify wrote it before the split, with "</" escaped
    # so no title or description can end the <script> early.
    data = json.dumps(games, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(template.replace(PLACEHOLDER, data), encoding="utf-8", newline="\n")


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
        if path.suffix == ".html" and "/" in rel:  # a game page, not the catalogue
            text = path.read_text(encoding="utf-8", errors="replace")
            if text.startswith("---\n"):
                errors.append(f"{rel}: games are standalone pages: no front matter")
            header = Page(text).site_header
            if header:
                errors.append(f"{rel}: games are standalone pages: no site header (found {header[0]})")
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

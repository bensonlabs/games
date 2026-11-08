#!/usr/bin/env python3
"""Validate authored game metadata and build the catalogue list (dist/games.json).

Precedence: game.json > index.source.html > index.html. Generated compiled
entrypoints are never metadata inputs. Partial metadata uses legacy fallbacks.
See GAME_METADATA.md for the source and validation contract.
"""
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GAMES_DIR = REPO_ROOT / "games"
OUTPUT_FILE = REPO_ROOT / "dist" / "games.json"

META_BLOCK_RE = re.compile(r"<!--\s*bl-game-meta(.*?)-->", re.DOTALL)
FIELD_RE = re.compile(r"^(title|emoji|order|description|games-link):\s*(.*)$")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
META_DESCRIPTION_RE = re.compile(
    r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"'][^>]*>",
    re.IGNORECASE | re.DOTALL,
)
META_DESCRIPTION_RE_ALT = re.compile(
    r"<meta[^>]+content=[\"'](.*?)[\"'][^>]+name=[\"']description[\"'][^>]*>",
    re.IGNORECASE | re.DOTALL,
)

REQUIRED_FIELDS = ("title", "emoji", "order", "description")
DEFAULT_EMOJI = "🎮"
DEFAULT_ORDER = 999
# Optional, and not part of the card: where tools/pack.py puts the game's "← Games" link
# back to the catalogue: a corner, optionally followed by its distance in px from the top
# (or bottom) edge, to clear the game's own controls ("top-left 68px"); or "off" for a
# game with its own way back.
GAMES_LINK_FIELD = "games-link"
GAMES_LINK_RE = re.compile(r"(?P<corner>(?:top|bottom)-(?:left|right))(?: (?P<distance>\d{1,4})px)?|off")
DEFAULT_GAMES_LINK = "top-left"

def find_game_dirs():
    return sorted({p.parent for name in ("index.html", "index.source.html", "game.json")
                   for p in GAMES_DIR.glob(f"*/{name}")})


def collapse_ws(text):
    return re.sub(r"\s+", " ", text).strip()


def title_from_slug(slug):
    return " ".join(part.capitalize() for part in slug.split("-"))


def normalize_title(title):
    if not title:
        return title
    normalized = collapse_ws(title)
    normalized = re.sub(
        r"\s+(?:—|-|\|)\s+Benson\s+Labs\s*$",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized.strip()


def extract_title(text):
    m = TITLE_RE.search(text)
    if not m:
        return None
    return normalize_title(m.group(1))


def extract_meta_description(text):
    m = META_DESCRIPTION_RE.search(text) or META_DESCRIPTION_RE_ALT.search(text)
    if not m:
        return None
    return collapse_ws(m.group(1))


def parse_meta_block(text):
    matches = META_BLOCK_RE.findall(text)
    starts = re.findall(r"<!--\s*bl-game-meta\b", text)
    if len(starts) != len(matches):
        return None, "malformed bl-game-meta block"
    if len(matches) > 1:
        return None, "duplicate bl-game-meta blocks"
    if not matches:
        if "bl-game-meta" in text:
            return None, "malformed bl-game-meta block"
        return None, None
    m = META_BLOCK_RE.search(text)
    if not m:
        return None, None

    fields = {}
    for line in m.group(1).strip().splitlines():
        line = line.strip()
        if not line:
            continue
        fm = FIELD_RE.match(line)
        if not fm:
            return None, f"unrecognized metadata line: {line!r}"
        if fm.group(1) in fields:
            return None, f"duplicate metadata field: {fm.group(1)}"
        fields[fm.group(1)] = fm.group(2).strip()
    return fields, None


def derive_fields(slug, text):
    title = extract_title(text) or title_from_slug(slug)
    description = extract_meta_description(text) or f"Browser game: {title}."
    return {
        "title": title,
        "emoji": DEFAULT_EMOJI,
        "order": DEFAULT_ORDER,
        "description": description,
    }


def merge_fields(slug, text, fields):
    derived = derive_fields(slug, text)
    merged = {}

    for field in REQUIRED_FIELDS:
        value = fields.get(field) if fields else None
        if value is None or value == "":
            merged[field] = derived[field]
        else:
            merged[field] = value

    for field in ("title", "emoji", "description"):
        if not isinstance(merged[field], str):
            return None, f"{field} must be a string"
    link = (fields or {}).get(GAMES_LINK_FIELD, "")
    if link != "" and not (isinstance(link, str) and GAMES_LINK_RE.fullmatch(link)):
        return None, (f"{GAMES_LINK_FIELD} must be top-left, top-right, bottom-left or bottom-right, "
                      f"optionally with a distance such as \"top-left 68px\", or off; got {link!r}")
    if isinstance(merged["order"], bool) or not re.fullmatch(r"[+-]?\d+", str(merged["order"])):
        return None, f"order must be an integer, got {merged['order']!r}"
    try:
        merged["order"] = int(merged["order"])
    except (ValueError, TypeError):
        return None, f"order must be an integer, got {merged['order']!r}"

    return merged, None


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate metadata field: {key}")
        result[key] = value
    return result


def read_metadata(game_dir):
    # A compiled game's generated index.html must not affect even fallbacks.
    source = game_dir / "index.source.html"
    sidecar = game_dir / "game.json"
    if source.exists():
        text = source.read_text(encoding="utf-8")
    elif sidecar.exists():
        # Do not even open a generated entrypoint: it may not exist yet.
        text = ""
    else:
        source = game_dir / "index.html"
        text = source.read_text(encoding="utf-8")
    fields, err = parse_meta_block(text)
    if err:
        raise ValueError(err)
    if sidecar.exists():
        fields = json.loads(sidecar.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if not isinstance(fields, dict):
            raise ValueError("game.json must contain an object")
        unknown = fields.keys() - {*REQUIRED_FIELDS, GAMES_LINK_FIELD}
        if unknown:
            raise ValueError(f"unknown fields: {', '.join(sorted(unknown))}")
        for key, value in fields.items():
            if value is None:
                raise ValueError(f"{key} cannot be null; omit it to use a fallback")
        source = sidecar
    return source, text, fields


def games_link(game_dir):
    """Where the game's "← Games" link goes (top-left by default), or "off"."""
    _, _, fields = read_metadata(game_dir)
    return (fields or {}).get(GAMES_LINK_FIELD) or DEFAULT_GAMES_LINK


def build_games_array():
    errors = []
    notes = []
    games = []

    for game_dir in find_game_dirs():
        slug = game_dir.name
        try:
            index_html, text, fields = read_metadata(game_dir)
        except (ValueError, OSError) as exc:
            errors.append(f"{game_dir.relative_to(REPO_ROOT)}: {exc}")
            continue

        note = None
        if fields is None:
            note = (
                f"{index_html.relative_to(REPO_ROOT)}: no bl-game-meta block; "
                "using deterministic fallback values"
            )
        else:
            fallback_fields = [
                field
                for field in REQUIRED_FIELDS
                if field not in fields or fields[field] == ""
            ]
            if fallback_fields:
                note = (
                    f"{index_html.relative_to(REPO_ROOT)}: fallback for missing "
                    f"field(s): {', '.join(fallback_fields)}"
                )

        merged, err = merge_fields(slug, text, fields)
        if err:
            errors.append(f"{index_html.relative_to(REPO_ROOT)}: {err}")
            continue

        if note:
            notes.append(note)

        games.append({
            "title": merged["title"],
            "description": merged["description"],
            "emoji": merged["emoji"],
            "path": f"/projects/games/{slug}/",
            "order": merged["order"],
        })

    if errors:
        print("Games registry build FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    for note in notes:
        print(f"NOTICE: {note}", file=sys.stderr)

    games.sort(key=lambda g: (g["order"], g["title"]))
    for g in games:
        del g["order"]
    return games


def main():
    games = build_games_array()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(games, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {OUTPUT_FILE.name} ({len(games)} games).")


if __name__ == "__main__":
    main()

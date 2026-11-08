#!/usr/bin/env python3
"""The site's sections and their cards (site/ mirrors /projects/ on bensonlabs.org).

A section is the Projects page (site/ itself) or any folder with a section.json. It lists the
cards of the folders directly inside it. A folder inside a section is an item (a game, a
project, a plan, a guide); a folder that is itself a section gets a card on its parent from its
section.json.

A card has a title, an emoji, a description, an order (lower comes first; 999 by default) and
a cta (the button's words, "Open →" by default), and optionally a link (somewhere else instead
of the item's own page), header: no (the item's page stays standalone, without the site header)
and listed: no (no card). A section.json can also give its page an intro.

Where a card comes from, first found wins: the folder's card.json (or section.json); a bl-card
comment in its index.html (the older bl-game-meta works too); the front matter of its index.md
or index.html; then the page's <title> and description meta tag.

The games catalogue keeps its own list (tools/build_games_registry.py); games/section.json is
only the games' card on the Projects page.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SITE = REPO_ROOT / "site"
TEMPLATE = REPO_ROOT / "templates" / "section.html"
SITE_URL = "/projects/"
PLACEHOLDER = "[] /* cards: filled in by tools/pack.py */"
DEFAULT_EMOJI = "🧩"
DEFAULT_ORDER = 999
DEFAULT_CTA = "Open →"
FIELDS = {"title", "emoji", "order", "description", "cta", "link", "header", "listed", "intro"}
PAGE_NAMES = ("index.html", "index.source.html", "index.md")

COMMENT_RE = re.compile(r"<!--\s*bl-(?:card|game-meta)\b(.*?)-->", re.S)
FIELD_RE = re.compile(r"^\s*([a-z]+):\s*(.*?)\s*$")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DESCRIPTION_RE = re.compile(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"']", re.I | re.S)


def is_section(folder: Path) -> bool:
    return folder == SITE or (folder / "section.json").is_file()


def page_of(folder: Path) -> Path | None:
    for name in PAGE_NAMES:
        if (folder / name).is_file():
            return folder / name
    return None


def url_of(folder: Path) -> str:
    rel = folder.relative_to(SITE).as_posix()
    return SITE_URL if rel == "." else f"{SITE_URL}{rel}/"


def _fields(text: str) -> dict:
    found = {}
    for line in text.splitlines():
        match = FIELD_RE.match(line)
        if match and match.group(1) in FIELDS:
            value = match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            found[match.group(1)] = value
    return found


def read_card(folder: Path) -> dict:
    """The card fields as written, from the first place that has them."""
    for name in ("card.json", "section.json"):
        source = folder / name
        if source.is_file():
            data = json.loads(source.read_text(encoding="utf-8"))
            unknown = set(data) - FIELDS
            if unknown:
                raise ValueError(f"{source}: unknown card fields {sorted(unknown)}")
            return data
    page = page_of(folder)
    if page is None:
        return {}
    text = page.read_text(encoding="utf-8", errors="replace")
    comment = COMMENT_RE.search(text)
    if comment:
        return _fields(comment.group(1))
    front = FRONT_MATTER_RE.match(text)
    card = _fields(front.group(1)) if front else {}
    if "title" not in card:
        title = TITLE_RE.search(text)
        if title:
            card["title"] = html.unescape(re.sub(r"\s+", " ", title.group(1)).strip())
    if "description" not in card:
        description = DESCRIPTION_RE.search(text)
        if description:
            card["description"] = html.unescape(description.group(1).strip())
    return card


def card(folder: Path) -> dict | None:
    """The card a folder shows on its section's page, or None when it isn't listed."""
    data = read_card(folder)
    if str(data.get("listed", "yes")).lower() == "no":
        return None
    try:
        order = int(data.get("order", DEFAULT_ORDER))
    except (TypeError, ValueError):
        raise ValueError(f"{folder}: order must be a whole number, not {data.get('order')!r}") from None
    return {
        "title": data.get("title") or folder.name.replace("-", " ").title(),
        "description": data.get("description", ""),
        "emoji": data.get("emoji") or DEFAULT_EMOJI,
        "path": data.get("link") or url_of(folder),
        "cta": data.get("cta") or DEFAULT_CTA,
        "_order": order,
    }


def sections() -> list[Path]:
    return sorted({SITE, *(path.parent for path in SITE.rglob("section.json"))})


def items(section: Path) -> list[Path]:
    """The folders directly inside a section that show a card (or could)."""
    return [child for child in sorted(p for p in section.iterdir() if p.is_dir())
            if is_section(child) or page_of(child) or (child / "card.json").is_file()]


def cards_for(section: Path) -> list[dict]:
    found = [c for c in (card(child) for child in items(section)) if c]
    found.sort(key=lambda c: (c["_order"], c["title"].lower()))
    return [{key: value for key, value in c.items() if not key.startswith("_")} for c in found]


def render_section(section: Path) -> str:
    """The section's page with its cards written in: its own index.html, or the template."""
    data = json.dumps(cards_for(section), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    own = section / "index.html"
    if own.is_file():
        page, source = own.read_text(encoding="utf-8"), own
    else:
        info = read_card(section)
        page, source = TEMPLATE.read_text(encoding="utf-8"), TEMPLATE
        page = page.replace("__SECTION_TITLE__", html.escape(info.get("title") or section.name.title()))
        page = page.replace("__SECTION_INTRO__", html.escape(info.get("intro", "")))
    if page.count(PLACEHOLDER) != 1:
        raise ValueError(f"{source}: needs the cards placeholder exactly once")
    return page.replace(PLACEHOLDER, data)


def _standalone(page: Path) -> bool:
    return page.suffix == ".html" and not page.read_text(encoding="utf-8", errors="replace").startswith("---")


def wrapped_pages(games: Path) -> list[str]:
    """Pages (relative to site/) the blog wraps in the site header: every section's page and
    every item's own index.html that is standalone HTML, except games and cards with header: no."""
    pages = []
    for section in sections():
        own = section / "index.html"
        if section != SITE and (not own.is_file() or _standalone(own)):
            pages.append((section / "index.html").relative_to(SITE).as_posix())
        if section == games:
            continue
        for item in items(section):
            page = item / "index.html"
            if is_section(item) or not page.is_file() or not _standalone(page):
                continue
            if str(read_card(item).get("header", "yes")).lower() != "no":
                pages.append(page.relative_to(SITE).as_posix())
    return sorted(pages)

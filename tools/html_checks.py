"""Reading game pages with an HTML parser rather than text search (core rule 8).

A page only "has the site header" when it contains the header's elements or files: an element
whose id or class starts with bl-nav (or the old nav-autohide), or a link to the blog's
/assets/css/header.css or /assets/js/header.js. A comment or a string that merely mentions
bl-nav doesn't count.
"""
from html.parser import HTMLParser

HEADER_ASSETS = ("/assets/css/header.css", "/assets/js/header.js")


def _is_header_name(name: str) -> bool:
    return name.startswith("bl-nav") or name == "nav-autohide"


class Page(HTMLParser):
    """Element ids, linked scripts and stylesheets, meta descriptions, and any trace of the
    blog's site header."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.ids: dict[str, int] = {}
        self.assets: list[str] = []
        self.descriptions: list[str] = []
        self.site_header: list[str] = []
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = {name: value or "" for name, value in attrs}
        element_id = attrs.get("id", "")
        if element_id:
            self.ids[element_id] = self.ids.get(element_id, 0) + 1
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.descriptions.append(attrs.get("content", "").strip())
        for name in [element_id, *attrs.get("class", "").split()]:
            if name and _is_header_name(name):
                self.site_header.append(f'<{tag}> "{name}"')
        source = None
        if tag == "script" and attrs.get("src"):
            source = attrs["src"]
            self.assets.append(source)
        elif tag == "link" and attrs.get("href"):
            source = attrs["href"]
            if attrs.get("rel") == "stylesheet":
                self.assets.append(source)
        if source and (source in HEADER_ASSETS or "nav-autohide" in source):
            self.site_header.append(f"<{tag}> {source}")

#!/usr/bin/env python3
"""Verify the packed dungeon crawler: Vite's entrypoint and its asset references.

Run after tools/pack.py; it reads dist/projects/games/dungeon-crawler/.
"""
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / 'dist'
GAME = SITE / 'projects/games/dungeon-crawler'


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = {}; self.assets = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            key = attrs['id']; self.ids[key] = self.ids.get(key, 0) + 1
        if tag == 'script' and attrs.get('src'): self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet': self.assets.append(attrs['href'])


text = (GAME / 'index.html').read_text(encoding='utf-8')
page = Page(text)
assert page.ids.get('root') == 1, 'React mount is missing or duplicated'
assert not any(token in text for token in ('bl-nav', 'nav-autohide', '/src/main.tsx'))
assert not text.startswith('---\n')
assert any(asset.endswith('.js') for asset in page.assets), 'Missing bundled JavaScript'
assert any(asset.endswith('.css') for asset in page.assets), 'Missing bundled CSS'
for asset in page.assets:
    if asset.startswith('https://'): continue
    assert asset.startswith('/projects/games/dungeon-crawler/assets/'), asset
    assert (SITE / asset.lstrip('/')).is_file(), f'Missing {asset}'
print('Dungeon React mount and deployed asset paths verified.')

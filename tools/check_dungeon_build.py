#!/usr/bin/env python3
"""Verify the packed dungeon crawler: Vite's entrypoint and its asset references.

Run after tools/pack.py; it reads dist/projects/games/dungeon-crawler/.
"""
from pathlib import Path

from html_checks import Page

SITE = Path(__file__).resolve().parents[1] / 'dist'
GAME = SITE / 'projects/games/dungeon-crawler'


text = (GAME / 'index.html').read_text(encoding='utf-8')
page = Page(text)
assert page.ids.get('root') == 1, 'React mount is missing or duplicated'
assert not page.site_header, f'Site header in the game: {page.site_header[:3]}'
assert '/src/main.tsx' not in page.assets, 'The unbuilt Vite entry is still linked'
assert not text.startswith('---\n')
assert any(asset.endswith('.js') for asset in page.assets), 'Missing bundled JavaScript'
assert any(asset.endswith('.css') for asset in page.assets), 'Missing bundled CSS'
for asset in page.assets:
    if asset.startswith('https://'): continue
    assert asset.startswith('/projects/games/dungeon-crawler/assets/'), asset
    assert (SITE / asset.lstrip('/')).is_file(), f'Missing {asset}'
print('Dungeon React mount and deployed asset paths verified.')

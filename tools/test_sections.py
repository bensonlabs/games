"""Tests for tools/sections.py: where cards come from, section pages, and which pages get the site header."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sections

TEMPLATE = '<html><head><title>__SECTION_TITLE__</title></head><body><p>__SECTION_INTRO__</p><script>const GAMES = ' + sections.PLACEHOLDER + ';</script></body></html>'


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class Cards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.site = Path(self.tmp.name) / 'site'
        self.site.mkdir()
        write(Path(self.tmp.name), 'templates/section.html', TEMPLATE)
        self.patches = [patch.object(sections, 'SITE', self.site),
                        patch.object(sections, 'TEMPLATE', Path(self.tmp.name) / 'templates' / 'section.html')]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_card_sources_in_order_of_precedence(self):
        write(self.site, 'a/card.json', json.dumps({'title': 'From JSON', 'order': 3}))
        write(self.site, 'a/index.html', '<!-- bl-card\ntitle: Ignored\n-->')
        write(self.site, 'b/index.html', '<html><head><!-- bl-card\ntitle: From comment\nemoji: 🎲\norder: 1\ncta: Play →\n-->')
        write(self.site, 'c/index.md', '---\nlayout: post\ntitle: "From front matter"\ndescription: A guide.\n---\nText')
        write(self.site, 'd/index.html', '<title>From &amp; title</title><meta name="description" content="Meta text">')
        write(self.site, 'e/index.html', '<!-- bl-game-meta\ntitle: Old comment\n-->')
        cards = {c['title']: c for c in sections.cards_for(self.site)}
        self.assertEqual(set(cards), {'From JSON', 'From comment', 'From front matter', 'From & title', 'Old comment'})
        self.assertEqual(cards['From comment']['emoji'], '🎲')
        self.assertEqual(cards['From comment']['cta'], 'Play →')
        self.assertEqual(cards['From front matter']['description'], 'A guide.')
        self.assertEqual(cards['From & title']['description'], 'Meta text')
        self.assertEqual(cards['Old comment']['cta'], 'Open →')
        self.assertEqual(cards['From JSON']['path'], '/projects/a/')
        self.assertEqual([c['title'] for c in sections.cards_for(self.site)][:2], ['From comment', 'From JSON'])

    def test_unlisted_cards_and_outside_links(self):
        write(self.site, 'hidden/card.json', json.dumps({'title': 'Hidden', 'listed': 'no'}))
        write(self.site, 'hidden/index.html', '<html></html>')
        write(self.site, 'app/card.json', json.dumps({'title': 'App', 'link': 'https://example.invalid/app'}))
        cards = sections.cards_for(self.site)
        self.assertEqual([c['title'] for c in cards], ['App'])
        self.assertEqual(cards[0]['path'], 'https://example.invalid/app')

    def test_unknown_card_fields_and_bad_orders_are_errors(self):
        write(self.site, 'a/card.json', json.dumps({'title': 'A', 'colour': 'red'}))
        with self.assertRaises(ValueError):
            sections.cards_for(self.site)
        write(self.site, 'a/card.json', json.dumps({'title': 'A', 'order': 'first'}))
        with self.assertRaises(ValueError):
            sections.cards_for(self.site)

    def test_a_section_without_its_own_page_uses_the_template(self):
        write(self.site, 'plans/section.json', json.dumps({'title': 'Plans & <More>', 'intro': 'Each one page.'}))
        write(self.site, 'plans/one/index.html', '<!-- bl-card\ntitle: One\n-->')
        page = sections.render_section(self.site / 'plans')
        self.assertIn('<title>Plans &amp; &lt;More&gt;</title>', page)
        self.assertIn('<p>Each one page.</p>', page)
        self.assertIn('"title":"One"', page)
        self.assertNotIn(sections.PLACEHOLDER, page)
        self.assertEqual(sections.cards_for(self.site)[0]['title'], 'Plans & <More>')

    def test_a_section_page_needs_the_placeholder(self):
        write(self.site, 'index.html', '<script>const PROJECTS = [];</script>')
        with self.assertRaises(ValueError):
            sections.render_section(self.site)

    def test_which_pages_get_the_site_header(self):
        write(self.site, 'games/section.json', json.dumps({'title': 'Games'}))
        write(self.site, 'games/index.html', '<html><head></head><body></body></html>')
        write(self.site, 'games/pong/index.html', '<html><head></head><body></body></html>')
        write(self.site, 'plans/section.json', json.dumps({'title': 'Plans'}))
        write(self.site, 'plans/mine/index.html', '<html><head></head><body></body></html>')
        write(self.site, 'tool/index.html', '<html><head></head><body></body></html>')
        write(self.site, 'bare/card.json', json.dumps({'title': 'Bare', 'header': 'no'}))
        write(self.site, 'bare/index.html', '<html><head></head><body></body></html>')
        write(self.site, 'layout/index.html', '---\nlayout: project\n---\n<p>x</p>')
        write(self.site, 'guide/index.md', '---\ntitle: Guide\n---\nText')
        self.assertEqual(sections.wrapped_pages(self.site / 'games'),
                         ['games/index.html', 'plans/index.html', 'plans/mine/index.html', 'tool/index.html'])


if __name__ == '__main__':
    unittest.main()

"""Tests for tools/pack.py: what a release contains, the catalogue, the checks and the release file."""
import contextlib
import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import html_checks
import pack


def make(root, names, content='x'):
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')


class PublishRules(unittest.TestCase):
    def test_only_files_a_browser_needs_are_published(self):
        keep = ['index.html', 'js/game.js', 'img/dog.png', 'pkg/game.wasm', 'levels.json', 'docs/pkg/game.js']
        drop = ['README.md', 'stub.md', 'Cargo.toml', 'Cargo.lock', 'src/main.rs', 'build.sh', 'bun.lock',
                'package.json', 'package-lock.json', 'game.json', 'metadata.json', 'tsconfig.json',
                'vite.config.ts', 'src/App.tsx', 'index.source.html', '.gitignore', '.nojekyll',
                '.publishignore', 'node_modules/x/index.js', 'dist/index.html', 'checks/play.mjs']
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            make(game, keep + drop)
            for name in keep:
                self.assertTrue(pack.publishable(game, game / name, ['checks/*.mjs']), name)
            for name in drop:
                self.assertFalse(pack.publishable(game, game / name, ['checks/*.mjs']), name)

    def test_publishignore_skips_blank_lines_and_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            game = Path(tmp)
            (game / '.publishignore').write_text('# dev checks\n\n*.mjs\n', encoding='utf-8')
            self.assertEqual(pack.read_publishignore(game), ['*.mjs'])
            self.assertEqual(pack.read_publishignore(game / 'missing'), [])


class Catalogue(unittest.TestCase):
    def test_games_list_is_written_in_and_cannot_close_the_script(self):
        games = [{'title': 'A</script>', 'description': 'Dark fantasy ⚔️', 'emoji': '🎮', 'path': '/projects/games/a/'}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, ['games/index.html'], '<script>const GAMES = ' + pack.PLACEHOLDER + ';</script>')
            with patch.object(pack, 'GAMES_DIR', root / 'games'), patch.object(pack, 'OUT', root / 'out'):
                pack.write_catalogue(games)
            text = (root / 'out' / 'index.html').read_text(encoding='utf-8')
        self.assertEqual(text.count('</script>'), 1)
        data = text[len('<script>const GAMES = '):-len(';</script>')]
        self.assertEqual(json.loads(data), games)
        self.assertIn('⚔️', data)  # written as-is, as Jekyll's jsonify did

    def test_template_must_have_the_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make(root, ['games/index.html'], '<script>const GAMES = [];</script>')
            with patch.object(pack, 'GAMES_DIR', root / 'games'), patch.object(pack, 'OUT', root / 'out'):
                with self.assertRaises(SystemExit):
                    pack.write_catalogue([])


class Checks(unittest.TestCase):
    def test_flags_missing_pages_big_files_and_site_header_in_games(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / 'dist'
            out = dist / 'projects' / 'games'
            make(out, ['index.html', 'ok/index.html'])
            make(out, ['nav/index.html'], '<nav id="bl-nav"></nav>')
            make(out, ['front/index.html'], '---\nlayout: project\n---\n')
            make(out, ['big/index.html'], 'x' * (pack.MAX_FILE_BYTES + 1))
            games = [{'path': f'/projects/games/{slug}/'} for slug in ('ok', 'nav', 'front', 'big', 'missing')]
            with patch.object(pack, 'DIST', dist), patch.object(pack, 'OUT', out):
                errors = pack.check(games)
        self.assertEqual(len(errors), 4, errors)
        for expected in ('/projects/games/missing/', 'nav/index.html', 'front/index.html', 'big/index.html'):
            self.assertTrue(any(expected in error for error in errors), expected)


    def test_flags_a_game_over_the_size_limit_for_one_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / 'dist'
            out = dist / 'projects' / 'games'
            make(out, ['index.html'], 'x' * pack.MAX_FILE_BYTES)  # the catalogue isn't a game
            make(out, ['heavy/a.webp', 'heavy/b.webp'], 'x' * 600 * 1024)  # each file is under its limit
            make(out, ['heavy/index.html'])
            make(out, ['full/index.html'], 'x' * (pack.MAX_GAME_BYTES - pack.MAX_FILE_BYTES))
            make(out, ['full/a.webp'], 'x' * pack.MAX_FILE_BYTES)  # exactly at the limit is fine
            games = [{'path': '/projects/games/heavy/'}, {'path': '/projects/games/full/'}]
            with patch.object(pack, 'DIST', dist), patch.object(pack, 'OUT', out):
                errors = [error for error in pack.check(games) if 'in all' in error]
        self.assertEqual(errors, ['heavy: 1200 KB in all, over the 1 MB limit for one game: '
                                  'shrink its images, sounds or fonts'])


class SiteHeader(unittest.TestCase):
    def test_found_by_its_elements_and_files_not_by_mentions(self):
        mentions = ('<html><body><!-- no bl-nav here --><p>about bl-nav</p>'
                    '<script>const note = "bl-nav nav-autohide";</script></body></html>')
        self.assertEqual(html_checks.Page(mentions).site_header, [])
        for page in ('<nav id="bl-nav" class="bl-nav"></nav>', '<div class="x bl-nav__links"></div>',
                     '<button id="bl-nav-toggle"></button>', '<div class="nav-autohide"></div>',
                     '<link rel="stylesheet" href="/assets/css/header.css">',
                     '<script src="/assets/js/header.js"></script>'):
            with self.subTest(page=page):
                self.assertTrue(html_checks.Page(page).site_header)

    def test_a_game_that_only_mentions_the_header_passes_the_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / 'dist'
            out = dist / 'projects' / 'games'
            make(out, ['index.html'])
            make(out, ['ok/index.html'], '<html><body><!-- not a bl-nav --><canvas></canvas></body></html>')
            with patch.object(pack, 'DIST', dist), patch.object(pack, 'OUT', out):
                self.assertEqual(pack.check([{'path': '/projects/games/ok/'}]), [])


class NpmInstall(unittest.TestCase):
    """npm ci runs in CI, and locally only when node_modules wasn't installed from these files."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.game = Path(self.tmp.name)
        make(self.game, ['package.json'], '{"name": "game"}')
        make(self.game, ['package-lock.json'], '{"lockfileVersion": 3}')

    def tearDown(self):
        self.tmp.cleanup()

    def installed(self):
        make(self.game, ['node_modules/' + pack.INSTALL_MARKER], pack.install_fingerprint(self.game) + '\n')

    def test_runs_when_nothing_says_what_node_modules_holds(self):
        self.assertTrue(pack.needs_npm_ci(self.game, environ={}))
        make(self.game, ['node_modules/vite/index.js'])  # installed some other way
        self.assertTrue(pack.needs_npm_ci(self.game, environ={}))

    def test_skipped_when_node_modules_matches(self):
        self.installed()
        self.assertFalse(pack.needs_npm_ci(self.game, environ={}))

    def test_runs_again_after_the_lockfile_or_package_json_changes(self):
        for name in ('package-lock.json', 'package.json'):
            with self.subTest(changed=name):
                self.installed()
                (self.game / name).write_text('{"changed": true}', encoding='utf-8')
                self.assertTrue(pack.needs_npm_ci(self.game, environ={}))

    def test_always_runs_in_ci(self):
        self.installed()
        self.assertTrue(pack.needs_npm_ci(self.game, environ={'CI': 'true'}))

    def test_a_build_records_the_install_and_the_next_build_skips_it(self):
        commands = []

        def fake_run(command, cwd):
            commands.append(' '.join(command[:2]))
            if command[:2] == ['npm', 'ci']:
                make(cwd, ['node_modules/vite/index.js'])
            else:
                make(cwd, ['dist/index.source.html'], '<html></html>')

        output = io.StringIO()
        with patch.object(pack, 'run', fake_run), patch.dict(os.environ), contextlib.redirect_stdout(output):
            os.environ.pop('CI', None)
            pack.pack_built_game(self.game, self.game / 'out')
            pack.pack_built_game(self.game, self.game / 'out')
        self.assertEqual(commands, ['npm ci', 'npm run', 'npm run'])
        self.assertIn('so no npm ci', output.getvalue())
        self.assertTrue((self.game / 'out' / 'index.html').is_file())


class Release(unittest.TestCase):
    def test_release_is_reproducible_and_matches_its_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp) / 'dist'
            out = dist / 'projects' / 'games'
            make(out, ['index.html', 'b/index.html', 'a/img/x.png'])
            with patch.object(pack, 'DIST', dist), patch.object(pack, 'OUT', out):
                first = pack.write_release('v1.2.3').read_bytes()
                second = pack.write_release('v1.2.3').read_bytes()
            sha_line = (dist / 'games-v1.2.3.tar.gz.sha256').read_text(encoding='utf-8')
            with tarfile.open(dist / 'games-v1.2.3.tar.gz') as tar:
                members = tar.getmembers()
        self.assertEqual(first, second)
        self.assertEqual(sha_line, hashlib.sha256(first).hexdigest() + '  games-v1.2.3.tar.gz\n')
        self.assertEqual([m.name for m in members], ['a/img/x.png', 'b/index.html', 'index.html'])
        self.assertTrue(all(m.isfile() and m.mode == 0o644 and m.mtime == 0 for m in members))


if __name__ == '__main__':
    unittest.main()

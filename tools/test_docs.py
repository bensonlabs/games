"""The docs cite only repo paths that exist (site review P14, 2026-11-08).

Checks README.md, CLAUDE.md, docs/** and .claude/skills/**: every path in `backticks` that
starts with tools/, games/, docs/ or .claude/ must exist. A path with a placeholder in it
(`games/<slug>/index.html`, `docs/decisions/NNNN-<slug>.md`) is a pattern: the folder before
its first placeholder must exist. A decision record cited by its number (`docs/decisions/0002`)
must match exactly one record. The docs are Markdown, not code, so a pattern finds the
`code spans` (core rule 8 allows text search for non-code files).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ("README.md", "CLAUDE.md", "docs/**/*.md", ".claude/skills/**/*.md")
PREFIXES = ("tools/", "games/", "docs/", ".claude/")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
PLACEHOLDER = re.compile(r"<[^>]*>|\*|\{|N{4}")
DECISION_NUMBER = re.compile(r"docs/decisions/(\d{4})")


def cited_paths(text: str) -> list[str]:
    """The repo paths in a Markdown text's code spans, one per word that starts like one."""
    paths = []
    for span in CODE_SPAN.findall(text):
        for word in span.split():
            word = word.strip("'\"(),.:;")
            if word.startswith(PREFIXES):
                paths.append(word)
    return paths


def exists(path: str, root: Path = ROOT) -> bool:
    placeholder = PLACEHOLDER.search(path)
    if placeholder:
        return (root / path[:placeholder.start()].rpartition("/")[0]).is_dir()
    number = DECISION_NUMBER.fullmatch(path)
    if number:
        return len(list((root / "docs" / "decisions").glob(f"{number.group(1)}-*.md"))) == 1
    return (root / path).exists()


class DocPaths(unittest.TestCase):
    def test_every_repo_path_the_docs_cite_exists(self):
        docs = sorted({path for pattern in DOCS for path in ROOT.glob(pattern)})
        self.assertIn(ROOT / "README.md", docs)
        self.assertTrue(any(".claude" in path.parts for path in docs))
        missing = [f"{doc.relative_to(ROOT).as_posix()}: `{path}`"
                   for doc in docs for path in cited_paths(doc.read_text(encoding="utf-8")) if not exists(path)]
        self.assertEqual(missing, [], "the docs cite paths that don't exist")

    def test_finds_paths_in_code_spans_and_judges_them(self):
        text = ("Run `python3 tools/pack.py --version v1.2.0`, see `docs/GAME_METADATA.md`, and not "
                "tools/outside-backticks.py or `https://example.com/tools/x`.")
        self.assertEqual(cited_paths(text), ["tools/pack.py", "docs/GAME_METADATA.md"])
        for path in ("tools/pack.py", "games/", "games/<slug>/index.html", "docs/decisions/NNNN-<slug>.md",
                     "docs/decisions/0002", ".claude/skills/add-game/SKILL.md"):
            with self.subTest(path=path):
                self.assertTrue(exists(path))
        for path in ("tools/no-such-tool.py", "docs/decisions/0099", "games/no-such-game/<slug>.html"):
            with self.subTest(path=path):
                self.assertFalse(exists(path))


if __name__ == "__main__":
    unittest.main()

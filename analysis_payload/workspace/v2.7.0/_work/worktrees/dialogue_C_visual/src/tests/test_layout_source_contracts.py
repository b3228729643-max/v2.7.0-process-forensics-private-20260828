from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '讲义源码'
STYLE = SOURCE / 'common' / 'statlearnbook.sty'
VOLUME_DIRS = sorted(path for path in SOURCE.iterdir() if path.name.startswith('第0') and '册_' in path.name)


class LayoutSourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.style = STYLE.read_text(encoding='utf-8')
        cls.latex_files = sorted(
            path
            for path in SOURCE.rglob('*')
            if path.suffix.lower() in {'.tex', '.sty', '.cls'}
        )

    def test_no_prohibited_font_or_whole_object_shrinking(self) -> None:
        prohibited = re.compile(r'\\(?:tiny|scriptsize|resizebox)\b')
        hits = []
        for path in self.latex_files:
            for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if prohibited.search(line) and not line.lstrip().startswith('%'):
                    hits.append(f'{path.relative_to(ROOT)}:{number}:{line.strip()}')
        self.assertEqual(hits, [], '\n'.join(hits))

    def test_math_script_floor_and_algorithm_line_number_size(self) -> None:
        declarations = {
            float(text): (float(script), float(scriptscript))
            for text, script, scriptscript in re.findall(
                r'\\DeclareMathSizes\{([0-9.]+)\}\{[0-9.]+\}\{([0-9.]+)\}\{([0-9.]+)\}',
                self.style,
            )
        }
        for text_size in (8.5, 9.0, 10.0, 10.95, 12.0):
            self.assertIn(text_size, declarations)
            script, scriptscript = declarations[text_size]
            self.assertGreaterEqual(script, 7.5)
            self.assertGreaterEqual(scriptscript, 7.5)
        for text_size in (8.5, 9.0, 10.0):
            script, scriptscript = declarations[text_size]
            self.assertGreaterEqual(script, 9.0)
            self.assertGreaterEqual(scriptscript, 9.0)
        self.assertGreaterEqual(declarations[10.95][1], 8.0)
        self.assertGreaterEqual(declarations[12.0][0], 11.5)
        self.assertGreaterEqual(declarations[12.0][1], 11.5)
        self.assertRegex(self.style, r"\\setsansfont\{TeX Gyre Heros\}\[Scale=1\]")
        self.assertRegex(self.style, r'\\SetAlgoNlRelativeSize\{0\}')

    def test_long_teaching_boxes_are_breakable(self) -> None:
        # The three legacy chapter-opening fields are captured and rendered in
        # one breakable five-field chapter map in v1.9.  They are deliberately
        # no longer separate visible tcolorboxes.
        for name in ('prerequisitebox', 'precheckbox', 'dependencybox'):
            self.assertRegex(
                self.style,
                rf'\\NewDocumentEnvironment\{{{name}\}}\{{\+b\}}',
                name,
            )
        renderer = self.style[
            self.style.index(r'\newcommand{\SLRenderChapterMap}'):
            self.style.index(r'\newcommand{\SLLevelSection}')
        ]
        self.assertIn('enhanced,breakable', renderer)

        for name in ('selfcheckbox', 'chaptersummarybox', 'chapterexercisebox'):
            pattern = rf'\\newtcolorbox\{{{name}\}}[^\n]*\bbreakable\b'
            self.assertRegex(self.style, pattern, name)
        self.assertIn('breakable', self.style[self.style.index('chapteranswerbox'):])

    def test_volume_entries_follow_tagged_pdf_compatibility_policy(self) -> None:
        self.assertEqual(len(VOLUME_DIRS), 5)
        for volume_dir in VOLUME_DIRS:
            entry = (volume_dir / 'main.tex').read_text(encoding='utf-8')
            self.assertNotIn(r'\DocumentMetadata', entry, volume_dir.name)
            self.assertIn(r'\documentclass[UTF8,a4paper,11pt,openany]{ctexbook}', entry)
            self.assertIn(r'\usepackage{../common/statlearnbook}', entry)
            self.assertIn(r'\SLSetBookMetadata', entry)

    def test_every_chapter_uses_compact_closure_and_bounded_self_check(self) -> None:
        chapter_files = [
            path
            for path in self.latex_files
            if path.name.startswith('V') and '-C' in path.name and path.suffix == '.tex'
        ]
        self.assertEqual(len(chapter_files), 37)
        for path in chapter_files:
            text = path.read_text(encoding='utf-8')
            self.assertEqual(text.count(r'\begin{SLCompactClosure}'), 1, path.name)
            self.assertEqual(text.count(r'\end{SLCompactClosure}'), 1, path.name)
            match = re.search(
                r'\\begin\{selfcheckbox\}.*?\\begin\{enumerate\}(.*?)\\end\{enumerate\}(.*?)\\end\{selfcheckbox\}',
                text,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, path.name)
            items = len(re.findall(r'\\item\b', match.group(1)))
            self.assertGreaterEqual(items, 3, path.name)
            self.assertLessEqual(items, 5, path.name)
            self.assertEqual(match.group(2).strip(), '', f'{path.name}: trailing prose can orphan')


if __name__ == '__main__':
    unittest.main()

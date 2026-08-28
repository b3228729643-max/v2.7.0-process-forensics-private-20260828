#!/usr/bin/env python3
"""Static contracts for the v1.9.0 global chapter navigation registry."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "讲义源码" / "common" / "statlearnbook.sty"
SOURCE = STYLE.read_text(encoding="utf-8")


def expected_mapping(chapter: int) -> tuple[int, int]:
    if chapter <= 11:
        return 1, chapter
    if chapter <= 16:
        return 2, chapter - 11
    if chapter <= 23:
        return 3, chapter - 16
    if chapter <= 29:
        return 4, chapter - 23
    return 5, chapter - 29


class NavigationRegistryTests(unittest.TestCase):
    def test_all_37_chapters_are_registered_once(self) -> None:
        rows = re.findall(
            r"\\SLDeclareGlobalChapter\{(\d+)\}\{(\d+)\}\{(\d+)\}",
            SOURCE,
        )
        self.assertEqual(37, len(rows))
        self.assertEqual(37, len({int(global_no) for global_no, _, _ in rows}))

    def test_registry_matches_volume_boundaries(self) -> None:
        rows = {
            int(global_no): (int(volume), int(local))
            for global_no, volume, local in re.findall(
                r"\\SLDeclareGlobalChapter\{(\d+)\}\{(\d+)\}\{(\d+)\}",
                SOURCE,
            )
        }
        self.assertEqual(
            {chapter: expected_mapping(chapter) for chapter in range(1, 38)},
            rows,
        )

    def test_public_navigation_macros_exist(self) -> None:
        for command in (
            r"\newcommand{\GlobalChapterRef}[3]",
            r"\newcommand{\NextChapter}[2]",
            r"\newcommand{\SLMethodLimitationsHeading}",
            r"\newcommand{\SLDegeneracyHeading}",
            r"\newcommand{\SLCommonErrorsHeading}",
            r"\newcommand{\SLComplexityAssumptionsHeading}",
        ):
            self.assertIn(command, SOURCE)

    def test_every_registered_label_exists_in_chapter_sources(self) -> None:
        all_tex = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "讲义源码").glob("第*册_*/chapters/V*-C*.tex")
        )
        for chapter in range(1, 38):
            volume, local = expected_mapping(chapter)
            label = f"chap:V{volume}-C{local:02d}"
            with self.subTest(chapter=chapter, label=label):
                self.assertEqual(1, all_tex.count(rf"\label{{{label}}}"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Static navigation contracts for NAV-001 through NAV-014."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "讲义源码"


CHAPTERS = {
    "V1-C03": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C03.tex",
    "V1-C05": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C05.tex",
    "V1-C06": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C06.tex",
    "V1-C08": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C08.tex",
    "V1-C10": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C10.tex",
    "V5-C01": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C01.tex",
    "V5-C03": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C03.tex",
    "V5-C04": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C04.tex",
    "V5-C06": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C06.tex",
    "V5-C07": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C07.tex",
    "V5-C08": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C08.tex",
}


def read_chapter(chapter: str) -> str:
    return CHAPTERS[chapter].read_text(encoding="utf-8")


def anchored_block(source: str, anchor: str) -> str:
    marker = rf"\phantomsection\label{{{anchor}}}"
    start = source.index(marker)
    next_anchor = source.find(r"\phantomsection\label{", start + len(marker))
    return source[start:] if next_anchor == -1 else source[start:next_anchor]


def opening_block(source: str) -> str:
    start = source.index(r"\SLChapterOpening")
    end = source.index(r"\phantomsection\label{", start)
    return source[start:end]


class NavigationContractTests(unittest.TestCase):
    def test_nav_001_chapter_three_enters_chapter_four_then_reuses_tools(self) -> None:
        block = anchored_block(read_chapter("V1-C03"), "schema:V1-C03:CH-36")
        self.assertIn(r"\NextChapter{4}{概率论基础}", block)
        self.assertIn(r"\GlobalChapterRef{7}{1}{7}", block)
        self.assertIn(r"\GlobalChapterRef{8}{1}{8}", block)

    def test_nav_002_chapter_six_enters_chapter_seven(self) -> None:
        block = anchored_block(read_chapter("V1-C06"), "struct:V1-C06-CH36")
        self.assertIn(r"\NextChapter{7}{凸优化与拉格朗日对偶}", block)
        self.assertIn(r"\GlobalChapterRef{15}{2}{4}", block)

    def test_nav_003_chapter_eight_enters_learning_framework(self) -> None:
        block = anchored_block(read_chapter("V1-C08"), "struct:V1-C08-CH36")
        self.assertIn(r"\NextChapter{9}{统计学习的基本框架}", block)
        self.assertIn(r"\GlobalChapterRef{12}{2}{1}", block)

    def test_nav_004_chapter_ten_enters_task_specification(self) -> None:
        block = anchored_block(read_chapter("V1-C10"), "struct:V1-C10-CH36")
        self.assertIn(r"\NextChapter{11}{监督学习任务与应用}", block)
        self.assertIn(r"\GlobalChapterRef{12}{2}{1}", block)

    def test_nav_005_three_prerequisite_questions_have_individual_exact_routes(self) -> None:
        block = anchored_block(read_chapter("V1-C05"), "struct:V1-C05-CH03")
        q1 = (
            r"\GlobalChapterRef{4}{1}{4}的\cref{sec:V1-C04-S04}，"
            r"并预习本章\cref{sec:V1-C05-S05}"
        )
        q2 = (
            r"\GlobalChapterRef{3}{1}{3}的"
            r"\cref{sec:V1-C03-S02,sec:V1-C03-S04,sec:V1-C03-S05,sec:V1-C03-S06}"
        )
        q3 = (
            r"\GlobalChapterRef{2}{1}{2}的\cref{sec:V1-C02-S06}或"
            r"\GlobalChapterRef{4}{1}{4}的\cref{sec:V1-C04-S03}"
        )
        self.assertIn(q1, block)
        self.assertIn(q2, block)
        self.assertIn(q3, block)
        self.assertNotIn("若有一项不能回答，分别回看", block)
        declarations = {
            "V1-C02": ("sec:V1-C02-S06",),
            "V1-C03": (
                "sec:V1-C03-S02",
                "sec:V1-C03-S04",
                "sec:V1-C03-S05",
                "sec:V1-C03-S06",
            ),
            "V1-C04": ("sec:V1-C04-S03", "sec:V1-C04-S04"),
            "V1-C05": ("sec:V1-C05-S05",),
        }
        for chapter, labels in declarations.items():
            path = (
                SOURCE_ROOT
                / "第01册_数学基础与统计学习基本理论"
                / "chapters"
                / f"{chapter}.tex"
            )
            source = path.read_text(encoding="utf-8")
            for label in labels:
                self.assertRegex(
                    source,
                    re.compile(rf"\\SL[A-Za-z]+Section\{{[^}}]+\}}\{{{re.escape(label)}\}}"),
                )

    def test_nav_006_chapter_thirty_enters_thirty_one_and_points_to_thirty_two(self) -> None:
        block = anchored_block(read_chapter("V5-C01"), "struct:V5-C01-CH36")
        self.assertIn(r"\NextChapter{31}{蒙特卡罗方法与直接采样}", block)
        self.assertIn(r"\GlobalChapterRef{32}{5}{3}", block)

    def test_nav_007_mh_prerequisites_use_global_chapters_thirty_and_thirty_one(self) -> None:
        source = read_chapter("V5-C03")
        opening = opening_block(source)
        prerequisites = anchored_block(source, "struct:V5-C03-CH02")
        dependencies = anchored_block(source, "struct:V5-C03-CH04")
        for block in (opening, prerequisites, dependencies):
            self.assertIn(r"\GlobalChapterRef{30}{5}{1}", block)
            self.assertIn(r"\GlobalChapterRef{31}{5}{2}", block)

    def test_nav_008_gibbs_opening_points_to_global_chapter_thirty_two(self) -> None:
        opening = opening_block(read_chapter("V5-C04"))
        self.assertIn(r"\GlobalChapterRef{32}{5}{3}", opening)
        self.assertNotIn("第3章", opening)

    def test_nav_009_gibbs_prerequisite_and_dependency_use_one_global_style(self) -> None:
        source = read_chapter("V5-C04")
        prerequisites = anchored_block(source, "struct:V5-C04-CH02")
        dependencies = anchored_block(source, "struct:V5-C04-CH04")
        for block in (prerequisites, dependencies):
            self.assertIn(r"\GlobalChapterRef{32}{5}{3}", block)
            self.assertNotIn("第5册第3章", block)

    def test_nav_010_gibbs_next_step_is_global_chapter_thirty_five(self) -> None:
        block = anchored_block(read_chapter("V5-C04"), "struct:V5-C04-CH36")
        self.assertIn(r"\NextChapter{35}{潜在狄利克雷分配}", block)
        self.assertNotIn(r"\NextChapter{34}", block)

    def test_nav_011_lda_opening_uses_global_coordinate_gibbs_reference(self) -> None:
        opening = opening_block(read_chapter("V5-C06"))
        self.assertIn(r"\GlobalChapterRef{33}{5}{4}", opening)
        self.assertNotIn("第4章", opening)

    def test_nav_012_lda_dependency_uses_global_dirichlet_and_gibbs_references(self) -> None:
        source = read_chapter("V5-C06")
        opening = opening_block(source)
        dependencies = anchored_block(source, "struct:V5-C06-CH04")
        for block in (opening, dependencies):
            self.assertIn(r"\GlobalChapterRef{34}{5}{5}", block)
            self.assertIn(r"\GlobalChapterRef{33}{5}{4}", block)

    def test_nav_013_pagerank_enters_global_chapter_thirty_seven(self) -> None:
        block = anchored_block(read_chapter("V5-C07"), "struct:V5-C07-CH36")
        self.assertIn(r"\NextChapter{37}{无监督学习方法总结}", block)
        self.assertIn(r"\GlobalChapterRef{30}{5}{1}", block)
        self.assertNotIn("第8章", block)
        self.assertNotIn("第36章", block)

    def test_nav_014_source_already_uses_non_self_referential_wording(self) -> None:
        source = read_chapter("V5-C08")
        opening = opening_block(source)
        self.assertIn("先按需要回看前七章的定义域和保证", opening)
        self.assertNotIn("第8章", source)
        self.assertNotIn(r"\GlobalChapterRef{37}{5}{8}", source)

    def test_targeted_volume_five_navigation_has_no_bare_local_chapter_number(self) -> None:
        targets = {
            "V5-C01/CH36": anchored_block(read_chapter("V5-C01"), "struct:V5-C01-CH36"),
            "V5-C03/opening": opening_block(read_chapter("V5-C03")),
            "V5-C03/CH02": anchored_block(read_chapter("V5-C03"), "struct:V5-C03-CH02"),
            "V5-C03/CH04": anchored_block(read_chapter("V5-C03"), "struct:V5-C03-CH04"),
            "V5-C04/opening": opening_block(read_chapter("V5-C04")),
            "V5-C04/CH02": anchored_block(read_chapter("V5-C04"), "struct:V5-C04-CH02"),
            "V5-C04/CH04": anchored_block(read_chapter("V5-C04"), "struct:V5-C04-CH04"),
            "V5-C04/CH36": anchored_block(read_chapter("V5-C04"), "struct:V5-C04-CH36"),
            "V5-C06/opening": opening_block(read_chapter("V5-C06")),
            "V5-C06/CH04": anchored_block(read_chapter("V5-C06"), "struct:V5-C06-CH04"),
            "V5-C06/CH36": anchored_block(read_chapter("V5-C06"), "struct:V5-C06-CH36"),
            "V5-C07/CH36": anchored_block(read_chapter("V5-C07"), "struct:V5-C07-CH36"),
            "V5-C08/opening": opening_block(read_chapter("V5-C08")),
        }
        bare_local_chapter = re.compile(r"(?<!册)第[1-8]章")
        offenders = {
            name: bare_local_chapter.findall(block)
            for name, block in targets.items()
            if bare_local_chapter.search(block)
        }
        self.assertEqual(offenders, {}, f"第五册目标位置仍有裸局部章号: {offenders}")


if __name__ == "__main__":
    unittest.main()

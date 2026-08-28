from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAWINGS = ROOT / "绘图源码"
LECTURES = ROOT / "讲义源码"


@dataclass(frozen=True)
class FigureTarget:
    issue_id: str
    label: str
    drawing: Path
    chapter: Path


TARGETS = (
    FigureTarget("FIG-001", "fig:V1-C01-language-flow", Path("第01册_数学基础与统计学习基本理论/V1-C01/fig_v1_c01_language_flow.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C01.tex")),
    FigureTarget("FIG-002", "fig:V1-C03-gradient-contour", Path("第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C03.tex")),
    FigureTarget("FIG-003", "fig:V1-C04-cdf", Path("第01册_数学基础与统计学习基本理论/V1-C04/fig_v1_c04_cdf.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C04.tex")),
    FigureTarget("FIG-004", "fig:V1-C05-gaussian", Path("第01册_数学基础与统计学习基本理论/V1-C05/fig_v1_c05_gaussian.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C05.tex")),
    FigureTarget("FIG-005", "fig:V1-C06-binary-entropy", Path("第01册_数学基础与统计学习基本理论/V1-C06/fig_v1_c06_binary_entropy.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C06.tex")),
    FigureTarget("FIG-006", "fig:V1-C07-convex-set", Path("第01册_数学基础与统计学习基本理论/V1-C07/fig_v1_c07_convex_set.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C07.tex")),
    FigureTarget("FIG-007", "fig:V1-C08-coordinate", Path("第01册_数学基础与统计学习基本理论/V1-C08/fig_v1_c08_coordinate.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C08.tex")),
    FigureTarget("FIG-008", "fig:V1-C09-learning-loop", Path("第01册_数学基础与统计学习基本理论/V1-C09/fig_v1_c09_learning_loop.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C09.tex")),
    FigureTarget("FIG-009", "fig:V1-C10-complexity", Path("第01册_数学基础与统计学习基本理论/V1-C10/fig_v1_c10_complexity.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C10.tex")),
    FigureTarget("FIG-010", "fig:V1-C11-tagging", Path("第01册_数学基础与统计学习基本理论/V1-C11/fig_v1_c11_tagging.tex"), Path("第01册_数学基础与统计学习基本理论/chapters/V1-C11.tex")),
)


def uncommented(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


class FigureFontContractTests(unittest.TestCase):
    def test_batch_identity_is_exact(self) -> None:
        self.assertEqual(len(TARGETS), 10)
        self.assertEqual(
            [target.issue_id for target in TARGETS],
            [f"FIG-{number:03d}" for number in range(1, 11)],
        )
        self.assertEqual(
            {target.chapter.stem for target in TARGETS},
            {"V1-C01", "V1-C03", "V1-C04", "V1-C05", "V1-C06", "V1-C07", "V1-C08", "V1-C09", "V1-C10", "V1-C11"},
        )

    def test_labels_and_chapter_inputs_are_preserved(self) -> None:
        for target in TARGETS:
            drawing = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            chapter = uncommented((LECTURES / target.chapter).read_text(encoding="utf-8"))
            relative_input = "../../绘图源码/" + target.drawing.as_posix()
            with self.subTest(issue=target.issue_id):
                self.assertEqual(drawing.count(rf"\label{{{target.label}}}"), 1)
                self.assertIn(rf"\input{{{relative_input}}}", chapter)
                self.assertRegex(
                    chapter,
                    rf"\\(?:ref|cref|Cref|autoref)\{{{re.escape(target.label)}\}}",
                )

    def test_explicit_node_font_floor_is_at_least_9pt(self) -> None:
        node_font = re.compile(
            r"every\s+node/\.style\s*=\s*\{[^{}]*font\s*=\s*"
            r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}\\selectfont[^{}]*\}",
            flags=re.DOTALL,
        )
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            matches = node_font.findall(source)
            with self.subTest(issue=target.issue_id):
                self.assertEqual(len(matches), 1)
                point_size, baseline_skip = map(float, matches[0])
                self.assertGreaterEqual(point_size, 9.0)
                self.assertGreaterEqual(baseline_skip, point_size)

    def test_pgfplots_ticks_labels_and_legend_are_explicit(self) -> None:
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            if r"\begin{axis}" not in source:
                continue
            with self.subTest(issue=target.issue_id):
                self.assertRegex(source, r"tick label style\s*=\s*\{font=\\fontsize\{[0-9.]+pt\}")
                self.assertRegex(source, r"label style\s*=\s*\{font=\\fontsize\{[0-9.]+pt\}")
                if r"\addlegendentry" in source:
                    self.assertRegex(source, r"legend style\s*=\s*\{font=\\fontsize\{[0-9.]+pt\}")

    def test_no_forbidden_font_or_box_scaling_workaround(self) -> None:
        forbidden = re.compile(r"\\(?:tiny|scriptsize|footnotesize|resizebox|scalebox)\b")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            with self.subTest(issue=target.issue_id):
                self.assertIsNone(forbidden.search(source))

    def test_no_hidden_sub_9pt_override(self) -> None:
        explicit_sizes = re.compile(r"\\fontsize\{([0-9.]+)pt\}")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            sizes = [float(value) for value in explicit_sizes.findall(source)]
            with self.subTest(issue=target.issue_id):
                self.assertTrue(sizes)
                self.assertGreaterEqual(min(sizes), 9.0)


if __name__ == "__main__":
    unittest.main()

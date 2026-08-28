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
    FigureTarget("FIG-011", "fig:V2-C01-separator", Path("第02册_基础监督学习方法/V2-C01/fig_v2_c01_separator.tex"), Path("第02册_基础监督学习方法/chapters/V2-C01.tex")),
    FigureTarget("FIG-012", "fig:V2-C02-lp-balls", Path("第02册_基础监督学习方法/V2-C02/fig_v2_c02_lp_balls.tex"), Path("第02册_基础监督学习方法/chapters/V2-C02.tex")),
    FigureTarget("FIG-013", "fig:V2-C02-kd-tree", Path("第02册_基础监督学习方法/V2-C02/fig_v2_c02_kd_tree.tex"), Path("第02册_基础监督学习方法/chapters/V2-C02.tex")),
    FigureTarget("FIG-014", "fig:V2-C03-star", Path("第02册_基础监督学习方法/V2-C03/fig_v2_c03_star.tex"), Path("第02册_基础监督学习方法/chapters/V2-C03.tex")),
    FigureTarget("FIG-015", "fig:V2-C04-tree-partition", Path("第02册_基础监督学习方法/V2-C04/fig_v2_c04_tree_partition.tex"), Path("第02册_基础监督学习方法/chapters/V2-C04.tex")),
    FigureTarget("FIG-016", "fig:V3-C01-simplex", Path("第03册_优化模型与序列模型/V3-C01/fig_v3_c01_simplex.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C01.tex")),
    FigureTarget("FIG-017", "fig:V3-C02-margin", Path("第03册_优化模型与序列模型/V3-C02/fig_v3_c02_margin.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C02.tex")),
    FigureTarget("FIG-018", "fig:V3-C03-adaboost-loop", Path("第03册_优化模型与序列模型/V3-C03/fig_v3_c03_adaboost_loop.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C03.tex")),
    FigureTarget("FIG-019", "fig:V3-C04-bound", Path("第03册_优化模型与序列模型/V3-C04/fig_v3_c04_bound.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C04.tex")),
    FigureTarget("FIG-020", "fig:V3-C05-lattice", Path("第03册_优化模型与序列模型/V3-C05/fig_v3_c05_lattice.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C05.tex")),
)


def uncommented(text: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


class FigureFontContractTests(unittest.TestCase):
    def test_batch_identity_is_exact(self) -> None:
        self.assertEqual(len(TARGETS), 10)
        self.assertEqual(
            {target.issue_id for target in TARGETS},
            {f"FIG-{number:03d}" for number in range(11, 21)},
        )

    def test_labels_and_chapter_inputs_are_preserved(self) -> None:
        for target in TARGETS:
            drawing_path = DRAWINGS / target.drawing
            chapter_path = LECTURES / target.chapter
            drawing = uncommented(drawing_path.read_text(encoding="utf-8"))
            chapter = uncommented(chapter_path.read_text(encoding="utf-8"))
            relative_input = "../../绘图源码/" + target.drawing.as_posix()
            with self.subTest(issue=target.issue_id):
                self.assertEqual(drawing.count(rf"\label{{{target.label}}}"), 1)
                self.assertIn(rf"\input{{{relative_input}}}", chapter)
                self.assertIn(rf"\ref{{{target.label}}}", chapter)

    def test_explicit_node_font_floor_is_at_least_8_5pt(self) -> None:
        font_pattern = re.compile(
            r"every\s+node/\.style\s*=\s*\{[^{}]*font\s*=\s*"
            r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}\\selectfont[^{}]*\}",
            flags=re.DOTALL,
        )
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            matches = font_pattern.findall(source)
            with self.subTest(issue=target.issue_id):
                self.assertEqual(len(matches), 1, "each target must declare one explicit every-node font contract")
                point_size, baseline_skip = map(float, matches[0])
                self.assertGreaterEqual(point_size, 8.5)
                self.assertGreaterEqual(baseline_skip, point_size)

    def test_no_forbidden_font_or_box_scaling_workaround(self) -> None:
        forbidden = re.compile(r"\\(?:tiny|scriptsize|footnotesize|resizebox|scalebox)\b")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            with self.subTest(issue=target.issue_id):
                self.assertIsNone(forbidden.search(source))

    def test_no_hidden_sub_8_5pt_override(self) -> None:
        explicit_sizes = re.compile(r"\\fontsize\{([0-9.]+)pt\}")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            sizes = [float(value) for value in explicit_sizes.findall(source)]
            with self.subTest(issue=target.issue_id):
                self.assertTrue(sizes)
                self.assertGreaterEqual(min(sizes), 8.5)


if __name__ == "__main__":
    unittest.main()

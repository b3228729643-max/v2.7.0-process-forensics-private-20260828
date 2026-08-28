from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAWINGS = ROOT / "绘图源码"
LECTURES = ROOT / "讲义源码"


@dataclass(frozen=True)
class Sample:
    volume: int
    chapter: str
    drawing: str
    label: str


SAMPLES = (
    Sample(1, "V1-C01", "fig_v1_c01_language_flow.tex", "fig:V1-C01-language-flow"),
    Sample(1, "V1-C02", "fig_v1_c02_projection.tex", "fig:V1-C02-projection"),
    Sample(1, "V1-C03", "fig_v1_c03_gradient_contour.tex", "fig:V1-C03-gradient-contour"),
    Sample(1, "V1-C04", "fig_v1_c04_cdf.tex", "fig:V1-C04-cdf"),
    Sample(2, "V2-C01", "fig_v2_c01_separator.tex", "fig:V2-C01-separator"),
    Sample(2, "V2-C02", "fig_v2_c02_lp_balls.tex", "fig:V2-C02-lp-balls"),
    Sample(2, "V2-C03", "fig_v2_c03_star.tex", "fig:V2-C03-star"),
    Sample(2, "V2-C04", "fig_v2_c04_tree_partition.tex", "fig:V2-C04-tree-partition"),
    Sample(3, "V3-C01", "fig_v3_c01_simplex.tex", "fig:V3-C01-simplex"),
    Sample(3, "V3-C02", "fig_v3_c02_margin.tex", "fig:V3-C02-margin"),
    Sample(3, "V3-C03", "fig_v3_c03_adaboost_loop.tex", "fig:V3-C03-adaboost-loop"),
    Sample(3, "V3-C04", "fig_v3_c04_bound.tex", "fig:V3-C04-bound"),
    Sample(4, "V4-C01", "fig_v4_c01_three_structures.tex", "fig:V4-C01-three-structures"),
    Sample(4, "V4-C02", "fig_v4_c02_dendrogram.tex", "fig:V4-C02-dendrogram"),
    Sample(4, "V4-C03", "fig_v4_c03_svd_geometry.tex", "fig:V4-C03-svd-geometry"),
    Sample(4, "V4-C04", "fig_v4_c04_ellipse.tex", "fig:V4-C04-ellipse"),
    Sample(5, "V5-C01", "fig_v5_c01_dependency_graph.tex", "fig:V5-C01-dependency"),
    Sample(5, "V5-C01", "fig_v5_c01_transition_graph.tex", "fig:V5-C01-transition-graph"),
    Sample(5, "V5-C01", "fig_v5_c01_return_time.tex", "fig:V5-C01-return-time"),
    Sample(5, "V5-C01", "fig_v5_c01_stationary_fixed_point.tex", "fig:V5-C01-stationary-fixed-point"),
)

VOLUME_NAMES = {
    1: "第01册_数学基础与统计学习基本理论",
    2: "第02册_基础监督学习方法",
    3: "第03册_优化模型与序列模型",
    4: "第04册_无监督学习与矩阵分解",
    5: "第05册_采样方法主题模型与图排序",
}


class FigureCaptionBodyContractTests(unittest.TestCase):
    def test_sample_is_stratified_twenty_figures(self) -> None:
        self.assertEqual(len(SAMPLES), 20)
        self.assertEqual(len({sample.label for sample in SAMPLES}), 20)
        self.assertEqual(
            {volume: sum(sample.volume == volume for sample in SAMPLES) for volume in range(1, 6)},
            {1: 4, 2: 4, 3: 4, 4: 4, 5: 4},
        )

    def test_sample_labels_inputs_and_references_are_preserved(self) -> None:
        for sample in SAMPLES:
            volume = VOLUME_NAMES[sample.volume]
            drawing_path = DRAWINGS / volume / sample.chapter / sample.drawing
            chapter_path = LECTURES / volume / "chapters" / f"{sample.chapter}.tex"
            drawing = drawing_path.read_text(encoding="utf-8")
            chapter = chapter_path.read_text(encoding="utf-8")
            input_command = rf"\input{{../../绘图源码/{volume}/{sample.chapter}/{sample.drawing}}}"
            with self.subTest(label=sample.label):
                self.assertEqual(drawing.count(rf"\label{{{sample.label}}}"), 1)
                self.assertIn(r"\caption{", drawing)
                self.assertEqual(chapter.count(input_command), 1)
                self.assertRegex(chapter, rf"\\(?:ref|cref|Cref|autoref)\{{{re.escape(sample.label)}\}}")

    def test_post_figure_body_avoids_legacy_caption_restatement_openers(self) -> None:
        for sample in SAMPLES:
            volume = VOLUME_NAMES[sample.volume]
            chapter_path = LECTURES / volume / "chapters" / f"{sample.chapter}.tex"
            chapter = chapter_path.read_text(encoding="utf-8")
            input_command = rf"\input{{../../绘图源码/{volume}/{sample.chapter}/{sample.drawing}}}"
            tail = chapter.split(input_command, maxsplit=1)[1][:900]
            legacy = re.compile(
                rf"(?:\\[cC]ref\{{{re.escape(sample.label)}\}}|"
                rf"图\\ref\{{{re.escape(sample.label)}\}})\s*"
                r"(?:展示(?:了)?|显示|给出|说明)",
            )
            with self.subTest(label=sample.label):
                self.assertIsNone(legacy.search(tail))

    def test_global_legacy_quoted_restatement_template_is_removed(self) -> None:
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in LECTURES.rglob("V*-C*.tex")
        )
        self.assertNotRegex(corpus, r"\\[cC]ref\{[^}]+\}展示了“")


if __name__ == "__main__":
    unittest.main()

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
    FigureTarget("FIG-021", "fig:V3-C06-chain", Path("第03册_优化模型与序列模型/V3-C06/fig_v3_c06_chain.tex"), Path("第03册_优化模型与序列模型/chapters/V3-C06.tex")),
    FigureTarget("FIG-022", "fig:V4-C02-dendrogram", Path("第04册_无监督学习与矩阵分解/V4-C02/fig_v4_c02_dendrogram.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C02.tex")),
    FigureTarget("FIG-023", "fig:V4-C03-svd-geometry", Path("第04册_无监督学习与矩阵分解/V4-C03/fig_v4_c03_svd_geometry.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C03.tex")),
    FigureTarget("FIG-024", "fig:V4-C04-ellipse", Path("第04册_无监督学习与矩阵分解/V4-C04/fig_v4_c04_ellipse.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C04.tex")),
    FigureTarget("FIG-025", "fig:V4-C05-two-geometries", Path("第04册_无监督学习与矩阵分解/V4-C05/fig_v4_c05_two_geometries.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C05.tex")),
    FigureTarget("FIG-026", "fig:V4-C06-plsa-dag", Path("第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_plsa_dag.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C06.tex")),
    FigureTarget("FIG-027", "fig:V4-C06-simplex", Path("第04册_无监督学习与矩阵分解/V4-C06/fig_v4_c06_simplex.tex"), Path("第04册_无监督学习与矩阵分解/chapters/V4-C06.tex")),
    FigureTarget("FIG-028", "fig:V5-C01-transition-graph", Path("第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_transition_graph.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C01.tex")),
    FigureTarget("FIG-029", "fig:V5-C01-return-time", Path("第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_return_time.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C01.tex")),
    FigureTarget("FIG-030", "fig:V5-C01-stationary-fixed-point", Path("第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_stationary_fixed_point.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C01.tex")),
    FigureTarget("FIG-031", "fig:V5-C01-chain-properties", Path("第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_chain_properties.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C01.tex")),
    FigureTarget("FIG-032", "fig:V5-C01-random-walk", Path("第05册_采样方法主题模型与图排序/V5-C01/fig_v5_c01_random_walk.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C01.tex")),
    FigureTarget("FIG-033", "fig:V5-C02-mc-integral", Path("第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_mc_integral.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C02.tex")),
    FigureTarget("FIG-034", "fig:V5-C02-running-mean", Path("第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_running_mean.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C02.tex")),
    FigureTarget("FIG-035", "fig:V5-C02-weight-ess", Path("第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_weight_ess.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C02.tex")),
    FigureTarget("FIG-036", "fig:V5-C02-rmse-rate", Path("第05册_采样方法主题模型与图排序/V5-C02/fig_v5_c02_rmse_rate.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C02.tex")),
    FigureTarget("FIG-037", "fig:V5-C03-dependency", Path("第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_dependency_graph.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C03.tex")),
    FigureTarget("FIG-038", "fig:V5-C03-markov-chain-path", Path("第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_markov_chain_path.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C03.tex")),
    FigureTarget("FIG-039", "fig:V5-C03-mcmc-pipeline", Path("第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mcmc_pipeline.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C03.tex")),
    FigureTarget("FIG-040", "fig:V5-C03-mh-accept-reject", Path("第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_mh_accept_reject.tex"), Path("第05册_采样方法主题模型与图排序/chapters/V5-C03.tex")),
)


def uncommented(text: str) -> str:
    return "\n".join(
        re.split(r"(?<!\\)%", line, maxsplit=1)[0] for line in text.splitlines()
    )


class FigureFontContractTests(unittest.TestCase):
    def test_batch_identity_is_exact(self) -> None:
        self.assertEqual(len(TARGETS), 20)
        self.assertEqual(
            [target.issue_id for target in TARGETS],
            [f"FIG-{number:03d}" for number in range(21, 41)],
        )
        self.assertEqual(len({target.label for target in TARGETS}), 20)
        self.assertEqual(len({target.drawing for target in TARGETS}), 20)

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

    def test_pgfplots_ticks_labels_and_legends_are_explicit(self) -> None:
        axis_start = re.compile(r"\\begin\{(?:axis|loglogaxis)\}")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            if not axis_start.search(source):
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

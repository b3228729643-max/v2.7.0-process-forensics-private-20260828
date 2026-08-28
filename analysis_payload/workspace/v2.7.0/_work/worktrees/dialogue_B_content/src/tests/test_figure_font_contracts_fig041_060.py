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


VOLUME = "第05册_采样方法主题模型与图排序"
TARGETS = (
    FigureTarget("FIG-041", "fig:V5-C03-acceptance-function", Path(f"{VOLUME}/V5-C03/fig_v5_c03_acceptance_function.tex"), Path(f"{VOLUME}/chapters/V5-C03.tex")),
    FigureTarget("FIG-042", "fig:V5-C03-componentwise-sweep", Path(f"{VOLUME}/V5-C03/fig_v5_c03_componentwise_sweep.tex"), Path(f"{VOLUME}/chapters/V5-C03.tex")),
    FigureTarget("FIG-043", "fig:V5-C03-trace-running-mean", Path(f"{VOLUME}/V5-C03/fig_v5_c03_trace_running_mean.tex"), Path(f"{VOLUME}/chapters/V5-C03.tex")),
    FigureTarget("FIG-044", "fig:V5-C03-autocorrelation-ess", Path(f"{VOLUME}/V5-C03/fig_v5_c03_autocorrelation_ess.tex"), Path(f"{VOLUME}/chapters/V5-C03.tex")),
    FigureTarget("FIG-045", "fig:V5-C04-dependency-graph", Path(f"{VOLUME}/V5-C04/fig_v5_c04_dependency_graph.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-046", "fig:V5-C04-conditional-slice", Path(f"{VOLUME}/V5-C04/fig_v5_c04_conditional_slice.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-047", "fig:V5-C04-coordinate-sweep", Path(f"{VOLUME}/V5-C04/fig_v5_c04_coordinate_sweep.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-048", "fig:V5-C04-gibbs-axis-path", Path(f"{VOLUME}/V5-C04/fig_v5_c04_gibbs_axis_path.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-049", "fig:V5-C04-gibbs-vs-mh", Path(f"{VOLUME}/V5-C04/fig_v5_c04_gibbs_vs_mh.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-050", "fig:V5-C04-bivariate-normal-conditionals", Path(f"{VOLUME}/V5-C04/fig_v5_c04_bivariate_normal_conditionals.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-051", "fig:V5-C04-mixing-rho-comparison", Path(f"{VOLUME}/V5-C04/fig_v5_c04_mixing_rho_comparison.tex"), Path(f"{VOLUME}/chapters/V5-C04.tex")),
    FigureTarget("FIG-052", "fig:V5-C05-multinomial-counts", Path(f"{VOLUME}/V5-C05/fig_v5_c05_multinomial_counts.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-053", "fig:V5-C05-distribution-relations", Path(f"{VOLUME}/V5-C05/fig_v5_c05_distribution_relations.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-054", "fig:V5-C05-simplex-geometry", Path(f"{VOLUME}/V5-C05/fig_v5_c05_simplex_geometry.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-055", "fig:V5-C05-gamma-normalization", Path(f"{VOLUME}/V5-C05/fig_v5_c05_gamma_normalization.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-056", "fig:V5-C05-exponential-family-moments", Path(f"{VOLUME}/V5-C05/fig_v5_c05_exponential_family_moments.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-057", "fig:V5-C05-conjugate-update", Path(f"{VOLUME}/V5-C05/fig_v5_c05_conjugate_update.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-058", "fig:V5-C05-dirichlet-shape-atlas", Path(f"{VOLUME}/V5-C05/fig_v5_c05_dirichlet_shape_atlas.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-059", "fig:V5-C05-concentration-mean", Path(f"{VOLUME}/V5-C05/fig_v5_c05_concentration_mean.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
    FigureTarget("FIG-060", "fig:V5-C05-posterior-predictive", Path(f"{VOLUME}/V5-C05/fig_v5_c05_posterior_predictive.tex"), Path(f"{VOLUME}/chapters/V5-C05.tex")),
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
            [f"FIG-{number:03d}" for number in range(41, 61)],
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

    def test_every_pgfplots_axis_has_explicit_font_contracts(self) -> None:
        axis_start = re.compile(r"\\begin\{(?:axis|loglogaxis)\}")
        explicit_size = r"font=\\fontsize\{[0-9.]+pt\}"
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            axis_count = len(axis_start.findall(source))
            if axis_count == 0:
                continue
            with self.subTest(issue=target.issue_id):
                self.assertGreaterEqual(len(re.findall(rf"tick label style\s*=\s*\{{{explicit_size}", source)), axis_count)
                self.assertGreaterEqual(len(re.findall(rf"label style\s*=\s*\{{{explicit_size}", source)), axis_count)
                if r"\addlegendentry" in source:
                    self.assertRegex(source, rf"legend style\s*=\s*\{{[^}}]*{explicit_size}")
                title_count = len(re.findall(r"(?<!style)\btitle\s*=", source))
                if title_count:
                    self.assertGreaterEqual(len(re.findall(rf"title style\s*=\s*\{{{explicit_size}", source)), title_count)

    def test_no_forbidden_font_or_box_scaling_workaround(self) -> None:
        forbidden = re.compile(r"\\(?:tiny|scriptsize|footnotesize|small|resizebox|scalebox)\b")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            with self.subTest(issue=target.issue_id):
                self.assertIsNone(forbidden.search(source))

    def test_every_font_assignment_starts_with_an_explicit_size(self) -> None:
        implicit_font = re.compile(r"\bfont\s*=\s*(?!\\fontsize\{)")
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            with self.subTest(issue=target.issue_id):
                self.assertIsNone(implicit_font.search(source))

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

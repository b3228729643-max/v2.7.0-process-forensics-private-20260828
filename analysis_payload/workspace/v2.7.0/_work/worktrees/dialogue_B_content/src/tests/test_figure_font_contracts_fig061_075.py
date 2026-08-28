from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAWINGS = ROOT / "绘图源码"
LECTURES = ROOT / "讲义源码"
VOLUME = "第05册_采样方法主题模型与图排序"


@dataclass(frozen=True)
class FigureTarget:
    issue_id: str
    label: str
    drawing: Path
    chapter: Path


TARGETS = (
    FigureTarget("FIG-061", "fig:V5-C06-plate-graph", Path(f"{VOLUME}/V5-C06/fig_v5_c06_plate_graph.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-062", "fig:V5-C06-generative-process", Path(f"{VOLUME}/V5-C06/fig_v5_c06_generative_process.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-063", "fig:V5-C06-collapsed-gibbs-counts", Path(f"{VOLUME}/V5-C06/fig_v5_c06_collapsed_gibbs_counts.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-064", "fig:V5-C06-mean-field-graph", Path(f"{VOLUME}/V5-C06/fig_v5_c06_mean_field_graph.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-065", "fig:V5-C06-variational-updates", Path(f"{VOLUME}/V5-C06/fig_v5_c06_variational_updates.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-066", "fig:V5-C06-method-comparison", Path(f"{VOLUME}/V5-C06/fig_v5_c06_method_comparison.tex"), Path(f"{VOLUME}/chapters/V5-C06.tex")),
    FigureTarget("FIG-067", "fig:V5-C07-dependency", Path(f"{VOLUME}/V5-C07/dependency_graph.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-068", "fig:V5-C07-periodic-dangling", Path(f"{VOLUME}/V5-C07/periodic_dangling_failures.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-069", "fig:V5-C07-inbound-contribution", Path(f"{VOLUME}/V5-C07/inbound_contribution.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-070", "fig:V5-C07-damping-teleportation", Path(f"{VOLUME}/V5-C07/damping_teleportation.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-071", "fig:V5-C07-simplex-contraction", Path(f"{VOLUME}/V5-C07/simplex_stationary_contraction.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-072", "fig:V5-C07-rank-trajectory", Path(f"{VOLUME}/V5-C07/numerical_rank_trajectory.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-073", "fig:V5-C07-power-flow", Path(f"{VOLUME}/V5-C07/power_method_flow_convergence.tex"), Path(f"{VOLUME}/chapters/V5-C07.tex")),
    FigureTarget("FIG-074", "fig:V5-C08-selection-map", Path(f"{VOLUME}/V5-C08/method_selection_decision_map.tex"), Path(f"{VOLUME}/chapters/V5-C08.tex")),
    FigureTarget("FIG-075", "fig:V5-C08-course-map", Path(f"{VOLUME}/V5-C08/full_course_synthesis_map.tex"), Path(f"{VOLUME}/chapters/V5-C08.tex")),
)


def uncommented(text: str) -> str:
    return "\n".join(
        re.split(r"(?<!\\)%", line, maxsplit=1)[0] for line in text.splitlines()
    )


class FigureFontContractTests(unittest.TestCase):
    def test_batch_identity_is_exact(self) -> None:
        self.assertEqual(len(TARGETS), 15)
        self.assertEqual(
            [target.issue_id for target in TARGETS],
            [f"FIG-{number:03d}" for number in range(61, 76)],
        )
        self.assertEqual(len({target.label for target in TARGETS}), 15)
        self.assertEqual(len({target.drawing for target in TARGETS}), 15)

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

    def test_each_tikz_picture_has_an_explicit_9pt_node_contract(self) -> None:
        node_font = re.compile(
            r"every\s+node/\.style\s*=\s*\{[^{}]*font\s*=\s*"
            r"\\fontsize\{([0-9.]+)pt\}\{([0-9.]+)pt\}\\selectfont[^{}]*\}",
            flags=re.DOTALL,
        )
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            tikz_count = source.count(r"\begin{tikzpicture}")
            matches = node_font.findall(source)
            with self.subTest(issue=target.issue_id):
                self.assertGreater(tikz_count, 0)
                self.assertEqual(len(matches), tikz_count)
                for point_size, baseline_skip in matches:
                    self.assertGreaterEqual(float(point_size), 9.0)
                    self.assertGreaterEqual(float(baseline_skip), float(point_size))

    def test_pgfplots_axes_have_explicit_font_contracts_if_present(self) -> None:
        axis_start = re.compile(r"\\begin\{(?:axis|loglogaxis)\}")
        nine_pt = r"font=\\fontsize\{(?:9(?:\.0)?)pt\}"
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            axis_count = len(axis_start.findall(source))
            if axis_count == 0:
                continue
            with self.subTest(issue=target.issue_id):
                self.assertGreaterEqual(len(re.findall(rf"tick label style\s*=\s*\{{{nine_pt}", source)), axis_count)
                self.assertGreaterEqual(len(re.findall(rf"label style\s*=\s*\{{{nine_pt}", source)), axis_count)
                if r"\addlegendentry" in source:
                    self.assertRegex(source, rf"legend style\s*=\s*\{{[^}}]*{nine_pt}")

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

    def test_local_environment_delimiters_remain_balanced(self) -> None:
        for target in TARGETS:
            source = uncommented((DRAWINGS / target.drawing).read_text(encoding="utf-8"))
            with self.subTest(issue=target.issue_id):
                for environment in ("figure", "tikzpicture", "scope"):
                    self.assertEqual(
                        source.count(rf"\begin{{{environment}}}"),
                        source.count(rf"\end{{{environment}}}"),
                    )


if __name__ == "__main__":
    unittest.main()

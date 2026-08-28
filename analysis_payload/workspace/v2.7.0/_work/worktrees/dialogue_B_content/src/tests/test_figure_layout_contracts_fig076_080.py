from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAWINGS = ROOT / "绘图源码"
LECTURES = ROOT / "讲义源码"
V1 = "第01册_数学基础与统计学习基本理论"
V5 = "第05册_采样方法主题模型与图排序"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class FigureLayoutContractTests(unittest.TestCase):
    def test_fig076_cdf_uses_at_least_sixty_percent_body_width(self) -> None:
        source = read(DRAWINGS / V1 / "V1-C04" / "fig_v1_c04_cdf.tex")
        match = re.search(r"\\begin\{tikzpicture\}\[x=([0-9.]+)cm", source)
        self.assertIsNotNone(match)
        # The plotted horizontal span is 5.4 x-units; 1.85 cm gives 9.99 cm,
        # exceeding 60% of the 15.5 cm body width without scaling text.
        self.assertGreaterEqual(float(match.group(1)) * 5.4, 9.3)
        self.assertIn(r"every node/.style={font=\fontsize{9.5pt}{11.4pt}\selectfont}", source)
        self.assertNotRegex(source, r"\\(?:resizebox|scalebox|tiny|scriptsize|footnotesize)\b")

    def test_fig077_monte_carlo_plot_width_and_font_floor(self) -> None:
        source = read(DRAWINGS / V5 / "V5-C02" / "fig_v5_c02_mc_integral.tex")
        width = re.search(r"width=([0-9.]+)\\linewidth", source)
        self.assertIsNotNone(width)
        self.assertGreaterEqual(float(width.group(1)), 0.60)
        self.assertIn(r"every node/.style={font=\fontsize{9.5pt}{11.4pt}\selectfont}", source)
        self.assertGreaterEqual(source.count(r"font=\fontsize{9.5pt}{11.4pt}\selectfont"), 3)

    def test_fig078_lda_process_has_a_wide_explicit_9pt_layout(self) -> None:
        source = read(DRAWINGS / V5 / "V5-C06" / "fig_v5_c06_generative_process.tex")
        formula_width = re.search(r"formula/\.style=\{[^}]*text width=([0-9.]+)mm", source, re.DOTALL)
        self.assertIsNotNone(formula_width)
        self.assertGreaterEqual(float(formula_width.group(1)), 93.0)
        self.assertIn(r"every node/.style={font=\fontsize{9.5pt}{11.4pt}\selectfont", source)
        self.assertNotRegex(source, r"\\(?:resizebox|scalebox|tiny|scriptsize|footnotesize)\b")

    def test_fig079_flow_uses_font_line_and_terminal_shape_contracts(self) -> None:
        source = read(DRAWINGS / V5 / "V5-C02" / "fig_v5_c02_rejection_flow.tex")
        self.assertIn(r"every node/.style={font=\fontsize{9.5pt}{11.4pt}\selectfont", source)
        line_width = re.search(r"arr/\.style=\{[^}]*line width=([0-9.]+)pt", source)
        self.assertIsNotNone(line_width)
        self.assertGreaterEqual(float(line_width.group(1)), 0.6)
        for style, shape in (("success", "rounded corners"), ("budgetstop", "ellipse"), ("failure", "double")):
            self.assertRegex(source, rf"{style}/\.style=\{{[^}}]*{shape}")
        for phrase in ("成功出口", "预算停止", "异常出口", "普通拒绝"):
            self.assertIn(phrase, source)
        self.assertNotRegex(source, r"\\(?:resizebox|scalebox|tiny|scriptsize|footnotesize|small)\b")

    def test_fig079_envelope_and_flow_are_page_separated(self) -> None:
        chapter = read(LECTURES / V5 / "chapters" / "V5-C02.tex")
        pattern = (
            r"fig_v5_c02_rejection_envelope\.tex\}\s*"
            r"\\clearpage\s*"
            r"\\input\{[^\n]*fig_v5_c02_rejection_flow\.tex\}"
        )
        self.assertRegex(chapter, pattern)

    def test_fig080_declares_three_main_figures_and_separates_67_68(self) -> None:
        chapter = read(LECTURES / V5 / "chapters" / "V5-C07.tex")
        for label in (
            "fig:V5-C07-periodic-dangling",
            "fig:V5-C07-damping-teleportation",
            "fig:V5-C07-power-flow",
        ):
            self.assertGreaterEqual(chapter.count(label), 2)
        self.assertIn("三张主图", chapter)
        self.assertIn("小型数值例子", chapter)
        self.assertRegex(
            chapter,
            r"(?s)numerical_rank_trajectory\.tex\}.*?\\clearpage.*?"
            r"\\input\{[^\n]*power_method_flow_convergence\.tex\}",
        )

    def test_fig080_all_six_figures_retain_the_9pt_floor(self) -> None:
        names = (
            "periodic_dangling_failures.tex",
            "inbound_contribution.tex",
            "damping_teleportation.tex",
            "simplex_stationary_contraction.tex",
            "numerical_rank_trajectory.tex",
            "power_method_flow_convergence.tex",
        )
        for name in names:
            with self.subTest(name=name):
                source = read(DRAWINGS / V5 / "V5-C07" / name)
                sizes = [float(size) for size in re.findall(r"\\fontsize\{([0-9.]+)pt\}", source)]
                self.assertTrue(sizes)
                self.assertGreaterEqual(min(sizes), 9.0)

    def test_fig080_numerical_trajectory_is_pinned_to_the_example(self) -> None:
        source = read(DRAWINGS / V5 / "V5-C07" / "numerical_rank_trajectory.tex")
        self.assertIn(r"\begin{figure}[H]", source)


if __name__ == "__main__":
    unittest.main()

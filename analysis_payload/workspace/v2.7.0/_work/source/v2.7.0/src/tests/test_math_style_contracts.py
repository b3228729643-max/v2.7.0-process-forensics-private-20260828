"""Independent static contracts for MATH-002..MATH-008 and STYLE-001."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "讲义源码"

CHAPTERS = {
    "V1-C04": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C04.tex",
    "V1-C05": SOURCE_ROOT / "第01册_数学基础与统计学习基本理论" / "chapters" / "V1-C05.tex",
    "V4-C03": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C03.tex",
    "V4-C04": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C04.tex",
    "V4-C05": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C05.tex",
    "V5-C07": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C07.tex",
    "V5-C08": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C08.tex",
}


def read(chapter: str) -> str:
    return CHAPTERS[chapter].read_text(encoding="utf-8")


def between(source: str, start_marker: str, end_marker: str) -> str:
    start = source.index(start_marker)
    end = source.index(end_marker, start + len(start_marker))
    return source[start:end]


class MathAndStyleContractTests(unittest.TestCase):
    def test_math_002_separates_discrete_and_general_conditional_independence(self) -> None:
        source = read("V1-C04")
        block = between(
            source,
            r"\knowledgeanchor{PRE-PR-012}{条件独立}",
            r"\phantomsection\label{struct:V1-C04-CH16}",
        )
        self.assertIn(r"p_Z(z)>0", block)
        self.assertIn("正则条件分布", block)
        self.assertIn(r"P_{(X,Y)\mid Z=z}(A\times B)", block)
        self.assertRegex(block, r"P_Z\$几乎处处")
        self.assertIn(r"\textbf{离散例。}", block)
        self.assertIn(r"\textbf{连续例。}", block)
        self.assertIn(r"P(Z=z)=0", block)
        self.assertNotIn("对有正概率的 $z$ 成立", block)

    def test_math_003_disambiguates_multinomial_vectors_and_total_count(self) -> None:
        source = read("V1-C05")
        symbol_table = between(source, r"\begin{symboltablebox}", r"\end{symboltablebox}")
        block = between(
            source,
            r"\knowledgeanchor{PRE-PR-018}{多项分布}",
            r"\phantomsection\label{struct:V1-C05-CH12}",
        )
        self.assertIn(r"$\mathbf N,\mathbf n$", symbol_table)
        self.assertIn("多项分布的总试验数", symbol_table)
        self.assertIn(r"\mathbf N=(N_1,\ldots,N_K)", block)
        self.assertIn(r"\mathbf n=(n_1,\ldots,n_K)", block)
        self.assertIn(r"P(\mathbf N=\mathbf n)", block)
        self.assertIn(r"\sum_{k=1}^K n_k=n", block)
        self.assertNotIn(r"P(N=n)", source)

    def test_math_004_distinguishes_nondegenerate_density_from_degenerate_measure(self) -> None:
        block = between(
            read("V1-C05"),
            r"\knowledgeanchor{PRE-PR-033}{多元高斯分布}",
            r"\begin{lemma}[标准化]",
        )
        self.assertIn(r"\Sigma\succ0", block)
        self.assertIn("非退化分布", block)
        self.assertIn(r"\Sigma\succeq0", block)
        self.assertIn("高斯测度", block)
        self.assertIn("相对于$d$维Lebesgue测度没有密度", block)
        self.assertIn("秩亏二维反例", block)
        self.assertIn(r"\begin{bmatrix}1&1\\1&1\end{bmatrix}", block)
        self.assertIn(r"\operatorname{rank}(\Sigma)=1", block)
        self.assertIn(r"x_1=x_2", block)

    def test_math_005_includes_lossy_and_exact_lsa_rank_boundaries(self) -> None:
        source = read("V4-C05")
        block = between(
            source,
            r"\begin{definition}[潜在语义因子模型]",
            r"\end{definition}",
        )
        self.assertIn(r"r=\operatorname{rank}(X)", block)
        self.assertIn(r"1\le k\le r", block)
        self.assertIn(r"k<r", block)
        self.assertIn(r"X_k\ne X", block)
        self.assertIn(r"k=r", block)
        self.assertIn(r"X_r=U_r\Sigma_rV_r^T=X", block)
        self.assertIn(r"U_r\in\mathbb R^{m\times r}", block)
        self.assertIn(r"\index{潜在语义因子模型!模型定义}", source)
        self.assertIn(r"\index{截断SVD!潜在维数选择}", source)
        self.assertNotIn(r"1\le k<\operatorname{rank}(X)", block)

    def test_math_006_reserves_the_full_theorem_statement_locally(self) -> None:
        source = read("V4-C03")
        pattern = re.compile(
            r"\\Needspace\{(\d+)\\baselineskip\}\s*"
            r"\\begin\{theorem\}\[Eckart--Young--Mirsky低秩最优性\]"
        )
        match = pattern.search(source)
        self.assertIsNotNone(match, "定理26.2前缺少局部Needspace")
        assert match is not None
        self.assertGreaterEqual(int(match.group(1)), 12)

    def test_math_007_has_ordered_three_line_pca_dimension_bridge(self) -> None:
        source = read("V4-C04")
        block = between(
            source,
            r"\begin{keypointbox}[title=中心化--编码--重构三行桥接]",
            r"\end{keypointbox}",
        )
        contracts = (
            r"z=x-\mu\in\mathbb R^m",
            r"y=B^{\mathsf T}z\in\mathbb R^q",
            r"\widehat z=By=BB^{\mathsf T}z\in\mathbb R^m",
        )
        positions = [block.index(contract) for contract in contracts]
        self.assertEqual(positions, sorted(positions))
        self.assertIn(r"B\in\mathbb R^{m\times q}", block)
        self.assertIn(r"B^{\mathsf T}B=I_q", block)
        self.assertIn(r"\widehat x=\mu+\widehat z\in\mathbb R^m", block)

    def test_math_008_defines_pagerank_before_proving_uniqueness(self) -> None:
        source = read("V5-C07")
        definition = between(
            source,
            r"\begin{definition}[一般\PageRank{}矩阵与向量]",
            r"\end{definition}",
        )
        theorem_marker = r"\begin{theorem}[一般\PageRank{}的唯一性与几何收敛]"
        self.assertIn(r"若概率向量$\boldsymbol r$满足", definition)
        self.assertIn(r"则称$\boldsymbol r$为一般\PageRank{}向量", definition)
        self.assertNotIn("唯一满足", definition)
        self.assertNotIn("有唯一不动点", definition)
        self.assertLess(source.index(r"\end{definition}", source.index(definition)), source.index(theorem_marker))
        self.assertIn("有唯一不动点", source[source.index(theorem_marker) :])

    def test_style_001_uses_one_numbered_environment_for_every_chapter_37_solution(self) -> None:
        source = read("V5-C08")
        exercise_labels = re.findall(r"\\begin\{exercise\}\\label\{([^}]+)\}", source)
        solution_labels = re.findall(
            r"\\begin\{chapterexercisesolution\}\{([^}]+)\}", source
        )
        self.assertEqual(len(exercise_labels), 10)
        self.assertCountEqual(solution_labels, exercise_labels)
        self.assertNotRegex(source, r"\\textbf\{练习[^}]*?(?:完整解析|解析)\}")
        self.assertNotIn(r"\ExerciseSolutionTitle", source)


if __name__ == "__main__":
    unittest.main()

"""Static contracts for HEAD-001 through HEAD-013."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "讲义源码"


CHAPTERS = {
    "V2-C05": SOURCE_ROOT / "第02册_基础监督学习方法" / "chapters" / "V2-C05.tex",
    "V3-C01": SOURCE_ROOT / "第03册_优化模型与序列模型" / "chapters" / "V3-C01.tex",
    "V3-C02": SOURCE_ROOT / "第03册_优化模型与序列模型" / "chapters" / "V3-C02.tex",
    "V3-C03": SOURCE_ROOT / "第03册_优化模型与序列模型" / "chapters" / "V3-C03.tex",
    "V3-C06": SOURCE_ROOT / "第03册_优化模型与序列模型" / "chapters" / "V3-C06.tex",
    "V3-C07": SOURCE_ROOT / "第03册_优化模型与序列模型" / "chapters" / "V3-C07.tex",
    "V4-C01": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C01.tex",
    "V4-C02": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C02.tex",
    "V4-C03": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C03.tex",
    "V4-C05": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C05.tex",
    "V4-C06": SOURCE_ROOT / "第04册_无监督学习与矩阵分解" / "chapters" / "V4-C06.tex",
    "V5-C05": SOURCE_ROOT / "第05册_采样方法主题模型与图排序" / "chapters" / "V5-C05.tex",
}


def read_chapter(chapter: str) -> str:
    return CHAPTERS[chapter].read_text(encoding="utf-8")


def anchored_block(source: str, anchor: str) -> str:
    marker = rf"\phantomsection\label{{{anchor}}}"
    start = source.index(marker)
    next_anchor = source.find(r"\phantomsection\label{struct:", start + len(marker))
    return source[start:] if next_anchor == -1 else source[start:next_anchor]


class HeadContractTests(unittest.TestCase):
    def assert_method_limitation(
        self,
        chapter: str,
        anchor: str,
        semantic_start: str,
        error_anchor: str,
    ) -> None:
        source = read_chapter(chapter)
        block = anchored_block(source, anchor)
        self.assertIn(r"\begin{notapplicablebox}[title=\SLMethodLimitationsTitle]", block)
        self.assertNotIn(r"\begin{warningbox}", block)
        normalized = re.sub(r"\s+", "", block)
        self.assertIn(re.sub(r"\s+", "", semantic_start), normalized)
        error_block = anchored_block(source, error_anchor)
        self.assertIn(r"\begin{warningbox}", error_block)

    def test_head_001_logistic_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V2-C05",
            "struct:V2-C05-CH29",
            "原始特征上的模型只能产生线性分界",
            "struct:V2-C05-CH30",
        )

    def test_head_002_maximum_entropy_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V3-C01",
            "struct:V3-C01-CH29",
            "大量稀疏特征会带来高计算与存储成本",
            "struct:V3-C01-CH30",
        )

    def test_head_003_second_svm_box_is_method_limitations(self) -> None:
        self.assert_method_limitation(
            "V3-C02",
            "struct:V3-C02-CH29",
            "核矩阵带来二次存储与较高训练成本",
            "struct:V3-C02-CH30",
        )

    def test_head_004_boosting_limitations_precede_real_errors(self) -> None:
        self.assert_method_limitation(
            "V3-C03",
            "struct:V3-C03-CH30",
            "指数损失会持续放大难分样本和错标样本的影响",
            "struct:V3-C03-CH31",
        )

    def test_head_005_crf_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V3-C06",
            "struct:V3-C06-CH29",
            "一阶链难以表示长距离标签依赖",
            "struct:V3-C06-CH30",
        )

    def test_head_006_supervised_summary_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V3-C07",
            "struct:V3-C07-CH29",
            "有限验证不能证明模型在所有未来分布上可靠",
            "struct:V3-C07-CH30",
        )

    def test_head_007_unsupervised_exception_and_limitation_titles_match_content(self) -> None:
        source = read_chapter("V4-C01")
        abnormal = re.compile(
            r"\\begin\{notapplicablebox\}\[title=\\SLDegeneracyTitle\]\s*"
            r"若某次划分使训练集或验证集为空.*?"
            r"\\end\{notapplicablebox\}",
            re.DOTALL,
        )
        self.assertRegex(source, abnormal)
        self.assert_method_limitation(
            "V4-C01",
            "struct:V4-C01-CH29",
            "无标签准则通常不能唯一指定语义",
            "struct:V4-C01-CH30",
        )

    def test_head_008_clustering_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V4-C02",
            "struct:V4-C02-CH29",
            "层次聚类早期错误合并通常不能撤销",
            "struct:V4-C02-CH30",
        )

    def test_head_009_svd_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V4-C03",
            "struct:V4-C03-CH29",
            "SVD对异常值敏感",
            "struct:V4-C03-CH30",
        )

    def test_head_010_lsa_nmf_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V4-C05",
            "struct:V4-C05-CH29",
            "词袋表示丢失词序与否定结构",
            "struct:V4-C05-CH30",
        )

    def test_head_011_plsa_limitations_are_not_common_errors(self) -> None:
        self.assert_method_limitation(
            "V4-C06",
            "struct:V4-C06-CH29",
            "PLSA为每篇训练文档配置独立",
            "struct:V4-C06-CH30",
        )

    def test_head_012_complexity_box_has_its_own_precise_title(self) -> None:
        source = read_chapter("V5-C05")
        self.assertRegex(
            source,
            re.compile(
                r"\\begin\{notapplicablebox\}\[title=\\SLComplexityAssumptionsTitle\]\s*"
                r"类别索引访问、浮点加法和一次\$\\log\\Gamma\$求值按固定精度视为.*?"
                r"\\end\{notapplicablebox\}",
                re.DOTALL,
            ),
        )
        real_errors = anchored_block(source, "struct:V5-C05-CH30")
        self.assertIn(r"\textbf{常见错误。}", real_errors)

    def test_head_013_example_18_1_uses_standard_environment_without_manual_spacing(self) -> None:
        source = read_chapter("V3-C02")
        match = re.search(
            r"\\begin\{example\}\[([^]]+)\]\\label\{exm:V3-C02-kkt-state\}",
            source,
        )
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group(1), "一维软间隔状态判定")
        self.assertNotRegex(match.group(0), r"\\(?:hspace|kern|quad|qquad)|[\u00a0\u3000~]")


if __name__ == "__main__":
    unittest.main()

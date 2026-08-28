"""Tests for the project-wide G1 source auditor."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "qa" / "static_source_audit.py"
SPEC = importlib.util.spec_from_file_location("static_source_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


FIELDS = """
input={x}, output={最后合法 x 与诊断}, preconditions={x 合法},
initialization={初始化 k=0}, loop={有限循环}, update={原子更新 x},
domain={检查有限性}, failure={失败时保留最后合法值},
stop={有限扫描完成}, budget={由输入规模决定的有限工作量},
status={\\mathtt{completed} 或 \\mathtt{invalid\\_input}},
iterations={k 记录实际工作量}, diagnostics={返回最终诊断},
complexity={线性时间与常数工作空间}
""".strip()


def chapter(label: str, contract: bool = True, status: str | None = None) -> str:
    fields = FIELDS if status is None else FIELDS.replace(
        r"\mathtt{completed} 或 \mathtt{invalid\_input}", status
    )
    algorithm = rf"""
\begin{{algorithm}}[H]
\caption{{测试算法}}\label{{{label}}}
\KwIn{{x}}\KwOut{{最后合法 x、\mathtt{{status}} 与诊断}}
返回 x、\mathtt{{completed}} 与最终诊断\;
\end{{algorithm}}
"""
    wrapped = rf"\begin{{AlgorithmContract}}{{{fields}}}{algorithm}\end{{AlgorithmContract}}" if contract else algorithm
    return rf"\chapter{{测试章}}\label{{chap:{label}}}{wrapped}"


class StaticSourceAuditTests(unittest.TestCase):
    def make_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        chapters = root / "volume" / "chapters"
        chapters.mkdir(parents=True)
        for index in range(37):
            (chapters / f"C{index + 1:02d}.tex").write_text(
                chapter(f"alg:test-{index + 1}"), encoding="utf-8"
            )
        # The v2.7.0 authoritative inventory contains 66 numbered algorithms.
        extra = "".join(
            chapter(f"alg:extra-{index}").replace(r"\chapter{测试章}", "", 1)
            for index in range(29)
        )
        target = chapters / "C37.tex"
        target.write_text(target.read_text(encoding="utf-8") + extra, encoding="utf-8")
        return temp, root

    def test_valid_fixture_passes(self) -> None:
        temp, root = self.make_root()
        self.addCleanup(temp.cleanup)
        result = AUDIT.audit_source(root)
        self.assertTrue(result.passed, result.findings)
        self.assertEqual(result.chapters, 37)
        self.assertEqual(result.algorithms, 66)
        self.assertEqual(result.contracted_algorithms, 66)

    def test_missing_contract_is_reported(self) -> None:
        temp, root = self.make_root()
        self.addCleanup(temp.cleanup)
        target = root / "volume" / "chapters" / "C01.tex"
        target.write_text(chapter("alg:test-1", contract=False), encoding="utf-8")
        result = AUDIT.audit_source(root)
        self.assertIn("algorithm_missing_contract", {item.code for item in result.findings})

    def test_duplicate_label_and_forbidden_sizing_are_reported(self) -> None:
        temp, root = self.make_root()
        self.addCleanup(temp.cleanup)
        target = root / "volume" / "chapters" / "C02.tex"
        target.write_text(target.read_text(encoding="utf-8") + r"\tiny\label{alg:test-1}", encoding="utf-8")
        result = AUDIT.audit_source(root)
        codes = {item.code for item in result.findings}
        self.assertIn("duplicate_label", codes)
        self.assertIn("forbidden_sizing", codes)

    def test_nonstandard_status_is_reported(self) -> None:
        temp, root = self.make_root()
        self.addCleanup(temp.cleanup)
        target = root / "volume" / "chapters" / "C01.tex"
        target.write_text(chapter("alg:test-1", status=r"\mathtt{success}"), encoding="utf-8")
        result = AUDIT.audit_source(root)
        self.assertIn("contract_status_invalid", {item.code for item in result.findings})

    def test_commented_labels_and_algorithms_are_ignored(self) -> None:
        temp, root = self.make_root()
        self.addCleanup(temp.cleanup)
        target = root / "volume" / "chapters" / "C01.tex"
        target.write_text(
            "% \\label{alg:test-2} \\begin{algorithm} \\tiny\n"
            + target.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        result = AUDIT.audit_source(root)
        self.assertTrue(result.passed, result.findings)
        self.assertEqual(result.algorithms, 66)


if __name__ == "__main__":
    unittest.main(verbosity=2)

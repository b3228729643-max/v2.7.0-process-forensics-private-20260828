"""Static contract tests for the bounded chapter 16--21 algorithm batch."""

from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "讲义源码" / "第02册_基础监督学习方法" / "chapters"
V3 = ROOT / "讲义源码" / "第03册_优化模型与序列模型" / "chapters"

FIELDS = {
    "input",
    "output",
    "preconditions",
    "initialization",
    "loop",
    "update",
    "domain",
    "failure",
    "stop",
    "budget",
    "status",
    "iterations",
    "diagnostics",
    "complexity",
}

ALLOWED_STATUSES = {
    "completed",
    "converged",
    "budget_stop",
    "invalid_input",
    "numerical_failure",
    "line_search_failed",
    "random_source_failure",
}


@dataclass(frozen=True)
class Case:
    issue_id: str
    volume: int
    filename: str
    label: str
    expected_statuses: frozenset[str]
    iteration_tokens: tuple[str, ...]
    semantic_tokens: tuple[str, ...]


CASES = (
    Case("ALG-C16-1", 2, "V2-C05.tex", "alg:V2-C05-newton",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"}),
         (r"t_{\rm done}", r"s_{\rm done}", r"\ell_{\rm done}"), ("原子提交", "最后合法")),
    Case("ALG-C17-1", 3, "V3-C01.tex", "alg:V3-C01-bfgs",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"}),
         (r"k_{\rm done}", r"\ell_{\rm done}", r"c_{\rm reset}"), ("原子提交", "强Wolfe")),
    Case("ALG-C17-2", 3, "V3-C01.tex", "alg:V3-C01-iis",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"s_{\rm done}", r"q_{\rm done}"), ("原子提交", "支撑冲突")),
    Case("ALG-C18-1", 3, "V3-C02.tex", "alg:V3-C02-smo",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"s_{\rm done}", r"u_{\rm done}", r"p_{\rm done}"), ("原子提交", "KKT")),
    Case("ALG-C19-1", 3, "V3-C03.tex", "alg:V3-C03-adaboost",
         frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"m_{\rm done}", r"a_{\rm done}"), ("原子提交", "权重")),
    Case("ALG-C19-2", 3, "V3-C03.tex", "alg:V3-C03-regression-tree-boost",
         frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"m_{\rm done}", r"a_{\rm done}"), ("原子提交", "叶为空")),
    Case("ALG-C19-3", 3, "V3-C03.tex", "alg:V3-C03-gradient-candidate",
         frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"i_{\rm done}", r"j_{\rm done}", r"q_{\rm done}"), ("主状态", "只读")),
    Case("ALG-C19-4", 3, "V3-C03.tex", "alg:V3-C03-gradient-boost",
         frozenset({"completed", "converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"}),
         (r"m_{\rm done}", r"\ell_{\rm done}"), ("原子提交", "候选生成器")),
    Case("ALG-C20-1", 3, "V3-C04.tex", "alg:V3-C04-em",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}",), ("原子提交", "E步", "M步")),
    Case("ALG-C20-3", 3, "V3-C04.tex", "alg:V3-C04-gem-f",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"c_{\rm done}"), ("原子提交", "坐标")),
    Case("ALG-C20-4", 3, "V3-C04.tex", "alg:V3-C04-gem-q",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"}),
         (r"t_{\rm done}", r"\ell_{\rm done}"), ("原子提交", "回缩")),
    Case("ALG-C20-5", 3, "V3-C04.tex", "alg:V3-C04-gem-block",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"b_{\rm done}"), ("原子提交", "主状态保持不变")),
    Case("ALG-C21-1", 3, "V3-C05.tex", "alg:V3-C05-generate",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"t_{\rm done}", r"q_{\rm done}"), ("原子追加", "随机源")),
    Case("ALG-C21-2", 3, "V3-C05.tex", "alg:V3-C05-forward-scaled",
         frozenset({"completed", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"r_{\rm done}"), ("原子提交", "零概率前缀")),
    Case("ALG-C21-3", 3, "V3-C05.tex", "alg:V3-C05-backward-scaled",
         frozenset({"completed", "invalid_input", "numerical_failure"}),
         (r"b_{\rm done}", r"g_{\rm done}", r"x_{\rm done}"), ("原子提交", "归一化")),
    Case("ALG-C21-4", 3, "V3-C05.tex", "alg:V3-C05-bw",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"r_{\rm done}", r"s_{\rm done}"), ("原子提交", "ML", "MAP")),
    Case("ALG-C21-5", 3, "V3-C05.tex", "alg:V3-C05-viterbi",
         frozenset({"completed", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"b_{\rm done}"), ("原子提交", "无路径标记")),
)


def balanced_brace_content(text: str, opening_brace: int) -> tuple[str, int]:
    if opening_brace < 0 or text[opening_brace] != "{":
        raise AssertionError("expected opening brace")
    depth = 0
    for index in range(opening_brace, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1:index], index + 1
    raise AssertionError("unbalanced contract brace")


def parse_fields(config: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    cursor = 0
    while cursor < len(config):
        while cursor < len(config) and (config[cursor].isspace() or config[cursor] == ","):
            cursor += 1
        if cursor >= len(config):
            break
        match = re.match(r"([a-z_]+)\s*=\s*", config[cursor:])
        if match is None:
            raise AssertionError(f"cannot parse contract near {config[cursor:cursor + 50]!r}")
        key = match.group(1)
        cursor += match.end()
        if cursor >= len(config) or config[cursor] != "{":
            raise AssertionError(f"field {key} is not brace-delimited")
        value, cursor = balanced_brace_content(config, cursor)
        if key in fields:
            raise AssertionError(f"duplicate contract field {key}")
        fields[key] = value.strip()
    return fields


def assert_balanced_algorithm_braces(text: str, issue_id: str) -> None:
    depth = 0
    for index, char in enumerate(text):
        if index > 0 and text[index - 1] == "\\":
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise AssertionError(f"{issue_id}: premature closing brace")
    if depth != 0:
        raise AssertionError(f"{issue_id}: unbalanced algorithm braces ({depth})")


def extract(case: Case) -> tuple[dict[str, str], str]:
    root = V2 if case.volume == 2 else V3
    text = (root / case.filename).read_text(encoding="utf-8")
    label = rf"\label{{{case.label}}}"
    if text.count(label) != 1:
        raise AssertionError(f"{case.issue_id}: label count is not one")
    label_position = text.index(label)

    marker = r"\begin{AlgorithmContract}"
    contract_start = text.rfind(marker, 0, label_position)
    if contract_start < 0:
        raise AssertionError(f"{case.issue_id}: missing AlgorithmContract")
    config_open = text.find("{", contract_start + len(marker))
    config, config_end = balanced_brace_content(text, config_open)
    contract_end = text.find(r"\end{AlgorithmContract}", label_position)
    if contract_end < 0:
        raise AssertionError(f"{case.issue_id}: unterminated AlgorithmContract")

    algorithm_start = text.find(r"\begin{algorithm}", config_end, label_position)
    algorithm_end = text.find(r"\end{algorithm}", label_position, contract_end)
    if algorithm_start < 0 or algorithm_end < 0:
        raise AssertionError(f"{case.issue_id}: contract does not wrap its algorithm")
    wrapped = text[config_end:contract_end]
    if wrapped.count(r"\begin{algorithm}") != 1 or wrapped.count(r"\end{algorithm}") != 1:
        raise AssertionError(f"{case.issue_id}: contract must wrap exactly one algorithm")
    algorithm = text[algorithm_start:algorithm_end + len(r"\end{algorithm}")]
    return parse_fields(config), algorithm


class Chapter16To21ContractTests(unittest.TestCase):
    def assert_case(self, case: Case) -> None:
        fields, algorithm = extract(case)
        assert_balanced_algorithm_braces(algorithm, case.issue_id)
        self.assertEqual(set(fields), FIELDS, case.issue_id)
        for name, value in fields.items():
            self.assertTrue(value.strip(), f"{case.issue_id}: empty {name}")
            self.assertNotIn("TODO", value, f"{case.issue_id}: placeholder {name}")

        normalized_contract_status = fields["status"].replace(r"\_", "_")
        contract_statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_contract_status))
        self.assertEqual(contract_statuses, set(case.expected_statuses), case.issue_id)
        self.assertTrue(contract_statuses <= ALLOWED_STATUSES, case.issue_id)

        normalized_algorithm = algorithm.replace(r"\_", "_")
        algorithm_statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_algorithm))
        algorithm_statuses.discard("status")
        self.assertEqual(algorithm_statuses, set(case.expected_statuses), case.issue_id)
        self.assertTrue(algorithm_statuses <= ALLOWED_STATUSES, case.issue_id)

        self.assertIn(r"\mathtt{status}", algorithm, case.issue_id)
        self.assertIn("最后合法", algorithm, case.issue_id)
        self.assertIn("最终诊断", algorithm, case.issue_id)
        self.assertNotIn("invalid_candidate", algorithm, case.issue_id)
        self.assertNotIn("undefined_mstep", algorithm, case.issue_id)
        for token in case.iteration_tokens:
            self.assertIn(token, fields["iterations"], f"{case.issue_id}: iterations lacks {token}")
            self.assertIn(token, algorithm, f"{case.issue_id}: algorithm lacks {token}")
        for token in case.semantic_tokens:
            self.assertIn(token, algorithm, f"{case.issue_id}: semantic token {token}")

        return_lines = [
            line for line in algorithm.splitlines() if "返回" in line and r"\mathtt{" in line
        ]
        self.assertGreaterEqual(len(return_lines), len(case.expected_statuses), case.issue_id)
        for line in return_lines:
            self.assertIn("诊断", line, f"{case.issue_id}: return lacks diagnosis: {line}")


def _make_test(case: Case):
    def test(self: Chapter16To21ContractTests) -> None:
        self.assert_case(case)

    test.__name__ = f"test_{case.issue_id.lower().replace('-', '_')}"
    return test


for _case in CASES:
    setattr(Chapter16To21ContractTests,
            f"test_{_case.issue_id.lower().replace('-', '_')}",
            _make_test(_case))


if __name__ == "__main__":
    unittest.main(verbosity=2)

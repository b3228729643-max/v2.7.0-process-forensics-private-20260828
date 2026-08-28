"""Independent static audits for algorithm contracts in chapters 31--37."""

from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters"
FIELDS = {
    "input", "output", "preconditions", "initialization", "loop", "update",
    "domain", "failure", "stop", "budget", "status", "iterations",
    "diagnostics", "complexity",
}
ALLOWED = {
    "completed", "converged", "budget_stop", "invalid_input",
    "numerical_failure", "line_search_failed", "random_source_failure",
}
FORBIDDEN_SIZE = (r"\tiny", r"\scriptsize", r"\small", r"\resizebox")


@dataclass(frozen=True)
class Case:
    issue_id: str
    filename: str
    label: str
    statuses: frozenset[str]
    counters: tuple[str, ...]
    semantics: tuple[str, ...]


CASES = (
    Case("ALG-C31-2", "V5-C02.tex", "alg:V5-C02-generalized-inverse",
         frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"k", r"j_{\rm done}", r"u_{\rm done}"), ("原子追加", "零预算", "括区间")),
    Case("ALG-C31-3", "V5-C02.tex", "alg:V5-C02-rejection-math",
         frozenset({"completed", "invalid_input"}),
         (r"m", r"a"), ("原子追加", "理想", "无人工")),
    Case("ALG-C31-4", "V5-C02.tex", "alg:V5-C02-importance-estimation",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"i_{\rm done}", r"q_{\rm done}"), ("原子追加", "零预算", "自归一化")),
    Case("ALG-C32-1", "V5-C03.tex", "alg:V5-C03-general-mh",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"t_{\rm done}", r"p_{\rm done}", r"u_{\rm done}"), ("原子追加", "零预算", "零流")),
    Case("ALG-C32-2", "V5-C03.tex", "alg:V5-C03-component-mh",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"s_{\rm done}", r"c_{\rm done}", r"a_{\rm done}"), ("原子提交", "只读", "上一轮末")),
    Case("ALG-C32-3", "V5-C03.tex", "alg:V5-C03-trace-diagnostics",
         frozenset({"completed", "invalid_input", "numerical_failure"}),
         (r"y_{\rm done}", r"k_{\rm done}", r"b_{\rm done}"), ("原子提交", "批均值", "不是收敛证明")),
    Case("ALG-C33-1", "V5-C04.tex", "alg:V5-C04-systematic-gibbs",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"t_{\rm done}", r"c_{\rm done}", r"q_{\rm done}"), ("原子提交", "只读", "上一完整")),
    Case("ALG-C34-1", "V5-C05.tex", "alg:V5-C05-closed-form-update",
         frozenset({"completed", "invalid_input", "numerical_failure"}),
         (r"w",), ("原子提交", "最后合法", "有限")),
    Case("ALG-C35-1", "V5-C06.tex", "alg:V5-C06-generate",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"k_{\rm done}", r"m_{\rm done}", r"i_{\rm done}", r"q_{\rm done}"), ("原子追加", "前缀", "随机")),
    Case("ALG-C35-2", "V5-C06.tex", "alg:V5-C06-gibbs",
         frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"t_{\rm done}", r"i_{\rm done}", r"q_{\rm done}"), ("原子提交", "回滚", "零预算")),
    Case("ALG-C35-3", "V5-C06.tex", "alg:V5-C06-generic-vem",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"e_{\rm done}", r"m_{\rm done}"), ("原子提交", "上一合法", "双证书")),
    Case("ALG-C35-4", "V5-C06.tex", "alg:V5-C06-local-vi",
         frozenset({"completed", "converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"s_{\rm done}", r"p_{\rm done}"), ("原子提交", "空文档", "上一合法")),
    Case("ALG-C36-1", "V5-C07.tex", "alg:V5-C07-basic-power",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"m_{\rm done}"), ("原子提交", "零预算", "双证书")),
    Case("ALG-C36-2", "V5-C07.tex", "alg:V5-C07-general-power",
         frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
         (r"t_{\rm done}", r"e_{\rm done}", r"p_{\rm done}"), ("原子提交", "悬挂", "零预算")),
    Case("ALG-C37-1", "V5-C08.tex", "alg:V5-C08-selection-protocol",
         frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure", "random_source_failure"}),
         (r"b_{\rm done}", r"e_{\rm done}", r"f_{\rm done}"), ("原子提交", "测试集", "共同分母")),
)


def balanced(text: str, opening: int) -> tuple[str, int]:
    if opening < 0 or text[opening] != "{":
        raise AssertionError("expected opening brace")
    depth = 0
    for index in range(opening, len(text)):
        escaped = index > 0 and text[index - 1] == "\\"
        if text[index] == "{" and not escaped:
            depth += 1
        elif text[index] == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[opening + 1:index], index + 1
    raise AssertionError("unbalanced contract")


def parse_fields(config: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    cursor = 0
    while cursor < len(config):
        while cursor < len(config) and (config[cursor].isspace() or config[cursor] == ","):
            cursor += 1
        if cursor == len(config):
            break
        match = re.match(r"([a-z_]+)\s*=\s*", config[cursor:])
        if match is None:
            raise AssertionError(f"cannot parse near {config[cursor:cursor + 60]!r}")
        key = match.group(1)
        cursor += match.end()
        value, cursor = balanced(config, cursor)
        if key in fields:
            raise AssertionError(f"duplicate {key}")
        fields[key] = value.strip()
    return fields


@lru_cache(maxsize=1)
def all_tex() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "讲义源码").rglob("*.tex"))


def extract(case: Case) -> tuple[dict[str, str], str]:
    text = (CHAPTERS / case.filename).read_text(encoding="utf-8")
    label = rf"\label{{{case.label}}}"
    if text.count(label) != 1 or all_tex().count(label) != 1:
        raise AssertionError(f"{case.label}: label is not globally unique")
    label_pos = text.index(label)
    marker = r"\begin{AlgorithmContract}"
    start = text.rfind(marker, 0, label_pos)
    if start < 0:
        raise AssertionError(f"{case.label}: missing contract")
    config, config_end = balanced(text, text.find("{", start + len(marker)))
    end = text.find(r"\end{AlgorithmContract}", label_pos)
    if end < 0:
        raise AssertionError(f"{case.label}: missing contract end")
    wrapped = text[config_end:end]
    if wrapped.count(r"\begin{algorithm}") != 1 or wrapped.count(r"\end{algorithm}") != 1:
        raise AssertionError(f"{case.label}: contract must wrap one algorithm")
    a0 = wrapped.index(r"\begin{algorithm}")
    a1 = wrapped.index(r"\end{algorithm}") + len(r"\end{algorithm}")
    algorithm = wrapped[a0:a1]
    if label not in algorithm:
        raise AssertionError(f"{case.label}: label outside algorithm")
    return parse_fields(config), algorithm


def assert_balanced_algorithm(algorithm: str, label: str) -> None:
    depth = 0
    for index, char in enumerate(algorithm):
        if index > 0 and algorithm[index - 1] == "\\":
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise AssertionError(f"{label}: premature closing brace")
    if depth:
        raise AssertionError(f"{label}: unbalanced braces ({depth})")


class Chapter31To37ContractTests(unittest.TestCase):
    def assert_case(self, case: Case) -> None:
        fields, algorithm = extract(case)
        assert_balanced_algorithm(algorithm, case.label)
        self.assertEqual(set(fields), FIELDS, case.issue_id)
        for name, value in fields.items():
            self.assertTrue(value, f"{case.issue_id}: empty {name}")
            self.assertNotRegex(value, r"TODO|TBD|待补|占位", f"{case.issue_id}: placeholder {name}")

        normalized_status = fields["status"].replace(r"\_", "_")
        statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_status))
        self.assertEqual(statuses, set(case.statuses), case.issue_id)
        self.assertTrue(statuses <= ALLOWED, case.issue_id)
        normalized_algorithm = algorithm.replace(r"\_", "_")
        for status in case.statuses:
            self.assertIn(rf"\mathtt{{{status}}}", normalized_algorithm, f"{case.issue_id}: {status}")
        self.assertNotRegex(normalized_algorithm, r"\\texttt\{(?:completed|converged|budget_stop|invalid_input|numerical_failure|random_source_failure)\}")
        self.assertNotIn(r"\mathtt{none}", normalized_algorithm)
        self.assertNotIn("failure_reason", normalized_algorithm)

        self.assertIn(r"\mathtt{status}", algorithm, case.issue_id)
        self.assertIn("最后合法", fields["output"], case.issue_id)
        self.assertIn("原子", fields["update"], case.issue_id)
        self.assertRegex(fields["budget"], r"至多|恰好|固定|不适用", case.issue_id)
        for counter in case.counters:
            self.assertIn(counter, fields["iterations"], f"{case.issue_id}: iterations lacks {counter}")
            self.assertIn(counter, algorithm, f"{case.issue_id}: algorithm lacks {counter}")
        for token in case.semantics:
            self.assertIn(token, algorithm, f"{case.issue_id}: missing {token}")
        for command in FORBIDDEN_SIZE:
            self.assertNotIn(command, algorithm, f"{case.issue_id}: forbidden sizing {command}")

        status_tokens = tuple(r"\mathtt{" + status.replace("_", r"\_") + "}" for status in case.statuses)
        return_lines = [
            line for line in algorithm.splitlines()
            if "返回" in line and any(token in line for token in status_tokens)
        ]
        self.assertTrue(return_lines, f"{case.issue_id}: no explicit exits")
        for line in return_lines:
            self.assertRegex(line, r"诊断|证书", f"{case.issue_id}: exit lacks final diagnosis: {line}")


def make_test(case: Case):
    def test(self: Chapter31To37ContractTests) -> None:
        self.assert_case(case)
    return test


for _case in CASES:
    setattr(Chapter31To37ContractTests,
            f"test_{_case.issue_id.lower().replace('-', '_')}", make_test(_case))


if __name__ == "__main__":
    unittest.main(verbosity=2)

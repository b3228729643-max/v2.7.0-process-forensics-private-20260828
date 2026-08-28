"""Static contract tests for the bounded chapter 12--15 algorithm batch."""

from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_ROOT = ROOT / "讲义源码" / "第02册_基础监督学习方法" / "chapters"

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
    filename: str
    label: str
    expected_statuses: frozenset[str]
    iteration_tokens: tuple[str, ...]


CASES = (
    Case(
        "ALG-C12-1",
        "V2-C01.tex",
        "alg:V2-C01-primal",
        frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
        (r"t_{\rm done}", "v", "U"),
    ),
    Case(
        "ALG-C12-2",
        "V2-C01.tex",
        "alg:V2-C01-dual",
        frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
        (r"t_{\rm done}", "v", "U"),
    ),
    Case(
        "ALG-C13-1",
        "V2-C02.tex",
        "alg:V2-C02-knn",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        (r"i_{\rm done}",),
    ),
    Case(
        "ALG-C13-2",
        "V2-C02.tex",
        "alg:V2-C02-kd-build",
        frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
        ("m",),
    ),
    Case(
        "ALG-C13-3",
        "V2-C02.tex",
        "alg:V2-C02-kd-search",
        frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
        ("v", r"p_{\rm cut}"),
    ),
    Case(
        "ALG-C14-1",
        "V2-C03.tex",
        "alg:V2-C03-nb",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        (r"i_{\rm done}", r"e_{\rm done}"),
    ),
    Case(
        "ALG-C15-1",
        "V2-C04.tex",
        "alg:V2-C04-id3-c45",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        ("v",),
    ),
    Case(
        "ALG-C15-2",
        "V2-C04.tex",
        "alg:V2-C04-entropy-prune",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        ("v", "p"),
    ),
    Case(
        "ALG-C15-3",
        "V2-C04.tex",
        "alg:V2-C04-cart-grow",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        ("v",),
    ),
    Case(
        "ALG-C15-4",
        "V2-C04.tex",
        "alg:V2-C04-cart-prune",
        frozenset({"completed", "invalid_input", "numerical_failure"}),
        ("k", "v"),
    ),
)


def balanced_brace_content(text: str, opening_brace: int) -> tuple[str, int]:
    if text[opening_brace] != "{":
        raise AssertionError("expected opening brace")
    depth = 0
    for index in range(opening_brace, len(text)):
        char = text[index]
        if char == "{" and (index == 0 or text[index - 1] != "\\"):
            depth += 1
        elif char == "}" and (index == 0 or text[index - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[opening_brace + 1 : index], index + 1
    raise AssertionError("unbalanced contract brace")


def parse_fields(config: str) -> dict[str, str]:
    result: dict[str, str] = {}
    cursor = 0
    while cursor < len(config):
        while cursor < len(config) and (config[cursor].isspace() or config[cursor] == ","):
            cursor += 1
        if cursor >= len(config):
            break
        match = re.match(r"([a-z_]+)\s*=\s*", config[cursor:])
        if match is None:
            raise AssertionError(f"cannot parse contract near {config[cursor:cursor + 40]!r}")
        key = match.group(1)
        cursor += match.end()
        if cursor >= len(config) or config[cursor] != "{":
            raise AssertionError(f"field {key} is not brace-delimited")
        value, cursor = balanced_brace_content(config, cursor)
        if key in result:
            raise AssertionError(f"duplicate contract field {key}")
        result[key] = value.strip()
    return result


def extract_contract_and_algorithm(case: Case) -> tuple[dict[str, str], str]:
    text = (CHAPTER_ROOT / case.filename).read_text(encoding="utf-8")
    label_token = rf"\label{{{case.label}}}"
    if text.count(label_token) != 1:
        raise AssertionError(f"{case.issue_id}: label count is not one")
    label_position = text.index(label_token)

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
        raise AssertionError(f"{case.issue_id}: contract does not wrap the algorithm")
    wrapped_region = text[config_end:contract_end]
    if wrapped_region.count(r"\begin{algorithm}") != 1 or wrapped_region.count(r"\end{algorithm}") != 1:
        raise AssertionError(f"{case.issue_id}: contract must wrap exactly one algorithm")
    return parse_fields(config), text[algorithm_start : algorithm_end + len(r"\end{algorithm}")]


class Chapter12To15ContractTests(unittest.TestCase):
    def assert_case(self, case: Case) -> None:
        fields, algorithm = extract_contract_and_algorithm(case)

        self.assertEqual(set(fields), FIELDS, case.issue_id)
        for key, value in fields.items():
            self.assertTrue(value.strip(), f"{case.issue_id}: empty {key}")
            self.assertNotIn("TODO", value, f"{case.issue_id}: placeholder {key}")

        normalized_status_field = fields["status"].replace(r"\_", "_")
        declared = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_status_field))
        self.assertEqual(declared, set(case.expected_statuses), case.issue_id)
        self.assertTrue(declared <= ALLOWED_STATUSES, case.issue_id)

        self.assertIn(r"\mathtt{status}", algorithm, case.issue_id)
        self.assertIn("最终诊断", algorithm, case.issue_id)
        self.assertIn("最后合法", algorithm, case.issue_id)
        self.assertIn(r"\mathtt{invalid\_input}", algorithm, case.issue_id)
        self.assertIn(r"\mathtt{numerical\_failure}", algorithm, case.issue_id)
        normalized_algorithm = algorithm.replace(r"\_", "_")
        algorithm_statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_algorithm))
        algorithm_statuses.discard("status")
        self.assertEqual(algorithm_statuses, set(case.expected_statuses), case.issue_id)
        self.assertTrue(algorithm_statuses <= ALLOWED_STATUSES, case.issue_id)
        for status in case.expected_statuses:
            escaped_status = status.replace("_", r"\_")
            self.assertIn(rf"\mathtt{{{escaped_status}}}", algorithm, case.issue_id)
        for token in case.iteration_tokens:
            self.assertIn(token, fields["iterations"], f"{case.issue_id}: {token}")
            self.assertIn(token, algorithm, f"{case.issue_id}: {token}")

        return_lines = [
            line for line in algorithm.splitlines() if "返回" in line and r"\mathtt{" in line
        ]
        self.assertGreaterEqual(len(return_lines), len(case.expected_statuses), case.issue_id)
        for line in return_lines:
            self.assertIn("诊断", line, f"{case.issue_id}: return lacks diagnosis: {line}")


def _make_test(case: Case):
    def test(self: Chapter12To15ContractTests) -> None:
        self.assert_case(case)

    test.__name__ = f"test_{case.issue_id.lower().replace('-', '_')}"
    return test


for _case in CASES:
    setattr(Chapter12To15ContractTests, f"test_{_case.issue_id.lower().replace('-', '_')}", _make_test(_case))


if __name__ == "__main__":
    unittest.main(verbosity=2)

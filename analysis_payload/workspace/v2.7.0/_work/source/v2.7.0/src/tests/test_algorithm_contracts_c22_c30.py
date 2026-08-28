"""Static contract tests for the bounded chapter 22--30 algorithm batch."""

from __future__ import annotations

import re
import unittest
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "讲义源码" / "第03册_优化模型与序列模型" / "chapters"
V4 = ROOT / "讲义源码" / "第04册_无监督学习与矩阵分解" / "chapters"
V5 = ROOT / "讲义源码" / "第05册_采样方法主题模型与图排序" / "chapters"

FIELDS = {
    "input", "output", "preconditions", "initialization", "loop", "update",
    "domain", "failure", "stop", "budget", "status", "iterations",
    "diagnostics", "complexity",
}
ALLOWED_STATUSES = {
    "completed", "converged", "budget_stop", "invalid_input",
    "numerical_failure", "line_search_failed", "random_source_failure",
}
FORBIDDEN_SIZING = (
    r"\tiny", r"\scriptsize", r"\small", r"\SLStudentTallAlgorithmFont",
    r"\resizebox",
)


@dataclass(frozen=True)
class Target:
    label: str
    statuses: frozenset[str]
    counters: tuple[str, ...]
    semantics: tuple[str, ...]


@dataclass(frozen=True)
class Case:
    issue_id: str
    volume: int
    filename: str
    targets: tuple[Target, ...]


CASES = (
    Case("ALG-C22-1", 3, "V3-C06.tex", (
        Target("alg:V3-C06-bfgs",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"}),
               (r"k_{\rm done}", r"\ell_{\rm done}", r"q_{\rm fb}"),
               ("原子提交", "前向--后向", "失败$(k")),
    )),
    Case("ALG-C23-1", 3, "V3-C07.tex", (
        Target("alg:V3-C07-selection",
               frozenset({"completed", "invalid_input", "numerical_failure"}),
               (r"m_{\rm done}", r"e_{\rm done}", r"f_{\rm done}"),
               ("共同分母", "原子提交", "全量重训")),
    )),
    Case("ALG-C24-1", 4, "V4-C01.tex", (
        Target("alg:V4-C01-selection",
               frozenset({"completed", "invalid_input", "numerical_failure", "random_source_failure"}),
               (r"r_{\rm done}", r"e_{\rm done}", r"c_h"),
               ("原子提交", "随机源", "无可用候选")),
    )),
    Case("ALG-C25-1", 4, "V4-C02.tex", (
        Target("alg:V4-C02-agglomerative",
               frozenset({"completed", "invalid_input", "numerical_failure"}),
               (r"m_{\rm done}", r"d_{\rm done}"),
               ("原子", "上一划分", "下一合并超过阈值")),
    )),
    Case("ALG-C25-2", 4, "V4-C02.tex", (
        Target("alg:V4-C02-kmeans",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"e_{\rm done}"),
               ("原子提交", "空类", "最后合法")),
        Target("alg:V4-C02-kmeans-empty-repair",
               frozenset({"completed", "invalid_input", "numerical_failure"}),
               (r"e_{\rm done}",),
               ("原子", "供体", "最后合法")),
        Target("alg:V4-C02-kmeans-multistart",
               frozenset({"completed", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"r_{\rm done}", r"t_{\rm total}"),
               ("原子保存", "启动", "无预算内收敛")),
    )),
    Case("ALG-C26-1", 4, "V4-C03.tex", (
        Target("alg:V4-C03-subspace-svd",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"b_{\rm done}", r"s_{\rm done}"),
               ("原子提交", "最后合法", "Ritz")),
    )),
    Case("ALG-C27-1", 4, "V4-C04.tex", (
        Target("alg:V4-C04-pca",
               frozenset({"completed", "invalid_input", "numerical_failure"}),
               (r"p_{\rm done}", r"s_{\rm done}"),
               ("原子提交", "一次薄SVD", "最后合法")),
    )),
    Case("ALG-C28-1", 4, "V4-C05.tex", (
        Target("alg:V4-C05-lsa",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"b_{\rm done}"),
               ("正交化", "原子提交", "上一合法")),
    )),
    Case("ALG-C28-2", 4, "V4-C05.tex", (
        Target("alg:V4-C05-nmf-fro",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"a_{\rm done}"),
               ("原子提交", "上一合法", "分母")),
    )),
    Case("ALG-C28-3", 4, "V4-C05.tex", (
        Target("alg:V4-C05-nmf-kl",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"a_{\rm done}"),
               ("原子提交", "上一合法", "支撑")),
    )),
    Case("ALG-C29-2", 4, "V4-C06.tex", (
        Target("alg:V4-C06-plsa-foldin",
               frozenset({"converged", "budget_stop", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"z_{\rm done}"),
               ("初始化", "原子提交", "上一合法")),
    )),
    Case("ALG-C30-1", 5, "V5-C01.tex", (
        Target("alg:V5-C01-distribution-propagation",
               frozenset({"completed", "invalid_input", "numerical_failure"}),
               (r"t_{\rm done}", r"r_{\rm done}"),
               ("原子提交", "上一合法", "不追加")),
    )),
)


def volume_root(volume: int) -> Path:
    return {3: V3, 4: V4, 5: V5}[volume]


def balanced_brace_content(text: str, opening: int) -> tuple[str, int]:
    if opening < 0 or text[opening] != "{":
        raise AssertionError("expected opening brace")
    depth = 0
    for index in range(opening, len(text)):
        char = text[index]
        escaped = index > 0 and text[index - 1] == "\\"
        if char == "{" and not escaped:
            depth += 1
        elif char == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return text[opening + 1:index], index + 1
    raise AssertionError("unbalanced brace")


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
            raise AssertionError(f"cannot parse contract near {config[cursor:cursor + 60]!r}")
        key = match.group(1)
        cursor += match.end()
        value, cursor = balanced_brace_content(config, cursor)
        if key in fields:
            raise AssertionError(f"duplicate field {key}")
        fields[key] = value.strip()
    return fields


def assert_balanced_algorithm_braces(algorithm: str, label: str) -> None:
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
        raise AssertionError(f"{label}: unbalanced algorithm braces ({depth})")


@lru_cache(maxsize=1)
def all_tex() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "讲义源码").rglob("*.tex"))


def extract(volume: int, filename: str, label: str) -> tuple[dict[str, str], str, str]:
    text = (volume_root(volume) / filename).read_text(encoding="utf-8")
    label_token = rf"\label{{{label}}}"
    if text.count(label_token) != 1 or all_tex().count(label_token) != 1:
        raise AssertionError(f"{label}: label is not globally unique")
    label_pos = text.index(label_token)
    marker = r"\begin{AlgorithmContract}"
    contract_start = text.rfind(marker, 0, label_pos)
    if contract_start < 0:
        raise AssertionError(f"{label}: missing AlgorithmContract")
    config_open = text.find("{", contract_start + len(marker))
    config, config_end = balanced_brace_content(text, config_open)
    contract_end = text.find(r"\end{AlgorithmContract}", label_pos)
    if contract_end < 0:
        raise AssertionError(f"{label}: unterminated contract")
    wrapped = text[config_end:contract_end]
    if wrapped.count(r"\begin{algorithm}") != 1 or wrapped.count(r"\end{algorithm}") != 1:
        raise AssertionError(f"{label}: contract must wrap exactly one algorithm")
    alg_start = wrapped.index(r"\begin{algorithm}")
    alg_end = wrapped.index(r"\end{algorithm}") + len(r"\end{algorithm}")
    algorithm = wrapped[alg_start:alg_end]
    if label_token not in algorithm:
        raise AssertionError(f"{label}: label not inside wrapped algorithm")
    return parse_fields(config), algorithm, text


class Chapter22To30ContractTests(unittest.TestCase):
    def assert_target(self, case: Case, target: Target) -> None:
        fields, algorithm, _ = extract(case.volume, case.filename, target.label)
        assert_balanced_algorithm_braces(algorithm, target.label)
        self.assertEqual(set(fields), FIELDS, target.label)
        for name, value in fields.items():
            self.assertTrue(value, f"{target.label}: empty {name}")
            self.assertNotRegex(value, r"TODO|TBD|待补|占位", f"{target.label}: placeholder {name}")

        contract_status = fields["status"].replace(r"\_", "_")
        contract_statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", contract_status))
        self.assertEqual(contract_statuses, set(target.statuses), target.label)
        normalized_algorithm = algorithm.replace(r"\_", "_")
        algorithm_statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", normalized_algorithm))
        algorithm_statuses.discard("status")
        self.assertTrue(algorithm_statuses <= ALLOWED_STATUSES, target.label)
        self.assertTrue(set(target.statuses) <= algorithm_statuses, target.label)

        self.assertIn(r"\mathtt{status}", algorithm, target.label)
        self.assertIn("诊断", algorithm, target.label)
        self.assertIn("原子", fields["update"], target.label)
        self.assertIn("最后合法", fields["output"], target.label)
        self.assertRegex(fields["budget"], r"至多|恰好|固定", target.label)
        for counter in target.counters:
            self.assertIn(counter, fields["iterations"], f"{target.label}: iterations lacks {counter}")
            self.assertIn(counter, algorithm, f"{target.label}: algorithm lacks {counter}")
        for token in target.semantics:
            self.assertIn(token, algorithm, f"{target.label}: missing semantic token {token}")
        for command in FORBIDDEN_SIZING:
            self.assertNotIn(command, algorithm, f"{target.label}: forbidden sizing command {command}")
        return_lines = [
            line for line in algorithm.splitlines()
            if "返回" in line and r"\mathtt{" in line
            and any(status in line.replace(r"\_", "_") for status in ALLOWED_STATUSES)
        ]
        self.assertTrue(return_lines, f"{target.label}: no explicit status exits")
        for line in return_lines:
            self.assertRegex(line, r"诊断|证书", f"{target.label}: exit lacks final diagnosis: {line}")

    def assert_case(self, case: Case) -> None:
        for target in case.targets:
            self.assert_target(case, target)
        if case.issue_id == "ALG-C25-2":
            text = (V4 / case.filename).read_text(encoding="utf-8")
            self.assertIn(r"\renewcommand{\thealgocf}{\thechapter.\arabic{algocf}A}", text)
            self.assertIn(r"\renewcommand{\thealgocf}{\thechapter.\arabic{algocf}B}", text)
            self.assertIn(r"\renewcommand{\thealgocf}{\thechapter.\arabic{algocf}C}", text)
            self.assertIn(r"算法\ref{alg:V4-C02-kmeans-empty-repair}", text)


def make_test(case: Case):
    def test(self: Chapter22To30ContractTests) -> None:
        self.assert_case(case)
    return test


for _case in CASES:
    setattr(Chapter22To30ContractTests,
            f"test_{_case.issue_id.lower().replace('-', '_')}", make_test(_case))


if __name__ == "__main__":
    unittest.main(verbosity=2)

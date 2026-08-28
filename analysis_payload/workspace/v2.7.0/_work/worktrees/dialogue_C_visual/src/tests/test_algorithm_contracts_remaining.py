from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "讲义源码"
AUDIT_PATH = ROOT / "qa" / "static_source_audit.py"

FIELDS = {
    "input", "output", "preconditions", "initialization", "loop", "update",
    "domain", "failure", "stop", "budget", "status", "iterations",
    "diagnostics", "complexity",
}
ALLOWED = {
    "completed", "converged", "budget_stop", "invalid_input",
    "numerical_failure", "line_search_failed", "random_source_failure",
}
FORBIDDEN_SIZE = (r"\tiny", r"\scriptsize", r"\small", r"\footnotesize", r"\resizebox")


@dataclass(frozen=True)
class ContractCase:
    issue_id: str
    file: str
    label: str
    statuses: tuple[str, ...]
    counters: tuple[str, ...]
    semantics: tuple[str, ...]


V1 = "第01册_数学基础与统计学习基本理论/chapters"
V3 = "第03册_优化模型与序列模型/chapters"
V4 = "第04册_无监督学习与矩阵分解/chapters"
V5 = "第05册_采样方法主题模型与图排序/chapters"

CONTRACT_CASES = (
    ContractCase("ALG-C2-1", f"{V1}/V1-C02.tex", "alg:V1-C02-power",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure"),
                 ("t_{\\rm done}", "m_{\\rm done}"),
                 ("r^+", "零轮残差证书", "预算耗尽")),
    ContractCase("ALG-C4-1", f"{V1}/V1-C04.tex", "alg:V1-C04-bayes",
                 ("completed", "invalid_input", "numerical_failure"),
                 ("h_{\\rm done}", "n_{\\rm done}"),
                 ("Z=0", "q^+", "原子提交")),
    ContractCase("ALG-C5-1", f"{V1}/V1-C05.tex", "alg:V1-C05-dirichlet",
                 ("completed", "invalid_input", "numerical_failure"),
                 ("i_{\\rm done}", "p_{\\rm done}"),
                 ("\\alpha^+", "p_k^+", "零观测")),
    ContractCase("ALG-C6-1", f"{V1}/V1-C06.tex", "alg:V1-C06-gain",
                 ("completed", "invalid_input", "numerical_failure"),
                 ("a_{\\rm done}", "s_{\\rm done}"),
                 ("\\mathcal A=\\varnothing", "空推荐", "原子追加")),
    ContractCase("ALG-C7-1", f"{V1}/V1-C07.tex", "alg:V1-C07-kkt-check",
                 ("completed", "invalid_input", "numerical_failure"),
                 ("c_{\\rm done}",),
                 ("通过标志", "主导残差", "原子追加")),
    ContractCase("ALG-C8-1", f"{V1}/V1-C08.tex", "alg:V1-C08-bfgs",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"),
                 ("k_{\\rm done}", "j_{\\rm done}", "g_{\\rm done}"),
                 ("G^+", "Wolfe", "曲率阶段诊断")),
    ContractCase("ALG-C8-2", f"{V1}/V1-C08.tex", "alg:V1-C08-iis",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure"),
                 ("k_{\\rm done}", "d_{\\rm done}"),
                 ("\\delta_i^+", "w^+", "原子提交")),
    ContractCase("ALG-C8-3", f"{V1}/V1-C08.tex", "alg:V1-C08-gradient",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed"),
                 ("k_{\\rm done}", "j_{\\rm done}", "f_{\\rm done}", "g_{\\rm done}"),
                 ("Armijo", "x^+", "原子提交")),
    ContractCase("ALG-C9-1", f"{V1}/V1-C09.tex", "alg:V1-C09-finite-erm",
                 ("completed", "invalid_input", "numerical_failure"),
                 ("m_{\\rm done}", "l_{\\rm done}"),
                 ("u_{mi}", "\\widehat R_m", "原子追加")),
    ContractCase("ALG-C10-1", f"{V1}/V1-C10.tex", "alg:V1-C10-kfold",
                 ("completed", "budget_stop", "invalid_input", "numerical_failure", "random_source_failure"),
                 ("f_{\\rm done}", "e_{\\rm done}", "c_{\\rm done}"),
                 ("B_{\\rm fit}", "未定义选择", "全折成功")),
    ContractCase("ALG-C11-1", f"{V1}/V1-C11.tex", "alg:V1-C11-task",
                 ("completed", "budget_stop", "invalid_input", "numerical_failure", "random_source_failure"),
                 ("k_{\\rm done}", "f_{\\rm done}", "r_{\\rm test}"),
                 ("读取测试集一次", "禁止返回搜索", "\\mathtt{frozen}")),
    ContractCase("ALG-PLSA-EM", f"{V4}/V4-C06.tex", "alg:V4-C06-plsa-em",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure"),
                 ("t_{\\rm done}", "z_{\\rm done}", "k_{\\rm done}"),
                 ("log-sum-exp", "零支撑", "原子提交")),
    ContractCase("ALG-GMM-EM", f"{V3}/V3-C04.tex", "alg:V3-C04-gmm",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure", "random_source_failure"),
                 ("r_{\\rm done}", "t_{\\rm done}", "e_{\\rm done}"),
                 ("\\Theta_\\sigma", "测试集不得参与", "原子提交")),
    ContractCase("ALG-IID-MC", f"{V5}/V5-C02.tex", "alg:V5-C02-iid-mc-online",
                 ("completed", "invalid_input", "numerical_failure", "random_source_failure"),
                 ("k", "u_{\\rm done}"),
                 ("N=0", "k^+", "原子提交")),
    ContractCase("ALG-L004-CONTRACT", f"{V5}/V5-C06.tex", "alg:V5-C06-vem",
                 ("converged", "budget_stop", "invalid_input", "numerical_failure", "line_search_failed", "random_source_failure"),
                 ("s_{\\rm done}", "r_{\\rm done}", "m_{\\rm done}", "k_{\\rm done}", "j_{\\rm done}"),
                 ("startup\\_ok", "topic\\_loop", "start\\_loop")),
)


def read(case: ContractCase) -> str:
    return (SOURCE_ROOT / case.file).read_text(encoding="utf-8")


def balanced(text: str, opening: int) -> tuple[str, int]:
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
    raise AssertionError("unbalanced brace group")


def parse_fields(config: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    cursor = 0
    while cursor < len(config):
        while cursor < len(config) and (config[cursor].isspace() or config[cursor] == ","):
            cursor += 1
        if cursor == len(config):
            break
        match = re.match(r"([a-z_]+)\s*=\s*", config[cursor:])
        if not match:
            raise AssertionError(f"cannot parse contract near {config[cursor:cursor + 60]!r}")
        key = match.group(1)
        cursor += match.end()
        value, cursor = balanced(config, cursor)
        if key in fields:
            raise AssertionError(f"duplicate contract field {key}")
        fields[key] = value.strip()
    return fields


def all_contract_ranges(text: str) -> list[tuple[int, int, dict[str, str]]]:
    marker = r"\begin{AlgorithmContract}"
    end_marker = r"\end{AlgorithmContract}"
    result: list[tuple[int, int, dict[str, str]]] = []
    cursor = 0
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            return result
        opening = text.find("{", start + len(marker))
        config, config_end = balanced(text, opening)
        end = text.find(end_marker, config_end)
        if end < 0:
            raise AssertionError("unterminated AlgorithmContract")
        end += len(end_marker)
        result.append((start, end, parse_fields(config)))
        cursor = end


def extract(case: ContractCase) -> tuple[dict[str, str], str, str]:
    text = read(case)
    label_token = rf"\label{{{case.label}}}"
    if text.count(label_token) != 1:
        raise AssertionError(f"{case.label}: label count is {text.count(label_token)}")
    label_pos = text.index(label_token)
    algorithm_start = text.rfind(r"\begin{algorithm}", 0, label_pos)
    algorithm_end = text.find(r"\end{algorithm}", label_pos)
    if algorithm_start < 0 or algorithm_end < 0:
        raise AssertionError(f"{case.label}: algorithm boundary missing")
    algorithm_end += len(r"\end{algorithm}")
    enclosing = [item for item in all_contract_ranges(text)
                 if item[0] < algorithm_start and algorithm_end <= item[1]]
    if len(enclosing) != 1:
        raise AssertionError(f"{case.label}: expected one contract, got {len(enclosing)}")
    start, end, fields = enclosing[0]
    region = text[start:end]
    if region.count(r"\begin{algorithm}") != 1:
        raise AssertionError(f"{case.label}: contract must contain exactly one algorithm")
    return fields, text[algorithm_start:algorithm_end], region


def global_label_count(label: str) -> int:
    token = rf"\label{{{label}}}"
    return sum(path.read_text(encoding="utf-8").count(token)
               for path in SOURCE_ROOT.rglob("*.tex"))


def normalized(value: str) -> str:
    return value.replace(r"\_", "_")


class RemainingContractTests(unittest.TestCase):
    def assert_contract(self, case: ContractCase) -> None:
        fields, algorithm, region = extract(case)
        self.assertEqual(set(fields), FIELDS, case.issue_id)
        for name, value in fields.items():
            self.assertTrue(value, f"{case.issue_id}: empty {name}")
            self.assertNotRegex(value, r"TODO|TBD|待补|占位", f"{case.issue_id}: placeholder {name}")
        self.assertEqual(global_label_count(case.label), 1, case.issue_id)

        status_value = normalized(fields["status"])
        statuses = set(re.findall(r"\\mathtt\{([a-z_]+)\}", status_value))
        self.assertEqual(statuses, set(case.statuses), case.issue_id)
        self.assertTrue(statuses <= ALLOWED, case.issue_id)
        algorithm_normal = normalized(algorithm)
        for status in case.statuses:
            self.assertIn(rf"\mathtt{{{status}}}", algorithm_normal, f"{case.issue_id}: {status}")
        self.assertNotIn(r"\mathtt{mathematical_failure}", algorithm_normal)
        self.assertNotRegex(algorithm_normal, r"\\texttt\{(?:completed|converged|budget_stop|invalid_input|numerical_failure|line_search_failed|random_source_failure)\}")

        self.assertIn("最后合法", fields["output"], case.issue_id)
        self.assertIn("原子", fields["update"], case.issue_id)
        self.assertRegex(fields["budget"], r"至多|恰好|上限|预算", case.issue_id)
        self.assertRegex(fields["diagnostics"], r"最终|失败|诊断", case.issue_id)
        self.assertRegex(algorithm, r"上一合法|最后合法|最后合法状态|旧记录|此前状态", case.issue_id)
        self.assertIn("原子", algorithm, case.issue_id)
        for counter in case.counters:
            self.assertIn(counter, fields["iterations"], f"{case.issue_id}: iterations lacks {counter}")
            self.assertIn(counter, algorithm, f"{case.issue_id}: algorithm lacks {counter}")
        for token in case.semantics:
            self.assertIn(token, algorithm, f"{case.issue_id}: semantic token {token}")
        for command in FORBIDDEN_SIZE:
            self.assertNotIn(command, region, f"{case.issue_id}: forbidden sizing {command}")

        status_tokens = tuple(r"\mathtt{" + status.replace("_", r"\_") + "}"
                              for status in case.statuses)
        return_lines = [line for line in algorithm.splitlines()
                        if "返回" in line and any(token in line for token in status_tokens)]
        self.assertTrue(return_lines, f"{case.issue_id}: no explicit standardized exit")
        for line in return_lines:
            self.assertRegex(line, r"诊断|证书|失败位置|最终", f"{case.issue_id}: exit lacks diagnosis: {line}")

    def test_full_static_source_audit_is_73_of_73(self) -> None:
        spec = importlib.util.spec_from_file_location("remaining_static_source_audit", AUDIT_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        result = module.audit_source(SOURCE_ROOT)
        self.assertEqual(result.algorithms, 73)
        self.assertEqual(result.contracted_algorithms, 73)
        self.assertEqual(result.findings, ())


def make_contract_test(case: ContractCase):
    def test(self: RemainingContractTests) -> None:
        self.assert_contract(case)
    return test


for _case in CONTRACT_CASES:
    setattr(RemainingContractTests,
            f"test_contract_{_case.label.removeprefix('alg:').lower().replace('-', '_')}",
            make_contract_test(_case))


class RemainingClosureTests(unittest.TestCase):
    @staticmethod
    def algorithm(file: str, label: str) -> str:
        case = ContractCase("closure", file, label, (), (), ())
        return extract(case)[1]

    def test_alg_c2_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C02.tex", "alg:V1-C02-power")
        self.assertIn("t_{\\rm done}", algorithm)
        self.assertIn(r"\mathtt{budget\_stop}", algorithm)
        self.assertIn("最后合法结果", algorithm)

    def test_alg_c3_1_existing_evidence(self) -> None:
        case = ContractCase("ALG-C3-1", f"{V1}/V1-C03.tex", "alg:V1-C03-gradient-descent", (), (), ())
        fields, algorithm, _ = extract(case)
        self.assertEqual(set(fields), FIELDS)
        self.assertIn("最终合法点", fields["output"])
        self.assertIn("t 精确记录", fields["iterations"])
        for status in ("converged", "budget_stop", "invalid_input", "numerical_failure"):
            self.assertIn(status, normalized(fields["status"]))
            self.assertIn(rf"\mathtt{{{status}}}", normalized(algorithm))
        self.assertIn("在当前返回点重算", algorithm)

    def test_alg_c4_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C04.tex", "alg:V1-C04-bayes")
        self.assertIn("Z=0", algorithm)
        self.assertIn("n_{\\rm done}", algorithm)
        self.assertIn(r"\mathtt{completed}", algorithm)

    def test_alg_c5_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C05.tex", "alg:V1-C05-dirichlet")
        self.assertIn("i_{\\rm done}", algorithm)
        self.assertIn("零观测", algorithm)
        self.assertIn("原子提交", algorithm)

    def test_alg_c6_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C06.tex", "alg:V1-C06-gain")
        self.assertIn("空推荐", algorithm)
        self.assertIn("s_{\\rm done}", algorithm)
        self.assertIn("最终诊断", algorithm)

    def test_alg_c7_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C07.tex", "alg:V1-C07-kkt-check")
        self.assertIn("c_{\\rm done}", algorithm)
        self.assertIn("主导残差", algorithm)
        self.assertIn(r"\mathtt{completed}", algorithm)

    def test_alg_c8_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C08.tex", "alg:V1-C08-bfgs")
        self.assertIn(r"\mathtt{line\_search\_failed}", algorithm)
        self.assertIn("上一合法状态", algorithm)
        self.assertIn("g_{\\rm done}", algorithm)

    def test_alg_c8_2(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C08.tex", "alg:V1-C08-iis")
        self.assertIn("无有限合法根", algorithm)
        self.assertIn("原子提交完整模型状态", algorithm)
        self.assertIn("d_{\\rm done}", algorithm)

    def test_alg_c8_3(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C08.tex", "alg:V1-C08-gradient")
        self.assertIn("j_{\\rm done}", algorithm)
        self.assertIn(r"\mathtt{line\_search\_failed}", algorithm)
        self.assertIn("预算耗尽", algorithm)

    def test_alg_c9_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C09.tex", "alg:V1-C09-finite-erm")
        self.assertIn("l_{\\rm done}", algorithm)
        self.assertIn("旧记录与当前最优", algorithm)
        self.assertIn(r"\mathtt{completed}", algorithm)

    def test_alg_c10_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C10.tex", "alg:V1-C10-kfold")
        partial_stop = algorithm.index("未定义选择")
        selection = algorithm.index("从完整可比较集选择")
        self.assertLess(partial_stop, selection)
        self.assertIn("f_{\\rm done}", algorithm)
        self.assertIn("重训预算诊断", algorithm)

    def test_alg_c11_1(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C11.tex", "alg:V1-C11-task")
        self.assertIn("r_{\\rm test}", algorithm)
        self.assertIn("K=0", algorithm)
        self.assertIn("不得读取测试集", algorithm)
        self.assertIn("最终搜索状态", algorithm)
        self.assertIn("部署/预算最终诊断", algorithm)

    def test_alg_l001_atomic_task_and_one_way_test(self) -> None:
        algorithm = self.algorithm(f"{V1}/V1-C11.tex", "alg:V1-C11-task")
        self.assertEqual(algorithm.count("读取测试集一次"), 1)
        read_position = algorithm.index("读取测试集一次")
        self.assertNotIn(r"\For", algorithm[read_position:])
        self.assertIn("禁止返回搜索", algorithm[read_position:])
        steps = ("定义预测时点", "定义$\\mathcal X", "生成互斥训练", "仅在训练集拟合", "仅在验证集计算", "原子冻结")
        lines = algorithm.splitlines()
        indices = [next(i for i, line in enumerate(lines) if step in line) for step in steps]
        self.assertEqual(indices, sorted(set(indices)))

    def test_alg_l002_existing_atomic_tree_steps(self) -> None:
        algorithm = self.algorithm("第02册_基础监督学习方法/chapters/V2-C04.tex", "alg:V2-C04-id3-c45")
        steps = ("枚举合法切分", "为每个合法切分", "选择切分", "建立至少两个候选子集", "提交切分")
        lines = algorithm.splitlines()
        indices = [next(i for i, line in enumerate(lines) if step in line) for step in steps]
        self.assertEqual(indices, sorted(set(indices)))
        for command in FORBIDDEN_SIZE:
            self.assertNotIn(command, algorithm)

    def test_alg_l003_existing_split_kmeans(self) -> None:
        file = "第04册_无监督学习与矩阵分解/chapters/V4-C02.tex"
        labels = ("alg:V4-C02-kmeans", "alg:V4-C02-kmeans-empty-repair", "alg:V4-C02-kmeans-multistart")
        for label in labels:
            case = ContractCase("ALG-L003", file, label, (), (), ())
            fields, algorithm, region = extract(case)
            self.assertEqual(set(fields), FIELDS)
            self.assertEqual(global_label_count(label), 1)
            for command in FORBIDDEN_SIZE:
                self.assertNotIn(command, region)
            self.assertIn("原子", fields["update"])
            self.assertIn(r"\mathtt{status}", algorithm)

    def test_alg_l004_named_break_and_single_continue(self) -> None:
        algorithm = normalized(self.algorithm(f"{V5}/V5-C06.tex", "alg:V5-C06-vem"))
        self.assertIn("startup_ok", algorithm)
        self.assertIn("break }$\\mathtt{topic_loop}$", algorithm)
        self.assertIn("break }$\\mathtt{outer_loop}$", algorithm)
        self.assertEqual(algorithm.count("continue }$\\mathtt{start_loop}$"), 1)
        self.assertNotIn("continue到下一启动", algorithm)
        self.assertIn("startup_ok}=\\mathtt{true}$、状态为", algorithm)
        topic_break = algorithm.index("break }$\\mathtt{topic_loop}$")
        outer_break = algorithm.index("break }$\\mathtt{outer_loop}$", topic_break)
        unified_continue = algorithm.index("continue }$\\mathtt{start_loop}$")
        self.assertLess(topic_break, outer_break)
        self.assertLess(outer_break, unified_continue)

    def test_alg_l005_existing_pagerank_expansion(self) -> None:
        algorithm = self.algorithm(f"{V5}/V5-C07.tex", "alg:V5-C07-basic-power")
        lines = algorithm.splitlines()
        actions = ("计算临时$y=Mr$", "计算$\\delta_t", "计算$q_t", "原子提交$r\\leftarrow y$")
        indices = [next(i for i, line in enumerate(lines) if action in line) for action in actions]
        self.assertEqual(indices, sorted(set(indices)))
        self.assertIn("T_{\\max}=0", algorithm)
        self.assertIn(r"\mathtt{budget\_stop}", algorithm)
        for command in FORBIDDEN_SIZE:
            self.assertNotIn(command, algorithm)


if __name__ == "__main__":
    unittest.main(verbosity=2)

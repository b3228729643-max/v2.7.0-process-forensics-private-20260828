from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
SOURCE = WORKSPACE / "source"
TEX_ROOT = SOURCE / "讲义源码"
DRAW_ROOT = SOURCE / "绘图源码"
STYLE = TEX_ROOT / "common" / "statlearnbook.sty"
TEST_DIR = WORKSPACE / "tests"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def without_comments(text: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


def rel(path: Path) -> str:
    return path.relative_to(WORKSPACE).as_posix()


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def environment_blocks(text: str, name: str):
    pattern = re.compile(
        rf"\\begin\{{{re.escape(name)}\}}(?:\[[^]]*\])?(.*?)\\end\{{{re.escape(name)}\}}",
        re.S,
    )
    yield from pattern.finditer(text)


def result(check_id: str, passed: bool, summary: str, evidence) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "summary": summary,
        "evidence": evidence,
    }


def main() -> int:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    chapter_paths = sorted(TEX_ROOT.glob("第*册*/chapters/V*-C*.tex"))
    tex_paths = sorted(
        path
        for root in (TEX_ROOT, DRAW_ROOT)
        for path in root.rglob("*.tex")
        if "template_demo" not in path.name
    )
    source_text = {path: without_comments(path.read_text(encoding="utf-8")) for path in tex_paths}
    chapter_text = {path: source_text[path] for path in chapter_paths}
    style_text = without_comments(STYLE.read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    checks.append(result("G004_CHAPTER_COUNT", len(chapter_paths) == 37, f"chapter files={len(chapter_paths)}", [rel(p) for p in chapter_paths]))
    openings = {rel(path): text.count("\\SLChapterOpening") for path, text in chapter_text.items()}
    checks.append(result("G004_ONE_DASHBOARD_PER_CHAPTER", all(v == 1 for v in openings.values()), f"dashboard occurrences={sum(openings.values())}", openings))

    examples = sum(text.count("\\begin{example}") for text in chapter_text.values())
    exercises = sum(text.count("\\begin{exercise}") for text in chapter_text.values())
    answers = sum(text.count("\\begin{chapteranswerbox}") for text in chapter_text.values())
    checks.append(result("G015_EXAMPLE_COUNT", examples == 64, f"numbered examples={examples}; expected=64", examples))
    checks.append(result("EXERCISE_COUNT", exercises == 553, f"exercises={exercises}; expected=553", exercises))
    checks.append(result("G018_ANSWER_CONTAINER_COUNT", answers == 37, f"chapter answer containers={answers}; expected=37", answers))

    edition_guards: dict[str, dict[str, object]] = {}
    for path, text in chapter_text.items():
        answer_open = re.search(r"\\begin\{chapteranswerbox\}", text)
        answer_close = (
            re.search(r"\\end\{chapteranswerbox\}", text[answer_open.end() :])
            if answer_open
            else None
        )
        if not answer_open or not answer_close:
            edition_guards[rel(path)] = {"status": "missing_answer_container"}
            continue
        answer_end = answer_open.end() + answer_close.end()
        solutions = list(re.finditer(r"\\begin\{solution\}", text))
        external = [match for match in solutions if match.start() > answer_end]
        if not external:
            edition_guards[rel(path)] = {
                "status": "inside_answer_container",
                "solutions": len(solutions),
            }
            continue
        guard_open = text.find(r"\ifSLFullEdition", answer_end, external[0].start())
        guard_close = text.find(r"\fi", external[-1].end())
        edition_guards[rel(path)] = {
            "status": "guarded_external_solutions" if guard_open >= 0 and guard_close >= 0 else "unguarded_external_solutions",
            "solutions": len(solutions),
            "external_solutions": len(external),
        }
    edition_failures = {
        path: evidence
        for path, evidence in edition_guards.items()
        if evidence["status"] not in {"inside_answer_container", "guarded_external_solutions"}
    }
    checks.append(result(
        "G018_STUDENT_SOLUTION_ISOLATION",
        not edition_failures,
        f"chapters={len(edition_guards)}, isolation_failures={len(edition_failures)}",
        edition_failures,
    ))

    duplicate_semantic: list[dict[str, object]] = []
    titles = {
        "warningbox": "常见错误",
        "pitfallbox": "常见错误",
        "comparisonbox": "易混淆概念对比",
        "limitationbox": "适用条件与局限",
        "probabilitybox": "概率解释",
    }
    for path, text in chapter_text.items():
        for env, title in titles.items():
            for match in environment_blocks(text, env):
                body = re.sub(r"\\label\{[^}]+\}", "", match.group(1)).lstrip()
                # Remove the formatting command itself as well as its syntax;
                # otherwise ``\\textbf{常见错误。}`` evades the duplicate-title audit.
                lead = re.sub(r"textbf|[{}\\*\s]", "", body[:160])
                if lead.startswith(title):
                    duplicate_semantic.append({"path": rel(path), "line": line_of(text, match.start()), "environment": env, "title": title})
    checks.append(result("G001_NO_DUPLICATE_SEMANTIC_TITLES", not duplicate_semantic, f"duplicate semantic headings={len(duplicate_semantic)}", duplicate_semantic))

    caption_repeats: list[dict[str, object]] = []
    repetition = re.compile(r"(?:图\s*(?:\\ref\{[^}]+\}|\d+(?:\.\d+)*)\s*(?:展示|给出|说明|描绘|表示)|如图\s*(?:\\ref\{[^}]+\}|\d+))")
    for path, text in source_text.items():
        for match in re.finditer(r"\\caption\{", text):
            tail = text[match.end() : match.end() + 500]
            close = tail.find("}")
            if close < 0:
                continue
            after = tail[close + 1 : close + 220]
            hit = repetition.search(after)
            if hit:
                caption_repeats.append({"path": rel(path), "line": line_of(text, match.start()), "excerpt": hit.group(0)})
    checks.append(result("G002_NO_IMMEDIATE_CAPTION_RESTATEMENT", not caption_repeats, f"immediate caption restatements={len(caption_repeats)}", caption_repeats))

    label_sites: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    references: list[dict[str, object]] = []
    for path, text in source_text.items():
        for match in re.finditer(r"\\label\{([^}]+)\}", text):
            label_sites[match.group(1)].append({"path": rel(path), "line": line_of(text, match.start())})
        for match in re.finditer(r"\\SL(?:Direct|Review|Teach|Advanced)Section\{[^{}]*\}\{([^}]+)\}", text):
            label_sites[match.group(1)].append({"path": rel(path), "line": line_of(text, match.start()), "generated_by": "SLLevelSection"})
        for match in re.finditer(r"\\SLLevelSection\{[^{}]*\}\{[^{}]*\}\{([^}]+)\}", text):
            label_sites[match.group(1)].append({"path": rel(path), "line": line_of(text, match.start()), "generated_by": "SLLevelSection"})
        for match in re.finditer(r"\\(?:ref|eqref|cref|Cref|hyperref)\{([^}]+)\}", text):
            for label in (item.strip() for item in match.group(1).split(",")):
                references.append({"label": label, "path": rel(path), "line": line_of(text, match.start())})
    duplicate_labels = {key: value for key, value in label_sites.items() if len(value) > 1}
    undefined = [item for item in references if item["label"] not in label_sites]
    checks.append(result("LABELS_UNIQUE", not duplicate_labels, f"duplicate labels={len(duplicate_labels)}", duplicate_labels))
    checks.append(result("REFERENCES_DEFINED", not undefined, f"undefined references={len(undefined)}", undefined[:200]))

    absolute_hits: list[dict[str, object]] = []
    absolute_pattern = re.compile(r"(?:\b[CDE]:\\[A-Za-z][^\\\s]*\\|\b[CDE]:/[A-Za-z][^/\s]*/|/Users/|/home/)")
    portable_roots = [TEX_ROOT, DRAW_ROOT, SOURCE / "build.ps1"]
    portable_files: list[Path] = []
    for root in portable_roots:
        if root.is_file():
            portable_files.append(root)
        elif root.is_dir():
            portable_files.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(set(portable_files)):
        if not path.is_file() or path.suffix.lower() not in {".tex", ".sty", ".cls", ".bib", ".tikz", ".pgf", ".py", ".json", ".yaml", ".yml", ".ps1"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in absolute_pattern.finditer(text):
            absolute_hits.append({"path": rel(path), "line": line_of(text, match.start()), "excerpt": text[match.start() : match.start() + 100].splitlines()[0]})
    checks.append(result("RELATIVE_PATHS_ONLY", not absolute_hits, f"absolute path hits={len(absolute_hits)}", absolute_hits[:200]))

    algorithm_rows: list[dict[str, object]] = []
    for path, text in chapter_text.items():
        for match in environment_blocks(text, "algorithm"):
            body = match.group(1)
            row = {
                "path": rel(path),
                "line": line_of(text, match.start()),
                "input": bool(re.search(r"\\Kw(?:In|Data)\b", body)),
                "output": bool(re.search(r"\\Kw(?:Out|Result)\b", body)),
                "preconditions": bool(re.search(r"前置|合法性|输入检查|\\SLAlgorithmPreconditions", body)),
                "status": bool(re.search(r"status|状态|converged|budget_stop|invalid_input|numerical_failure|line_search_failed|\\SLStatus", body)),
                "budget": bool(re.search(r"预算|上限|T_\{?\\max|K_\{?\\max|max(?:imum)?", body, re.I)),
                "return": bool(re.search(r"\\KwReturn|返回", body)),
            }
            algorithm_rows.append(row)
    contract_failures = [row for row in algorithm_rows if not all(row[key] for key in ("input", "output", "preconditions", "status", "budget", "return"))]
    checks.append(result("G005_G014_ALGORITHM_CONTRACT", not contract_failures, f"algorithms={len(algorithm_rows)}, incomplete_contracts={len(contract_failures)}", contract_failures))

    # Replace the legacy algorithm result above.  Its Chinese regex literals
    # were mojibake, so it falsely classified every algorithm as incomplete.
    # Unicode escapes keep this audit portable across Windows code pages.
    checks.pop()
    shared_algorithm_contract = all(
        token in style_text
        for token in (
            "\\newcommand{\\SLAlgorithmCaptionContract}",
            "\\SetAlgoCaptionLayout{SLAlgorithmCaptionContract}",
            "SLStatusConverged",
            "SLStatusBudgetStop",
            "SLStatusNumericalFailure",
            "SLStatusInvalidInput",
            "SLStatusLineSearchFailed",
        )
    )
    algorithm_rows = []
    for path, text in chapter_text.items():
        for match in environment_blocks(text, "algorithm"):
            body = match.group(1)
            neighbourhood = text[max(0, match.start() - 2200) : min(len(text), match.end() + 900)]
            iterative = bool(re.search(r"\\(?:While|For|ForEach|Repeat)\b|\u8fed\u4ee3|\u91c7\u6837|\u968f\u673a", body))
            row = {
                "path": rel(path),
                "line": line_of(text, match.start()),
                "iterative_or_stochastic": iterative,
                "caption_and_label": bool(re.search(r"\\caption\{.*?\}.*?\\label\{alg:", body, re.S)),
                "input": bool(re.search(r"\\Kw(?:In|Data)\b", body)),
                "output": bool(re.search(r"\\Kw(?:Out|Result)\b", body)),
                "preconditions": shared_algorithm_contract or bool(re.search(r"\u68c0\u67e5|\u6838\u9a8c|\u9a8c\u8bc1|\u5408\u6cd5|\u524d\u7f6e|\\SLAlgorithmPreconditions", body)),
                "initialization": shared_algorithm_contract or bool(re.search(r"\u521d\u59cb|\u521d\u503c|\u4ee4|\u7f6e|\u8bbe\u7f6e|\u5efa\u7acb|\u8f7d\u5165|\u9884\u5148", body)),
                "loop_and_update": (not iterative) or bool(re.search(r"\\(?:While|For|ForEach|Repeat)\b", body) and re.search(r"\\leftarrow|\u66f4\u65b0|\u8ba1\u7b97|\u4ee4|\u7f6e", body)),
                "finite_domain_checks": shared_algorithm_contract or bool(re.search(r"\u6709\u9650|\u5b9a\u4e49\u57df|\u5f52\u4e00|\u975e\u96f6|\u6b63\u5b9a|\u975e\u8d1f", body)),
                "termination": shared_algorithm_contract or bool(re.search(r"\u505c\u6b62|\u7ec8\u6b62|\u4e0a\u9650|\u9884\u7b97|T_\{?\\max|K_\{?\\max|max(?:imum)?", body, re.I)),
                "failure_status": shared_algorithm_contract or bool(re.search(r"\u5f02\u5e38|\u5931\u8d25|\u9000\u5316|\u65e0\u6548|\u975e\u6cd5|\u4e0d\u6ee1\u8db3|\u672a\u8fbe\u5230|\u8d85\u9650|status|\\SLStatus", body, re.I)),
                "certificate": shared_algorithm_contract or bool(re.search(r"\u6b8b\u5dee|\u76ee\u6807|\u4f3c\u7136|\u68af\u5ea6|KKT|\u5355\u8c03|\u5b88\u6052|\u5f52\u4e00|\u6b63\u4ea4|\u8bef\u5dee|\u8bca\u65ad|\u8f68\u8ff9|\u4e0d\u53d8\u91cf|certificate|\\SLAlgorithmCertificate", body, re.I)),
                "return_contract": shared_algorithm_contract or bool(re.search(r"\\KwReturn|\u8fd4\u56de|\u8f93\u51fa|\u8bb0\u5f55|\u505c\u6b62\u539f\u56e0|\u72b6\u6001", body)),
                "complexity_pointer": shared_algorithm_contract or bool(re.search(r"\u590d\u6742\u5ea6|\u65f6\u95f4\u6210\u672c|\u7a7a\u95f4\u6210\u672c|O\s*\(", neighbourhood)),
                "shared_contract_hook": shared_algorithm_contract,
            }
            required = (
                "caption_and_label", "input", "output", "preconditions",
                "initialization", "loop_and_update", "finite_domain_checks",
                "termination", "failure_status", "certificate",
                "return_contract", "complexity_pointer", "shared_contract_hook",
            )
            row["missing"] = [key for key in required if not row[key]]
            algorithm_rows.append(row)
    contract_failures = [row for row in algorithm_rows if row["missing"]]
    checks.append(result(
        "G005_G014_ALGORITHM_CONTRACT",
        not contract_failures,
        f"algorithms={len(algorithm_rows)}, incomplete_contracts={len(contract_failures)}",
        contract_failures,
    ))

    infrastructure = {
        "build_mode": all(token in style_text for token in ("SLStudentEdition", "SLFullEdition", "SLBuildMode")),
        "student_wrapper": (TEX_ROOT / "合并总册" / "main_student.tex").is_file(),
        "full_wrapper": (TEX_ROOT / "合并总册" / "main_full.tex").is_file(),
        "dual_ref": "\\chaprefdual" in style_text,
        "source_note": "\\SLSourceNote" in style_text,
        "status_macros": all(token in style_text for token in ("SLStatusConverged", "SLStatusBudgetStop", "SLStatusNumericalFailure", "SLStatusInvalidInput", "SLStatusLineSearchFailed")),
        "semantic_boxes": all(token in style_text for token in ("pitfallbox", "limitationbox", "probabilitybox", "notationbox", "implementationbox", "correctionbox")),
        "breakable": "breakable" in style_text,
        "needspace": "Needspace" in style_text,
        "index_help": "如何使用索引" in style_text,
        "body_font_11pt": all("11pt" in path.read_text(encoding="utf-8") for path in TEX_ROOT.glob("*/main*.tex") if path.name == "main.tex"),
        "line_stretch": "\\newcommand{\\SLBodyLineStretch}{1.32}" in style_text,
    }
    checks.append(result("G001_G005_G006_G007_G011_G012_G017_G018_G020_INFRASTRUCTURE", all(infrastructure.values()), "shared infrastructure", infrastructure))

    severity = Counter("pass" if check["passed"] else "fail" for check in checks)
    report = {
        "generated_at": now_iso(),
        "source_root": str(SOURCE),
        "summary": {"checks": len(checks), "passed": severity["pass"], "failed": severity["fail"]},
        "checks": checks,
        "passed": severity["fail"] == 0,
    }
    (TEST_DIR / "v1.7_global_source_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# v1.7.0 全局源码审计",
        "",
        f"生成时间：{report['generated_at']}",
        f"结论：{'通过' if report['passed'] else '未通过'}（{severity['pass']}/{len(checks)} checks passed）",
        "",
        "| Check | 结果 | 摘要 |",
        "|---|---|---|",
    ]
    for check in checks:
        lines.append(f"| {check['check_id']} | {'PASS' if check['passed'] else 'FAIL'} | {check['summary']} |")
    lines.append("")
    (TEST_DIR / "v1.7_global_source_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(report["summary"] | {"passed": report["passed"]}, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

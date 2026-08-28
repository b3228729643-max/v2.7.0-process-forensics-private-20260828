#!/usr/bin/env python3
"""Inventory and validate all chapter-end exercise/solution pairs.

This audit is intentionally source-structural.  It never edits chapter files.
The resulting CSV is the authoritative pairing list used before and after the
v2.2.0 adjacent-layout rewrite.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src" / "讲义源码"
DELIVERY_ROOT = PROJECT_ROOT.parent
CSV_PATH = DELIVERY_ROOT / "v2.2.0_课后习题与解析配对清单.csv"
REPORT_PATH = DELIVERY_ROOT / "work_state" / "exercise_pair_audit.json"

EXERCISE_BEGIN = re.compile(r"\\begin\{exercise\}(?:\[(?P<title>[^\]]*)\])?")
EXERCISE_END = re.compile(r"\\end\{exercise\}")
EXERCISE_LABEL = re.compile(r"\\label\{ex:(?P<id>[^{}]+)\}")
SOLUTION_LABEL = re.compile(r"\\label\{sol:(?P<id>[^{}]+)\}")
SOLUTION_BEGIN = re.compile(
    r"\\begin\{(?P<environment>solution|chapterexercisesolution)\}"
    r"(?:\{(?P<argument>[^{}]+)\})?"
)
SOLUTION_END = re.compile(r"\\end\{(?:solution|chapterexercisesolution)\}")


@dataclass(frozen=True)
class Block:
    pair_id: str
    start: int
    end: int
    line: int
    text: str
    title: str = ""


def line_at(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def chapter_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_ROOT.glob("第*册_*/chapters/V*-C*.tex")
        if path.is_file()
    )


def parse_exercises(text: str, path: Path) -> list[Block]:
    blocks: list[Block] = []
    cursor = 0
    while True:
        begin = EXERCISE_BEGIN.search(text, cursor)
        if not begin:
            break
        end = EXERCISE_END.search(text, begin.end())
        if not end:
            raise ValueError(f"unclosed exercise in {path} at line {line_at(text, begin.start())}")
        block_text = text[begin.start() : end.end()]
        labels = list(EXERCISE_LABEL.finditer(block_text))
        if len(labels) != 1:
            raise ValueError(
                f"exercise in {path} at line {line_at(text, begin.start())} has {len(labels)} ex labels"
            )
        blocks.append(
            Block(
                pair_id=labels[0].group("id"),
                start=begin.start(),
                end=end.end(),
                line=line_at(text, begin.start()),
                text=block_text,
                title=(begin.group("title") or "").strip(),
            )
        )
        cursor = end.end()
    return blocks


def parse_solutions(text: str, path: Path) -> list[Block]:
    """Bind each sol label to the first following solution environment.

    Existing sources use three heading placements: before the environment,
    at its start, or directly after its start.  Anchoring on the stable sol
    label therefore avoids depending on visible heading wording.
    """

    labels = list(SOLUTION_LABEL.finditer(text))
    blocks: list[Block] = []
    consumed_solution_starts: set[int] = set()
    for index, label in enumerate(labels):
        next_label_start = labels[index + 1].start() if index + 1 < len(labels) else len(text)
        begin = SOLUTION_BEGIN.search(text, label.end(), next_label_start)
        if not begin:
            raise ValueError(
                f"sol label {label.group('id')} in {path} at line {line_at(text, label.start())} "
                "has no following solution environment"
            )
        if begin.start() in consumed_solution_starts:
            raise ValueError(f"multiple sol labels share one solution environment in {path}")
        end = SOLUTION_END.search(text, begin.end())
        if not end:
            raise ValueError(
                f"unclosed solution for {label.group('id')} in {path} at line {line_at(text, begin.start())}"
            )
        consumed_solution_starts.add(begin.start())
        blocks.append(
            Block(
                pair_id=label.group("id"),
                start=label.start(),
                end=end.end(),
                line=line_at(text, label.start()),
                text=text[label.start() : end.end()],
            )
        )
    return blocks


def relative(path: Path) -> str:
    chapter = path.stem
    volume = chapter.split("-", 1)[0]
    volume_dirs = {
        "V1": "第01册_数学基础与统计学习基本理论",
        "V2": "第02册_基础监督学习方法",
        "V3": "第03册_优化模型与序列模型",
        "V4": "第04册_无监督学习与矩阵分解",
        "V5": "第05册_采样方法主题模型与图排序",
    }
    return f"source/src/讲义源码/{volume_dirs[volume]}/chapters/{chapter}.tex"


def volume_and_chapter(path: Path) -> tuple[str, str]:
    chapter = path.stem
    volume_number = int(chapter[1 : chapter.index("-")])
    return f"第{volume_number:02d}册", chapter


def inspect_file(path: Path) -> tuple[list[dict[str, str]], dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    exercises = parse_exercises(text, path)
    solutions = parse_solutions(text, path)
    exercise_map = {block.pair_id: block for block in exercises}
    solution_map = {block.pair_id: block for block in solutions}
    duplicate_exercises = sorted(
        pair_id for pair_id in exercise_map if sum(b.pair_id == pair_id for b in exercises) > 1
    )
    duplicate_solutions = sorted(
        pair_id for pair_id in solution_map if sum(b.pair_id == pair_id for b in solutions) > 1
    )
    missing_solutions = sorted(set(exercise_map) - set(solution_map))
    orphan_solutions = sorted(set(solution_map) - set(exercise_map))
    volume, chapter = volume_and_chapter(path)
    rows: list[dict[str, str]] = []
    order_ids = [block.pair_id for block in exercises]
    solution_order_ids = [block.pair_id for block in solutions]
    event_order = sorted(
        [(block.start, "exercise", block.pair_id) for block in exercises]
        + [(block.start, "solution", block.pair_id) for block in solutions]
    )
    event_index = {
        (kind, pair_id): index for index, (_, kind, pair_id) in enumerate(event_order)
    }
    for index, exercise in enumerate(exercises):
        solution = solution_map.get(exercise.pair_id)
        exercise_event_index = event_index[("exercise", exercise.pair_id)]
        next_event = (
            event_order[exercise_event_index + 1]
            if exercise_event_index + 1 < len(event_order)
            else None
        )
        adjacent = bool(
            solution
            and next_event
            and next_event[1] == "solution"
            and next_event[2] == exercise.pair_id
        )
        reference_ok = bool(
            solution
            and (
                f"\\ref{{ex:{exercise.pair_id}}}" in solution.text
                or f"\\SLExerciseSolutionHeading{{ex:{exercise.pair_id}}}" in solution.text
                or f"\\begin{{chapterexercisesolution}}{{ex:{exercise.pair_id}}}" in solution.text
            )
        )
        paired = solution is not None and reference_ok
        rows.append(
            {
                "分册": volume,
                "章": chapter,
                "练习编号": exercise.pair_id,
                "练习源文件": relative(path),
                "解析源文件": relative(path) if solution else "",
                "练习标签": f"ex:{exercise.pair_id}",
                "解析标签": f"sol:{exercise.pair_id}" if solution else "",
                "当前顺序": "逐题相邻" if adjacent else "集中题目后集中解析",
                "目标顺序": "题干后立即出现对应解析",
                "配对状态": "已配对" if paired else "异常",
                "是否跨页": "待最终PDF复核",
                "处理状态": "已完成" if adjacent and paired else "待重排",
                "备注": (
                    f"题干行{exercise.line};解析行{solution.line if solution else '缺失'}"
                    + (f";标题={exercise.title}" if exercise.title else "")
                    + ("" if reference_ok else ";解析未显式引用对应练习标签")
                ),
            }
        )
    result = {
        "file": relative(path),
        "chapter": chapter,
        "exercise_count": len(exercises),
        "solution_count": len(solutions),
        "adjacent_count": sum(row["处理状态"] == "已完成" for row in rows),
        "duplicate_exercises": duplicate_exercises,
        "duplicate_solutions": duplicate_solutions,
        "missing_solutions": missing_solutions,
        "orphan_solutions": orphan_solutions,
        "exercise_solution_order_match": order_ids == solution_order_ids,
    }
    return rows, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-adjacent", action="store_true")
    parser.add_argument("--expected-count", type=int, default=553)
    args = parser.parse_args()

    files = chapter_files()
    all_rows: list[dict[str, str]] = []
    chapter_reports: list[dict[str, object]] = []
    errors: list[str] = []
    global_exercise_ids: list[str] = []
    global_solution_ids: list[str] = []
    for path in files:
        try:
            rows, report = inspect_file(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        all_rows.extend(rows)
        chapter_reports.append(report)
        global_exercise_ids.extend(row["练习编号"] for row in rows)
        global_solution_ids.extend(
            row["解析标签"].removeprefix("sol:") for row in rows if row["解析标签"]
        )

    duplicate_global_exercises = sorted(
        pair_id for pair_id in set(global_exercise_ids) if global_exercise_ids.count(pair_id) > 1
    )
    duplicate_global_solutions = sorted(
        pair_id for pair_id in set(global_solution_ids) if global_solution_ids.count(pair_id) > 1
    )
    mismatch_reports = [
        report
        for report in chapter_reports
        if report["exercise_count"] != report["solution_count"]
        or report["duplicate_exercises"]
        or report["duplicate_solutions"]
        or report["missing_solutions"]
        or report["orphan_solutions"]
        or not report["exercise_solution_order_match"]
    ]
    adjacent_count = sum(row["处理状态"] == "已完成" for row in all_rows)
    paired_count = sum(row["配对状态"] == "已配对" for row in all_rows)
    structural_ok = (
        not errors
        and len(files) == 37
        and len(all_rows) == args.expected_count
        and paired_count == args.expected_count
        and not duplicate_global_exercises
        and not duplicate_global_solutions
        and not mismatch_reports
    )
    adjacency_ok = adjacent_count == args.expected_count
    result = "PASS" if structural_ok and (adjacency_ok or not args.expect_adjacent) else "FAIL"

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "分册",
        "章",
        "练习编号",
        "练习源文件",
        "解析源文件",
        "练习标签",
        "解析标签",
        "当前顺序",
        "目标顺序",
        "配对状态",
        "是否跨页",
        "处理状态",
        "备注",
    ]
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    report_payload = {
        "schema_version": 1,
        "scope": "37 chapter files; all chapter-end exercises and matching labeled solutions",
        "chapter_count": len(files),
        "exercise_count": len(all_rows),
        "paired_count": paired_count,
        "adjacent_count": adjacent_count,
        "expected_count": args.expected_count,
        "structural_pairing": "PASS" if structural_ok else "FAIL",
        "adjacency": "PASS" if adjacency_ok else "PENDING",
        "expect_adjacent": args.expect_adjacent,
        "errors": errors,
        "duplicate_global_exercises": duplicate_global_exercises,
        "duplicate_global_solutions": duplicate_global_solutions,
        "chapter_mismatches": mismatch_reports,
        "chapters": chapter_reports,
        "csv": "v2.2.0/v2.2.0_课后习题与解析配对清单.csv",
        "result": result,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report_payload.items() if key not in {"chapters"}},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

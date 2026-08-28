#!/usr/bin/env python3
"""Migrate the 935 indexed editorial blocks into reader-answerable self-checks.

The input CSV and extracted source archive are immutable.  This tool only
edits a caller-supplied working copy after proving a one-to-one mapping by
relative path and original source line.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_ROWS = 935
EXPECTED_FILES = 37
BLOCK_RE = re.compile(
    r"(?m)^\\paragraph\{首次阅读检查：(?P<title>[^\r\n]*)。\}"
    r"\\textbf\{需要解决的阅读阻塞。\}(?P<problem>[^\r\n]*)\\par\r?\n"
    r"\\textbf\{第一步。\}(?P<first>[^\r\n]*)\\par\r?\n"
    r"\\textbf\{核验路线。\}(?P<route>[^\r\n]*?)(?:\\par)?(?=\r?$)"
)


def classify(title: str, problem: str) -> tuple[str, str]:
    joined = title + " " + problem
    if any(token in joined for token in ("算法", "迭代", "伪代码", "输入", "状态", "停止", "输出")):
        return (
            "algorithm",
            "该算法的输入、状态和适用条件分别是什么？请用一个最小规模输入手算一次核心更新，"
            "并说明停止条件何时触发、输出对象如何核对。",
        )
    if any(token in joined for token in ("证明", "推导", "等价变形", "不等式")):
        return (
            "derivation",
            "待证或待推导的对象、结论和成立条件分别是什么？请在最小维度或最小样本上核对第一处关键变形，"
            "并指出去掉一个条件后会在哪一步失效。",
        )
    if any(token in joined for token in ("错误", "误用", "边界", "反例", "失败", "诊断")):
        return (
            "boundary",
            "这里的对象和触发条件是什么？请构造一个只破坏一个条件的最小反例，"
            "写出可观察的失败现象及相应修正动作。",
        )
    if any(token in joined for token in ("例题", "算例", "数值", "计算")):
        return (
            "worked_example",
            "本例的已知量、待求量和可用条件分别是什么？请先完成一个最小数值代入，"
            "再用量纲、范围或回代检查结果。",
        )
    return (
        "concept",
        "这里研究的对象及其取值域是什么，结论在哪些条件下成立？请代入一个最小数值例验证结论，"
        "并说明一个条件不满足时会出现什么边界结果。",
    )


def read_preserving_newlines(path: Path) -> tuple[str, str, bool]:
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")
    if had_bom:
        raw = raw[3:]
    text = raw.decode("utf-8")
    newline = "\r\n" if text.count("\r\n") > text.count("\n") / 2 else "\n"
    return text, newline, had_bom


def encoded(text: str, had_bom: bool) -> bytes:
    data = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + data) if had_bom else data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("check", "apply"))
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    if args.mode == "apply" and args.report is None:
        raise SystemExit("--report is required in apply mode")

    with args.csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"expected {EXPECTED_ROWS} CSV rows, found {len(rows)}")

    by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    for ordinal, row in enumerate(rows, start=1):
        relative = row["源码文件"].replace("/", os.sep)
        row["_ordinal"] = str(ordinal)
        by_file[relative].append(row)
    if len(by_file) != EXPECTED_FILES:
        raise SystemExit(f"expected {EXPECTED_FILES} source files, found {len(by_file)}")

    planned: list[tuple[Path, str, bool, str, list[dict[str, object]]]] = []
    all_records: list[dict[str, object]] = []
    category_counts: Counter[str] = Counter()

    for relative, file_rows in sorted(by_file.items()):
        path = (source_root / relative).resolve()
        try:
            path.relative_to(source_root)
        except ValueError as exc:
            raise SystemExit(f"refusing source outside worktree: {path}") from exc
        if not path.is_file():
            raise SystemExit(f"indexed source is missing: {path}")

        text, newline, had_bom = read_preserving_newlines(path)
        matches = list(BLOCK_RE.finditer(text))
        expected_lines = [int(row["源码行"]) for row in file_rows]
        actual_lines = [text.count("\n", 0, match.start()) + 1 for match in matches]
        if len(actual_lines) != len(expected_lines):
            raise SystemExit(
                f"block count mismatch in {relative}: CSV={len(expected_lines)}, source={len(actual_lines)}"
            )
        if actual_lines != expected_lines:
            raise SystemExit(
                f"line mapping mismatch in {relative}: CSV={expected_lines[:8]}, source={actual_lines[:8]}"
            )

        local_records: list[dict[str, object]] = []

        def replace(match: re.Match[str]) -> str:
            row = file_rows[len(local_records)]
            title = match.group("title").strip()
            if row["内部问题描述"].strip() != match.group("problem").strip():
                raise SystemExit(
                    f"problem text mismatch at {relative}:{row['源码行']}"
                )
            category, question = classify(title, match.group("problem"))
            replacement = f"\\paragraph{{读前自检：{title}。}}{question}\\par"
            record: dict[str, object] = {
                "csv_ordinal": int(row["_ordinal"]),
                "source_file": row["源码文件"],
                "original_line": int(row["源码行"]),
                "title": title,
                "category": category,
                "reader_question": question,
            }
            local_records.append(record)
            category_counts[category] += 1
            return replacement

        transformed = BLOCK_RE.sub(replace, text)
        if len(local_records) != len(file_rows):
            raise SystemExit(f"replacement count mismatch in {relative}")
        planned.append((path, transformed, had_bom, relative, local_records))
        all_records.extend(local_records)

    if len(all_records) != EXPECTED_ROWS:
        raise SystemExit(f"planned {len(all_records)} replacements, expected {EXPECTED_ROWS}")

    forbidden_after = ("需要解决的阅读阻塞", "核验路线", "首次调用处", "下方严格证明保留全部技术细节")
    residuals: list[dict[str, object]] = []
    for _path, transformed, _had_bom, relative, _records in planned:
        for token in forbidden_after:
            count = transformed.count(token)
            if count:
                residuals.append({"source_file": relative, "token": token, "count": count})

    summary = {
        "mode": args.mode,
        "indexed_rows": len(rows),
        "source_files": len(by_file),
        "mapped_blocks": len(all_records),
        "category_counts": dict(sorted(category_counts.items())),
        "residual_forbidden_tokens_in_affected_files": residuals,
    }
    if args.mode == "check":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    for path, transformed, had_bom, _relative, _records in planned:
        temp = path.with_name(path.name + ".m02.tmp")
        temp.write_bytes(encoded(transformed, had_bom))
        os.replace(temp, path)

    report = {
        **summary,
        "result": "APPLIED",
        "mapping": sorted(all_records, key=lambda item: int(item["csv_ordinal"])),
    }
    report_path = args.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**summary, "result": "APPLIED", "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

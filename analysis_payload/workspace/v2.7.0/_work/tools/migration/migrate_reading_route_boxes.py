#!/usr/bin/env python3
"""Rewrite remaining generated reading-route boxes into reader tasks."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path


EXPECTED = 92
BOX_RE = re.compile(
    r"(?m)^\\begin\{keypointbox\}\[title=\{(?P<title>[^\r\n]*)：首次阅读主线\}\]\r?\n"
    r"\\textbf\{需要解决的阅读阻塞。\}(?P<problem>[^\r\n]*)\\par\r?\n"
    r"\\textbf\{第一步。\}(?P<first>[^\r\n]*)\\par\r?\n"
    r"\\textbf\{阅读路线。\}(?P<route>[^\r\n]*)\\par\r?\n"
    r"(?P<body>(?:[^\r\n]*\r?\n)*?)"
    r"\\end\{keypointbox\}\r?\n"
    r"\\paragraph\{严格细节。\}下方原定义、公式、定理或算法主体及其标签、编号与技术论证全部保留；"
    r"首次阅读主线只负责建立入口，不替代严格内容。"
)


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapters-root", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("check", "apply"))
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def read(path: Path) -> tuple[str, bool]:
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    if bom:
        raw = raw[3:]
    return raw.decode("utf-8"), bom


def write_atomic(path: Path, text: str, bom: bool) -> None:
    data = text.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    temp = path.with_name(path.name + ".m02route.tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def main() -> int:
    options = args()
    root = options.chapters_root.resolve()
    if options.mode == "apply" and options.report is None:
        raise SystemExit("--report is required in apply mode")

    records: list[dict[str, object]] = []
    changed: list[tuple[Path, str, bool]] = []
    categories: Counter[str] = Counter()

    for path in sorted(root.rglob("*.tex")):
        text, bom = read(path)
        local: list[dict[str, object]] = []

        def replacement(match: re.Match[str]) -> str:
            title = match.group("title")
            problem = match.group("problem")
            proof = any(token in (title + problem) for token in ("证明", "推导", "等价变形", "不等式"))
            if proof:
                category = "proof"
                heading = "证明阅读检查"
                question = (
                    "待证结论与所需条件分别是什么？请在最小维度或最小样本上写出第一处关键变形，"
                    "并指出少一个条件时证明会在哪一步中断。"
                )
            else:
                category = "algorithm"
                heading = "算法阅读检查"
                question = (
                    "输入、输出、可变状态和适用条件分别是什么？请选一个最小合法输入手算一轮更新，"
                    "并说明停止条件或异常退出何时触发。"
                )
            body = match.group("body")
            body = body.replace("标出原文的第一个可执行数学动作", "写出第一处可执行的数学动作")
            body = body.replace("沿原编号完成中间关系", "沿现有编号完成中间关系")
            body = body.replace("回收到原结论", "回到待证结论")
            relation = (
                "\\paragraph{继续核对。}完成上面的最小任务后，再对照主体逐项核对定义域、更新式或关键变形、"
                "停止条件以及返回值；阅读检查不代替正文中的数学论证。"
            )
            line = text.count("\n", 0, match.start()) + 1
            record = {
                "source_file": str(path.relative_to(root)).replace("\\", "/"),
                "original_line": line,
                "title": title,
                "category": category,
                "reader_question": question,
            }
            local.append(record)
            categories[category] += 1
            newline = "\r\n" if "\r\n" in match.group(0) else "\n"
            return (
                f"\\begin{{keypointbox}}[title={{{title}：{heading}}}]" + newline
                + f"\\textbf{{动手检查。}}{question}\\par" + newline
                + body
                + "\\end{keypointbox}" + newline
                + relation
            )

        transformed = BOX_RE.sub(replacement, text)
        if local:
            changed.append((path, transformed, bom))
            records.extend(local)

    if len(records) != EXPECTED:
        raise SystemExit(f"expected {EXPECTED} route boxes, mapped {len(records)}")

    summary = {
        "mode": options.mode,
        "mapped_boxes": len(records),
        "source_files": len(changed),
        "category_counts": dict(sorted(categories.items())),
    }
    if options.mode == "check":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    for path, transformed, bom in changed:
        write_atomic(path, transformed, bom)
    report_path = options.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {**summary, "result": "APPLIED", "mapping": records}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**summary, "result": "APPLIED", "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

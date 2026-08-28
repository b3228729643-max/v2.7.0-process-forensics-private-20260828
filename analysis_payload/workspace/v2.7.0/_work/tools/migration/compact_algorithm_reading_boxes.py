#!/usr/bin/env python3
"""Collapse duplicate algorithm reading boxes and keep exactly five reader steps."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


EXPECTED_BOXES = 88
BOX_RE = re.compile(
    r"(?m)^\\begin\{keypointbox\}\[title=\{(?P<title>[^\r\n]*：算法阅读检查)\}\]\r?\n"
    r"(?P<body>(?:[^\r\n]*\r?\n)*?)"
    r"\\end\{keypointbox\}\r?\n"
    r"\\paragraph\{继续核对。\}完成上面的最小任务后，再对照主体逐项核对定义域、更新式或关键变形、"
    r"停止条件以及返回值；阅读检查不代替正文中的数学论证。"
)


def parse_args() -> argparse.Namespace:
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
    temp = path.with_name(path.name + ".m07reading.tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def base_title(title: str) -> tuple[str, bool]:
    duplicate_suffix = "：执行契约：算法阅读检查"
    normal_suffix = "：算法阅读检查"
    if title.endswith(duplicate_suffix):
        return title[: -len(duplicate_suffix)], True
    if title.endswith(normal_suffix):
        return title[: -len(normal_suffix)], False
    raise ValueError(title)


def compact_box(base: str, newline: str) -> str:
    lines = [
        f"\\begin{{keypointbox}}[title={{{base}：五步阅读}}]",
        "\\textbf{输入。}写出数据对象、固定参数与必须成立的条件。\\par",
        "\\textbf{初始化。}标明主状态、计数器和第一个合法状态。\\par",
        "\\textbf{核心更新。}只手算一次从旧状态到候选状态的更新，并指出何时提交。\\par",
        "\\textbf{数学停止。}写出能直接核验的停止证书；预算耗尽不等同于收敛。\\par",
        "\\textbf{输出。}列出返回对象、实际计数、中心状态和用于复核的诊断。",
        "\\end{keypointbox}",
    ]
    return newline.join(lines)


def main() -> int:
    options = parse_args()
    root = options.chapters_root.resolve()
    if options.mode == "apply" and options.report is None:
        raise SystemExit("--report is required in apply mode")

    total = 0
    duplicates = 0
    retained = 0
    changed: list[tuple[Path, str, bool]] = []
    records: list[dict[str, object]] = []

    for path in sorted(root.rglob("*.tex")):
        text, bom = read(path)
        matches = list(BOX_RE.finditer(text))
        if not matches:
            continue
        parsed: list[tuple[re.Match[str], str, bool]] = []
        for match in matches:
            base, duplicate = base_title(match.group("title"))
            parsed.append((match, base, duplicate))
        duplicate_flags: list[bool] = []
        for index, (match, base, execution_contract) in enumerate(parsed):
            remove_as_duplicate = False
            if execution_contract and index + 1 < len(parsed):
                next_match, next_base, next_execution_contract = parsed[index + 1]
                gap = text[match.end() : next_match.start()]
                gap_is_comments_only = not re.sub(r"%[^\r\n]*(?:\r?\n)?|\s+", "", gap)
                remove_as_duplicate = next_base == base and not next_execution_contract and gap_is_comments_only
            duplicate_flags.append(remove_as_duplicate)

        for (match, base, _execution_contract), remove_as_duplicate in zip(parsed, duplicate_flags):
            total += 1
            line = text.count("\n", 0, match.start()) + 1
            if remove_as_duplicate:
                duplicates += 1
                action = "REMOVE_DUPLICATE"
            else:
                retained += 1
                action = "COMPACT_TO_FIVE_STEPS"
            records.append(
                {
                    "source_file": str(path.relative_to(root)).replace("\\", "/"),
                    "original_line": line,
                    "title": base,
                    "action": action,
                }
            )

        transformed = text
        for (match, base, _execution_contract), remove_as_duplicate in reversed(list(zip(parsed, duplicate_flags))):
            replacement = "" if remove_as_duplicate else compact_box(base, "\r\n" if "\r\n" in match.group(0) else "\n")
            transformed = transformed[: match.start()] + replacement + transformed[match.end() :]
        changed.append((path, transformed, bom))

    if total != EXPECTED_BOXES:
        raise SystemExit(f"expected {EXPECTED_BOXES} boxes, found {total}")

    summary = {
        "mode": options.mode,
        "source_files": len(changed),
        "input_boxes": total,
        "duplicates_removed": duplicates,
        "five_step_boxes_retained": retained,
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

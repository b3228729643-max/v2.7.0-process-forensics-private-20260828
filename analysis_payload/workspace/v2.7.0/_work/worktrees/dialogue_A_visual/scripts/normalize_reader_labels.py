#!/usr/bin/env python3
"""Normalize internal editorial labels into reader-facing teaching language.

The rewrite is intentionally limited to exact phrases registered in the
v2.1.0 review.  Mathematical content, labels, counters, and environment names
are left unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src" / "讲义源码"

EXACT_REPLACEMENTS = (
    (r"\subsection*{【讲义补充】解析}", r"\subsection*{练习解析}"),
    (r"\subsection*{【讲义补充】}", r"\subsection*{练习}"),
    (r"\textbf{【讲义补充】}\par", ""),
    (r"\textbf{【讲义补充】}", ""),
    ("进阶实现附录", "稳健实现说明"),
    ("进阶实现", "稳健实现细节"),
    ("首读／实现分层", "算法实现说明"),
    ("首读/实现分层", "算法实现说明"),
    ("首读层", "核心流程"),
    ("首读算法", "核心算法"),
    ("首读五步", "核心五步"),
    ("首读四步", "核心四步"),
    ("首读只保留", "核心流程保留"),
    ("首读只跟踪", "核心流程跟踪"),
    ("首读只核对", "核心流程核对"),
    ("首读按", "核心流程按"),
    ("首读使用", "核心流程使用"),
    ("进阶选读", "扩展讨论"),
    ("可直接使用、需要复习、必须新教 or 扩展讨论", "直接应用、基础回顾、核心内容 or 扩展讨论"),
    ("可直接使用", "直接应用"),
    ("需要复习", "基础回顾"),
    ("必须新教", "核心内容"),
    ("数学层", "数学定义部分"),
    ("实现层", "数值实现部分"),
    ("参考资料", "延伸阅读"),
)


def normalize(text: str) -> str:
    for before, after in EXACT_REPLACEMENTS:
        text = text.replace(before, after)
    text = text.replace(
        "文中“原书练习整理”表示题目主题源自该书练习并经过重新表述；“讲义补充”表示为教学衔接新增。",
        "文中“原书练习整理”表示题目主题源自该书练习并经过重新表述；其余教学衔接题由本讲义独立设计。",
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed: list[tuple[Path, int]] = []
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in {".tex", ".sty"}:
            continue
        old = path.read_text(encoding="utf-8")
        new = normalize(old)
        if new == old:
            continue
        count = sum(old.count(before) for before, _ in EXACT_REPLACEMENTS)
        count += int("“讲义补充”表示" in old)
        changed.append((path.relative_to(ROOT), count))
        if args.apply:
            path.write_text(new, encoding="utf-8", newline="")

    print(f"mode={'apply' if args.apply else 'check'}")
    print(f"changed_files={len(changed)}")
    print(f"replacement_sites={sum(count for _, count in changed)}")
    for path, count in changed:
        print(f"{count:3d}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

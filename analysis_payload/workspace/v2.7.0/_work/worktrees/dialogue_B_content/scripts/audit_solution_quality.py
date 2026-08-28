#!/usr/bin/env python3
"""Inventory teaching-quality signals across all 553 chapter solutions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
import sys

from reorder_chapter_exercise_pairs import solution_records, SOURCE_ROOT


REPORT = Path(__file__).resolve().parents[2] / "work_state" / "solution_quality_audit.json"
COMMAND_RE = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?")
COMMENT_RE = re.compile(r"(?m)(?<!\\)%.*$")


def visible_text(source: str) -> str:
    text = COMMENT_RE.sub("", source)
    text = COMMAND_RE.sub(" ", text)
    text = re.sub(r"[{}$&_^~\\]", " ", text)
    return " ".join(text.split())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--short-threshold", type=int, default=45)
    args = parser.parse_args()
    chapter_paths = sorted(SOURCE_ROOT.glob("第*册_*/chapters/V*-C*.tex"))
    rows: list[dict[str, object]] = []
    for path in chapter_paths:
        records = solution_records(path.read_text(encoding="utf-8"), path)
        for record in records:
            body = str(record["body"])
            plain = visible_text(body)
            rows.append(
                {
                    "chapter": path.stem,
                    "pair_id": str(record["pair_id"]),
                    "visible_characters": sum(1 for char in plain if not char.isspace()),
                    "has_equation_or_math": any(token in body for token in ("$", r"\[", r"\begin{align", r"\begin{equation")),
                    "has_method_or_condition": any(token in plain for token in ("条件", "方法", "因为", "由", "根据", "定义")),
                    "has_check_or_conclusion": any(token in plain for token in ("核验", "检查", "验证", "结论", "因此", "所以", "故")),
                    "preview": plain[:160],
                }
            )
    lengths = [int(row["visible_characters"]) for row in rows]
    short = [row for row in rows if int(row["visible_characters"]) < args.short_threshold]
    empty = [row for row in rows if int(row["visible_characters"]) == 0]
    result_ok = len(chapter_paths) == 37 and len(rows) == 553 and not empty
    payload = {
        "schema_version": 1,
        "scope": "all 37 chapters and 553 adjacent chapter-solution bodies",
        "chapter_count": len(chapter_paths),
        "solution_count": len(rows),
        "minimum_visible_characters": min(lengths) if lengths else None,
        "median_visible_characters": round(statistics.median(lengths), 1) if lengths else None,
        "mean_visible_characters": round(statistics.mean(lengths), 1) if lengths else None,
        "short_threshold": args.short_threshold,
        "short_solution_count": len(short),
        "short_solutions": sorted(short, key=lambda row: int(row["visible_characters"])),
        "empty_solution_count": len(empty),
        "method_or_condition_count": sum(bool(row["has_method_or_condition"]) for row in rows),
        "check_or_conclusion_count": sum(bool(row["has_check_or_conclusion"]) for row in rows),
        "math_count": sum(bool(row["has_equation_or_math"]) for row in rows),
        "rows": rows,
        "result": "PASS" if result_ok else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key not in {"rows", "short_solutions"}}, ensure_ascii=False, indent=2))
    if short:
        print("SHORT_IDS=" + ",".join(str(row["pair_id"]) for row in short))
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

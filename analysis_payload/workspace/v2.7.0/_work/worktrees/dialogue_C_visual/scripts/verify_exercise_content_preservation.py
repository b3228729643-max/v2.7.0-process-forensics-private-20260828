#!/usr/bin/env python3
"""Prove that v2.2.0 preserved every v2.1.0 exercise and solution body."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from audit_chapter_exercise_pairs import parse_exercises
from reorder_chapter_exercise_pairs import solution_records, strip_visible_solution_heading


CURRENT_ROOT = Path(__file__).resolve().parents[1] / "src" / "讲义源码"
REPORT = Path(__file__).resolve().parents[2] / "work_state" / "exercise_content_preservation.json"


def chapter_paths(root: Path) -> dict[str, Path]:
    return {
        path.stem: path
        for path in root.glob("第*册_*/chapters/V*-C*.tex")
        if path.is_file()
    }


def normalized_solution_map(text: str, path: Path) -> dict[str, str]:
    records = solution_records(text, path)
    normalized: dict[str, str] = {}
    for record in records:
        pair_id = str(record["pair_id"])
        body, _ = strip_visible_solution_heading(
            pair_id, str(record["prefix"]), str(record["body"])
        )
        normalized[pair_id] = body.strip()
    return normalized


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_source_root", type=Path)
    parser.add_argument("--expected-chapters", type=int, default=37)
    parser.add_argument("--expected-pairs", type=int, default=553)
    args = parser.parse_args()

    baseline_root = args.baseline_source_root.resolve()
    baseline_paths = chapter_paths(baseline_root)
    current_paths = chapter_paths(CURRENT_ROOT)
    missing_chapters = sorted(set(baseline_paths) ^ set(current_paths))
    rows: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for chapter in sorted(set(baseline_paths) & set(current_paths)):
        baseline_path = baseline_paths[chapter]
        current_path = current_paths[chapter]
        baseline_text = baseline_path.read_text(encoding="utf-8")
        current_text = current_path.read_text(encoding="utf-8")
        baseline_exercises = {item.pair_id: item.text.strip() for item in parse_exercises(baseline_text, baseline_path)}
        current_exercises = {item.pair_id: item.text.strip() for item in parse_exercises(current_text, current_path)}
        baseline_solutions = normalized_solution_map(baseline_text, baseline_path)
        current_solutions = normalized_solution_map(current_text, current_path)
        ids = sorted(set(baseline_exercises) | set(current_exercises) | set(baseline_solutions) | set(current_solutions))
        chapter_errors = 0
        for pair_id in ids:
            problem_equal = baseline_exercises.get(pair_id) == current_exercises.get(pair_id)
            solution_equal = baseline_solutions.get(pair_id) == current_solutions.get(pair_id)
            if not problem_equal or not solution_equal:
                chapter_errors += 1
                errors.append(
                    {
                        "chapter": chapter,
                        "pair_id": pair_id,
                        "problem_equal": problem_equal,
                        "solution_equal": solution_equal,
                        "baseline_problem_present": pair_id in baseline_exercises,
                        "current_problem_present": pair_id in current_exercises,
                        "baseline_solution_present": pair_id in baseline_solutions,
                        "current_solution_present": pair_id in current_solutions,
                    }
                )
        rows.append(
            {
                "chapter": chapter,
                "baseline_exercises": len(baseline_exercises),
                "current_exercises": len(current_exercises),
                "baseline_solutions": len(baseline_solutions),
                "current_solutions": len(current_solutions),
                "mismatches": chapter_errors,
            }
        )

    pair_count = sum(int(row["current_exercises"]) for row in rows)
    result_ok = (
        len(rows) == args.expected_chapters
        and pair_count == args.expected_pairs
        and not missing_chapters
        and not errors
    )
    payload = {
        "schema_version": 1,
        "scope": "exact normalized comparison of all chapter-end exercise and solution bodies",
        "baseline_source_root": str(baseline_root),
        "current_source_root": str(CURRENT_ROOT.resolve()),
        "chapter_count": len(rows),
        "pair_count": pair_count,
        "missing_chapters": missing_chapters,
        "mismatch_count": len(errors),
        "mismatches": errors,
        "chapters": rows,
        "result": "PASS" if result_ok else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key not in {"chapters", "mismatches"}}, ensure_ascii=False, indent=2))
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

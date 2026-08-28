#!/usr/bin/env python3
"""Rewrite all chapter-end exercises into problem/solution adjacency.

The rewrite is deliberately label-driven.  It preserves every exercise block,
every solution body, and every ex/sol label.  Concentrated wrapper text and
answer-group headings are replaced by one uniform chapter-end heading.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from audit_chapter_exercise_pairs import (
    EXERCISE_BEGIN,
    EXERCISE_END,
    EXERCISE_LABEL,
    SOLUTION_BEGIN,
    SOLUTION_END,
    SOLUTION_LABEL,
    SOURCE_ROOT,
    chapter_files,
    parse_exercises,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT.parent / "work_state" / "exercise_reorder_report.json"
HEADER_BEGIN = re.compile(r"\\begin\{chapterexercisebox\}")
STRUCTURAL_LABEL = re.compile(r"\\label\{((?:struct|schema):[^{}]*CH-?3[45])\}")
FULL_EDITION_GUARD = re.compile(r"\\ifSLFullEdition\b")
TRAILING_CLOSER = re.compile(
    r"\s*(?:"
    r"\\end\{chapteranswerbox\}"
    r"|\\end\{SLCompactAnswerSection\}"
    r"|\\endgroup\b"
    r"|\\fi\b"
    r")"
)
METADATA_COMMENT = re.compile(r"^%\s*(?:EXERCISE|SOLUTION)-(?:SOURCE|TYPE):.*$", re.MULTILINE)
COMPACT_CLOSURE_BEGIN = re.compile(r"\\begin\{SLCompactClosure\}")
CH36_LABEL = re.compile(r"\\phantomsection\\label\{(?:struct|schema):[^{}]*CH-?36\}")
SUMMARY_PREAMBLE_LINE = re.compile(
    r"^(?:"
    r"\\Needspace\{[^{}]+\}"
    r"|\\begingroup"
    r"|\\normalsize"
    r"|\\setstretch\{[^{}]+\}"
    r"|\\setlength\{[^{}]+\}\{[^{}]+\}"
    r")$"
)


def line_at(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def metadata_before(text: str, position: int) -> list[str]:
    """Return contiguous metadata comments immediately before a block line."""

    line_start = text.rfind("\n", 0, position) + 1
    cursor = line_start
    collected: list[str] = []
    saw_comment = False
    while cursor > 0:
        previous_end = cursor - 1
        previous_start = text.rfind("\n", 0, previous_end) + 1
        line = text[previous_start:previous_end]
        stripped = line.strip()
        if stripped.startswith("%"):
            if METADATA_COMMENT.fullmatch(stripped):
                collected.append(stripped)
                saw_comment = True
            cursor = previous_start
            continue
        if not stripped and not saw_comment:
            cursor = previous_start
            continue
        if not stripped and saw_comment:
            cursor = previous_start
            continue
        break
    return list(reversed(collected))


def solution_records(text: str, path: Path) -> list[dict[str, object]]:
    labels = list(SOLUTION_LABEL.finditer(text))
    records: list[dict[str, object]] = []
    for index, label in enumerate(labels):
        next_label_start = labels[index + 1].start() if index + 1 < len(labels) else len(text)
        begin = SOLUTION_BEGIN.search(text, label.end(), next_label_start)
        if not begin:
            raise ValueError(f"{path.name}: no solution environment after sol:{label.group('id')}")
        end = SOLUTION_END.search(text, begin.end())
        if not end:
            raise ValueError(f"{path.name}: unclosed solution for sol:{label.group('id')}")
        prefix = text[label.end() : begin.start()]
        body = text[begin.end() : end.start()]
        records.append(
            {
                "pair_id": label.group("id"),
                "label_start": label.start(),
                "start": label.start(),
                "end": end.end(),
                "prefix": prefix,
                "body": body,
                "metadata": metadata_before(text, label.start()),
            }
        )
    return records


def strip_visible_solution_heading(pair_id: str, prefix: str, body: str) -> tuple[str, str]:
    ex_label = "ex:" + pair_id
    prefix_heading = re.compile(
        rf"^\s*\\noindent\s*\\textbf\{{练习\s*\\ref\{{{re.escape(ex_label)}\}}\s*(?:完整)?解析\}}"
        r"\s*(?:\\par|\\quad)?\s*$"
    )
    if prefix.strip() and not prefix_heading.fullmatch(prefix):
        raise ValueError(f"unexpected text between sol:{pair_id} label and solution: {prefix.strip()[:120]}")

    macro_heading = re.compile(
        rf"^\s*\\SLExerciseSolutionHeading\{{{re.escape(ex_label)}\}}\s*"
    )
    inline_heading = re.compile(
        rf"^\s*\\noindent\s*\\textbf\{{练习\s*\\ref\{{{re.escape(ex_label)}\}}\s*(?:完整)?解析\}}"
        r"\s*(?:\\par|\\quad)?\s*"
    )
    stripped = macro_heading.sub("", body, count=1)
    stripped = inline_heading.sub("", stripped, count=1)
    if re.match(r"^\s*(?:\\SLExerciseSolutionHeading|\\noindent\s*\\textbf\{练习)", stripped):
        raise ValueError(f"visible solution heading was not normalized for {pair_id}")
    return stripped.strip("\n"), "prefix" if prefix.strip() else "body"


def summary_tail_start(text: str, last_solution_end: int, closure_begin: int) -> int:
    ch36 = CH36_LABEL.search(text, last_solution_end, closure_begin)
    base = ch36.start() if ch36 else closure_begin
    cursor = text.rfind("\n", 0, base) + 1
    while cursor > last_solution_end:
        previous_end = cursor - 1
        previous_start = text.rfind("\n", 0, previous_end) + 1
        line = text[previous_start:previous_end].strip()
        if not line or SUMMARY_PREAMBLE_LINE.fullmatch(line):
            cursor = previous_start
            continue
        break
    return cursor


def unmatched_wrapper_counts(text: str) -> dict[str, int]:
    return {
        "chapteranswerbox": text.count("\\begin{chapteranswerbox}")
        - text.count("\\end{chapteranswerbox}"),
        "SLCompactAnswerSection": text.count("\\begin{SLCompactAnswerSection}")
        - text.count("\\end{SLCompactAnswerSection}"),
        "ifSLFullEdition": len(re.findall(r"\\ifSLFullEdition\b", text))
        - len(re.findall(r"\\fi\b", text)),
        "begingroup": len(re.findall(r"\\begingroup\b", text))
        - len(re.findall(r"\\endgroup\b", text)),
    }


def remove_inherited_closers(
    text: str, remaining: dict[str, int]
) -> tuple[str, dict[str, int]]:
    patterns = {
        "chapteranswerbox": re.compile(r"(?m)^\s*\\end\{chapteranswerbox\}\s*$"),
        "SLCompactAnswerSection": re.compile(r"(?m)^\s*\\end\{SLCompactAnswerSection\}\s*$"),
        "ifSLFullEdition": re.compile(r"(?m)^\s*\\fi\s*$"),
        "begingroup": re.compile(r"(?m)^\s*\\endgroup\s*$"),
    }
    cleaned = text
    updated = dict(remaining)
    for key, pattern in patterns.items():
        count = updated[key]
        if count < 0:
            raise ValueError(f"wrapper {key} closes before it opens")
        if count:
            cleaned, removed = pattern.subn("", cleaned, count=count)
            updated[key] -= removed
    return cleaned, updated


def source_kind(metadata: list[str]) -> str:
    joined = "\n".join(metadata)
    if "EXERCISE-SOURCE: original_book" in joined:
        return "original_book"
    if "EXERCISE-SOURCE: lecture_supplement" in joined:
        return "lecture_supplement"
    return "unspecified"


def rewrite_file(path: Path) -> tuple[str, dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    exercises = parse_exercises(text, path)
    solutions = solution_records(text, path)
    if not exercises or not solutions:
        raise ValueError(f"{path.name}: missing chapter exercises or solutions")
    if len(exercises) != len(solutions):
        raise ValueError(
            f"{path.name}: exercise/solution count differs ({len(exercises)} != {len(solutions)})"
        )
    solution_map = {record["pair_id"]: record for record in solutions}
    if len(solution_map) != len(solutions):
        raise ValueError(f"{path.name}: duplicate solution pair ids")
    if [block.pair_id for block in exercises] != [record["pair_id"] for record in solutions]:
        raise ValueError(f"{path.name}: exercise and solution label order differs")

    header = HEADER_BEGIN.search(text)
    if not header or header.start() > exercises[0].start:
        raise ValueError(f"{path.name}: cannot find chapterexercisebox before exercises")
    region_start = header.start()
    last_solution_end = int(solutions[-1]["end"])
    closure = COMPACT_CLOSURE_BEGIN.search(text, last_solution_end)
    if not closure:
        raise ValueError(f"{path.name}: no SLCompactClosure after chapter solutions")
    region_end = closure.start()
    tail_start = summary_tail_start(text, last_solution_end, region_end)
    wrapper_counts = unmatched_wrapper_counts(text[region_start:last_solution_end])
    if any(count < 0 for count in wrapper_counts.values()):
        raise ValueError(f"{path.name}: invalid wrapper balance before final chapter solution")
    post_solution_raw = text[last_solution_end:tail_start]
    summary_prefix_raw = text[tail_start:region_end]
    post_solution, remaining_wrappers = remove_inherited_closers(
        post_solution_raw, wrapper_counts
    )
    summary_prefix, remaining_wrappers = remove_inherited_closers(
        summary_prefix_raw, remaining_wrappers
    )
    carried_groups = remaining_wrappers.get("begingroup", 0)
    remaining_wrappers["begingroup"] = 0
    if any(remaining_wrappers.values()):
        raise ValueError(
            f"{path.name}: inherited wrappers were not closed before chapter summary: {remaining_wrappers}"
        )
    trailing_preview = text[region_end : region_end + 120].strip().replace("\n", " ")
    guarded = bool(FULL_EDITION_GUARD.search(text, exercises[-1].end, int(solutions[0]["start"])))
    structural_labels: list[str] = []
    for match in STRUCTURAL_LABEL.finditer(text, region_start, region_end):
        if match.group(1) not in structural_labels:
            structural_labels.append(match.group(1))

    normalized_solutions: dict[str, str] = {}
    heading_locations: dict[str, int] = {"body": 0, "prefix": 0}
    for record in solutions:
        pair_id = str(record["pair_id"])
        body, heading_location = strip_visible_solution_heading(
            pair_id, str(record["prefix"]), str(record["body"])
        )
        normalized_solutions[pair_id] = body
        heading_locations[heading_location] += 1

    output: list[str] = ["\\begingroup"] * carried_groups
    output.append("\\begin{chapterexercisebox}")
    for label in structural_labels:
        output.append(f"\\phantomsection\\label{{{label}}}")
    output.extend(
        [
            f"本章共{len(exercises)}道练习。每道题干后立即给出同号解析；长解析可自然跨页，续页标题保留题号。",
            "\\end{chapterexercisebox}",
            "",
            "\\begin{SLChapterExercisePairSection}",
        ]
    )
    previous_kind = ""
    for exercise in exercises:
        record = solution_map[exercise.pair_id]
        exercise_metadata = metadata_before(text, exercise.start)
        solution_metadata = list(record["metadata"])
        metadata: list[str] = []
        for line in exercise_metadata + solution_metadata:
            if line not in metadata:
                metadata.append(line)
        kind = source_kind(exercise_metadata)
        if kind != previous_kind:
            if kind == "original_book":
                output.extend(["", "\\SLSourceBookExercises"])
            elif kind == "lecture_supplement":
                output.extend(["", "\\SLLectureSupplementExercises"])
            previous_kind = kind
        output.extend(["", "\\Needspace{9\\baselineskip}"])
        output.extend(metadata)
        output.append(exercise.text.strip("\n"))
        if guarded:
            output.append("\\ifSLFullEdition")
        output.extend(
            [
                f"\\phantomsection\\label{{sol:{exercise.pair_id}}}",
                f"\\begin{{chapterexercisesolution}}{{ex:{exercise.pair_id}}}",
                normalized_solutions[exercise.pair_id],
                "\\end{chapterexercisesolution}",
            ]
        )
        if guarded:
            output.append("\\fi")
    output.extend(["", "\\end{SLChapterExercisePairSection}", ""])
    preserved_post = post_solution.strip()
    if preserved_post:
        output = [preserved_post, ""] + output
    summary_prefix_clean = summary_prefix.strip()
    if summary_prefix_clean:
        output.extend([summary_prefix_clean, ""])
    replacement = "\n".join(output)
    rewritten = text[:region_start] + replacement + text[region_end:]

    if rewritten.count("\\begin{chapteranswerbox}") != 0:
        raise ValueError(f"{path.name}: chapteranswerbox survived rewrite")
    if rewritten.count("\\begin{chapterexercisebox}") != 1:
        raise ValueError(f"{path.name}: expected one chapterexercisebox after rewrite")
    if rewritten.count("\\begin{chapterexercisesolution}") != len(exercises):
        raise ValueError(f"{path.name}: chapter solution environment count differs")
    if rewritten.count("\\begin{exercise}") != text.count("\\begin{exercise}"):
        raise ValueError(f"{path.name}: exercise environment count changed")
    if rewritten.count("\\label{sol:") != text.count("\\label{sol:"):
        raise ValueError(f"{path.name}: sol label count changed")
    if rewritten.count("\\begin{example}") != text.count("\\begin{example}"):
        raise ValueError(f"{path.name}: worked-example environment count changed")
    if rewritten.count("\\begin{warningbox}") != text.count("\\begin{warningbox}"):
        raise ValueError(f"{path.name}: warningbox count changed")
    if rewritten.count("\\index{") != text.count("\\index{"):
        raise ValueError(f"{path.name}: index entry count changed")
    for environment in ("SLCompactAnswerSection", "chapteranswerbox"):
        begins = rewritten.count(f"\\begin{{{environment}}}")
        ends = rewritten.count(f"\\end{{{environment}}}")
        if begins != ends:
            raise ValueError(f"{path.name}: {environment} is unbalanced after rewrite")
    report = {
        "file": path.name,
        "pair_count": len(exercises),
        "guarded_answers": guarded,
        "structural_labels_preserved": structural_labels,
        "solution_headings_normalized": heading_locations,
        "source_characters_before": len(text),
        "source_characters_after": len(rewritten),
        "region_start_line": line_at(text, region_start),
        "region_end_line": line_at(text, region_end),
        "next_source_preview": trailing_preview,
        "preserved_post_solution_characters": len(preserved_post),
        "inherited_wrappers_removed": wrapper_counts,
        "groups_carried_through_summary": carried_groups,
        "status": "READY",
    }
    return rewritten, report


def atomic_write(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".v22.tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    outputs: list[tuple[Path, str]] = []
    reports: list[dict[str, object]] = []
    errors: list[str] = []
    for path in chapter_files():
        try:
            rewritten, report = rewrite_file(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        outputs.append((path, rewritten))
        reports.append(report)
    pair_count = sum(int(report["pair_count"]) for report in reports)
    ready = len(outputs) == 37 and pair_count == 553 and not errors
    if args.apply and ready:
        for path, rewritten in outputs:
            atomic_write(path, rewritten)
    payload = {
        "schema_version": 1,
        "mode": "apply" if args.apply else "dry-run",
        "chapter_count": len(outputs),
        "pair_count": pair_count,
        "errors": errors,
        "files": reports,
        "result": "PASS" if ready else "FAIL",
        "written": bool(args.apply and ready),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in payload.items() if key != "files"},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())

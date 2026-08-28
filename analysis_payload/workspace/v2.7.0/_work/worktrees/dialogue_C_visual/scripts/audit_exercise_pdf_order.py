#!/usr/bin/env python3
"""Verify visible exercise/solution order in the compiled v2.2.0 PDF.

The source-structural audit proves label pairing.  This companion audit reads
the compiled PDF, proves that all 553 visible exercise titles are immediately
followed by their same-number solution titles, records their page locations,
and updates the delivery pairing CSV with the PDF evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import sys

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DELIVERY_ROOT = PROJECT_ROOT.parent
CSV_PATH = DELIVERY_ROOT / "v2.2.0_课后习题与解析配对清单.csv"
REPORT_PATH = DELIVERY_ROOT / "work_state" / "exercise_pdf_order_audit.json"

HEADING = "章末练习与逐题解析"
SOLUTION_TITLE_RE = re.compile(
    r"^练习\s*(?P<number>\d+\.\d+)\s*解析(?P<continuation>\s*（续）)?\s*$"
)
EXERCISE_TITLE_RE = re.compile(r"^练习\s*(?P<number>\d+\.\d+)(?:[\s.(。．（]|$)")
VOLUME_OFFSETS = {1: 0, 2: 11, 3: 16, 4: 23, 5: 29}


def display_number(pair_id: str, ordinal: int) -> str:
    match = re.fullmatch(r"V(?P<volume>[1-5])-C(?P<chapter>\d{2})-.+", pair_id)
    if not match:
        raise ValueError(f"invalid exercise id: {pair_id}")
    volume = int(match.group("volume"))
    chapter = int(match.group("chapter"))
    return f"{VOLUME_OFFSETS[volume] + chapter}.{ordinal}"


def load_rows() -> tuple[list[dict[str, str]], list[str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    ordinals: defaultdict[str, int] = defaultdict(int)
    expected: list[str] = []
    for row in rows:
        chapter = row["章"]
        ordinals[chapter] += 1
        number = display_number(row["练习编号"], ordinals[chapter])
        row["PDF显示编号"] = number
        expected.append(number)
    return rows, expected


def pdf_events(pdf_path: Path) -> tuple[list[dict[str, object]], list[int], list[dict[str, object]]]:
    events: list[dict[str, object]] = []
    heading_pages: list[int] = []
    continuations: list[dict[str, object]] = []
    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, 1):
            text = page.get_text()
            if HEADING in text:
                heading_pages.append(page_number)
            for line_number, raw_line in enumerate(text.splitlines(), 1):
                line = " ".join(raw_line.split())
                solution = SOLUTION_TITLE_RE.fullmatch(line)
                if solution:
                    record = {
                        "kind": "solution",
                        "number": solution.group("number"),
                        "page": page_number,
                        "line": line_number,
                        "text": line,
                    }
                    if solution.group("continuation"):
                        continuations.append(record)
                    else:
                        events.append(record)
                    continue
                exercise = EXERCISE_TITLE_RE.match(line)
                if exercise and "解析" not in line[: exercise.end() + 3]:
                    events.append(
                        {
                            "kind": "exercise",
                            "number": exercise.group("number"),
                            "page": page_number,
                            "line": line_number,
                            "text": line,
                        }
                    )
    return events, heading_pages, continuations


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--expected-count", type=int, default=553)
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    rows, expected = load_rows()
    events, heading_pages, continuations = pdf_events(pdf_path)
    exercise_events = [event for event in events if event["kind"] == "exercise"]
    solution_events = [event for event in events if event["kind"] == "solution"]
    exercise_counts = Counter(str(event["number"]) for event in exercise_events)
    solution_counts = Counter(str(event["number"]) for event in solution_events)
    event_pairs = list(zip(events[0::2], events[1::2], strict=False))
    adjacency_errors = [
        {"first": first, "second": second}
        for first, second in event_pairs
        if first["kind"] != "exercise"
        or second["kind"] != "solution"
        or first["number"] != second["number"]
    ]
    odd_event = events[-1] if len(events) % 2 else None
    visible_numbers = [str(event["number"]) for event in exercise_events]
    missing_exercises = sorted(set(expected) - set(exercise_counts))
    missing_solutions = sorted(set(expected) - set(solution_counts))
    unexpected_exercises = sorted(set(exercise_counts) - set(expected))
    unexpected_solutions = sorted(set(solution_counts) - set(expected))
    duplicate_exercises = sorted(number for number, count in exercise_counts.items() if count != 1)
    duplicate_solutions = sorted(number for number, count in solution_counts.items() if count != 1)

    by_exercise = {str(event["number"]): event for event in exercise_events}
    by_solution = {str(event["number"]): event for event in solution_events}
    row_by_number = {row["PDF显示编号"]: row for row in rows}
    pair_records: list[dict[str, object]] = []
    for number in expected:
        exercise = by_exercise.get(number)
        solution = by_solution.get(number)
        source_row = row_by_number[number]
        if exercise and solution:
            cross_page = int(exercise["page"]) != int(solution["page"])
            source_row["是否跨页"] = (
                f"是（题干p.{exercise['page']}；解析p.{solution['page']}）"
                if cross_page
                else f"否（p.{exercise['page']}）"
            )
            source_row["处理状态"] = "已完成（PDF已复核）"
            source_row["备注"] = (
                source_row["备注"].split(";PDF题干p.", 1)[0]
                + f";PDF题干p.{exercise['page']};PDF解析p.{solution['page']}"
            )
        pair_records.append(
            {
                "pair_id": source_row["练习编号"],
                "display_number": number,
                "exercise_page": exercise["page"] if exercise else None,
                "solution_page": solution["page"] if solution else None,
                "cross_page": (
                    int(exercise["page"]) != int(solution["page"])
                    if exercise and solution
                    else None
                ),
            }
        )

    chapter_ranges: list[dict[str, object]] = []
    exercise_section_pages: set[int] = set()
    for chapter in range(1, 38):
        chapter_pairs = [
            item for item in pair_records if str(item["display_number"]).startswith(f"{chapter}.")
        ]
        chapter_continuations = [
            item for item in continuations if str(item["number"]).startswith(f"{chapter}.")
        ]
        visible_pages = [
            int(page)
            for item in chapter_pairs
            for page in (item["exercise_page"], item["solution_page"])
            if page is not None
        ] + [int(item["page"]) for item in chapter_continuations]
        start_page = heading_pages[chapter - 1] if len(heading_pages) >= chapter else None
        end_page = max(visible_pages) if visible_pages else None
        if start_page is not None and end_page is not None:
            exercise_section_pages.update(range(start_page, end_page + 1))
        chapter_ranges.append(
            {
                "chapter": chapter,
                "start_page": start_page,
                "end_page": end_page,
                "page_count": end_page - start_page + 1 if start_page and end_page else None,
                "pair_count": len(chapter_pairs),
            }
        )

    result_ok = (
        len(rows) == args.expected_count
        and len(expected) == args.expected_count
        and len(exercise_events) == args.expected_count
        and len(solution_events) == args.expected_count
        and len(heading_pages) == 37
        and not adjacency_errors
        and odd_event is None
        and visible_numbers == expected
        and not missing_exercises
        and not missing_solutions
        and not unexpected_exercises
        and not unexpected_solutions
        and not duplicate_exercises
        and not duplicate_solutions
    )

    if result_ok:
        fieldnames = list(rows[0].keys())
        with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    payload = {
        "schema_version": 1,
        "pdf": str(pdf_path),
        "expected_count": args.expected_count,
        "chapter_heading_count": len(heading_pages),
        "chapter_heading_pages": heading_pages,
        "exercise_title_count": len(exercise_events),
        "solution_title_count": len(solution_events),
        "continuation_title_count": len(continuations),
        "continuation_pages": sorted({int(item["page"]) for item in continuations}),
        "source_expected_order_matches_pdf": visible_numbers == expected,
        "adjacent_pair_count": len(event_pairs) - len(adjacency_errors),
        "adjacency_errors": adjacency_errors,
        "odd_event": odd_event,
        "missing_exercises": missing_exercises,
        "missing_solutions": missing_solutions,
        "unexpected_exercises": unexpected_exercises,
        "unexpected_solutions": unexpected_solutions,
        "duplicate_exercises": duplicate_exercises,
        "duplicate_solutions": duplicate_solutions,
        "cross_page_pair_count": sum(bool(item["cross_page"]) for item in pair_records),
        "chapter_ranges": chapter_ranges,
        "exercise_section_page_count": len(exercise_section_pages),
        "exercise_section_pages": sorted(exercise_section_pages),
        "pairs": pair_records,
        "result": "PASS" if result_ok else "FAIL",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    console_summary = {
        "result": payload["result"],
        "chapter_heading_count": payload["chapter_heading_count"],
        "exercise_title_count": payload["exercise_title_count"],
        "solution_title_count": payload["solution_title_count"],
        "continuation_title_count": payload["continuation_title_count"],
        "source_expected_order_matches_pdf": payload["source_expected_order_matches_pdf"],
        "adjacent_pair_count": payload["adjacent_pair_count"],
        "adjacency_error_count": len(adjacency_errors),
        "cross_page_pair_count": payload["cross_page_pair_count"],
        "missing_exercise_count": len(missing_exercises),
        "missing_solution_count": len(missing_solutions),
        "unexpected_exercise_count": len(unexpected_exercises),
        "unexpected_solution_count": len(unexpected_solutions),
    }
    print(json.dumps(console_summary, ensure_ascii=False, indent=2))
    return 0 if result_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

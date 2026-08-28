#!/usr/bin/env python3
r"""Mechanically normalize worked examples into adjacent solution blocks.

This script only edits the 37 chapter files.  It preserves every existing
example label and answer body, moves grouped answers next to their matching
problem, and wraps plain answer bodies in the existing ``solution``
environment.  Two examples without a solution heading are intentionally left
for explicit editorial repair.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src" / "讲义源码"

EXAMPLE_BEGIN = re.compile(r"\\begin\{example\}(?:\[[^\]]*\])?")
EXAMPLE_END = re.compile(r"\\end\{example\}")
EXAMPLE_LABEL = re.compile(r"\\label\{(exm:[^{}]+)\}")
HEADING = re.compile(r"\\SLExampleSolutionHeading\{(exm:[^{}]+)\}")
BOUNDARY = re.compile(
    r"(?m)^[ \t]*(?="
    r"\\SL(?:Teach|Direct|Review|Advanced|Practice|Application|Closing)Section\b"
    r"|\\begin\{chapterexercisebox\}"
    r"|\\phantomsection\\label\{struct:"
    r"|\\chapter\b|\\section\b|\\subsection\b"
    r")"
)
PAIRING_TOKEN = re.compile(
    r"(?:\s+|\\phantomsection\b|\\label\{[^{}]+\}|"
    r"\\Needspace\*?\{[^{}]+\}|\\par\b|\\smallskip\b|\\medskip\b)"
)
TRAILING_SPACING = re.compile(
    r"(?:\s|\\Needspace\*?\{[^{}]+\}|\\smallskip\b|\\medskip\b|\\nopagebreak(?:\[[^\]]+\])?)*\Z"
)


@dataclass
class Example:
    start: int
    end: int
    label: str | None
    heading_start: int | None
    heading_end: int | None


def chapter_files() -> list[Path]:
    return sorted(SOURCE_ROOT.glob("第*册_*/chapters/V*-C*.tex"))


def consume_pairing(text: str, position: int) -> int:
    while True:
        match = PAIRING_TOKEN.match(text, position)
        if not match:
            return position
        position = match.end()


def parse(text: str) -> list[Example]:
    headings: dict[str, list[re.Match[str]]] = {}
    for match in HEADING.finditer(text):
        headings.setdefault(match.group(1), []).append(match)
    examples: list[Example] = []
    cursor = 0
    while True:
        begin = EXAMPLE_BEGIN.search(text, cursor)
        if not begin:
            break
        end = EXAMPLE_END.search(text, begin.end())
        if not end:
            raise RuntimeError("unclosed example environment")
        block = text[begin.start():end.end()]
        labels = EXAMPLE_LABEL.findall(block)
        label = labels[0] if len(labels) == 1 else None
        matches = headings.get(label, []) if label else []
        heading = matches[0] if len(matches) == 1 else None
        examples.append(Example(
            start=begin.start(),
            end=end.end(),
            label=label,
            heading_start=heading.start() if heading else None,
            heading_end=heading.end() if heading else None,
        ))
        cursor = end.end()
    return examples


def apply_edits(text: str, edits: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in sorted(edits, key=lambda item: (item[0], item[1]), reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def split_inside_examples(text: str) -> tuple[str, int]:
    edits: list[tuple[int, int, str]] = []
    count = 0
    for example in parse(text):
        if example.heading_start is None or example.heading_end is None:
            continue
        if not (example.start < example.heading_start < example.end):
            continue
        old_end = EXAMPLE_END.search(text, example.heading_end, example.end)
        if old_end is None:
            raise RuntimeError(f"missing end for {example.label}")
        question = text[example.start:example.heading_start].rstrip()
        heading = text[example.heading_start:example.heading_end]
        answer = text[example.heading_end:old_end.start()].strip()
        replacement = (
            question + "\n\\end{example}\n"
            + heading + "\n\\begin{solution}\n"
            + answer + "\n\\end{solution}"
        )
        edits.append((example.start, old_end.end(), replacement))
        count += 1
    return apply_edits(text, edits), count


def solution_end(text: str, heading_start: int, heading_end: int, all_headings: list[re.Match[str]]) -> int:
    candidates = [
        match.start() for match in all_headings if match.start() > heading_start
    ]
    boundary = BOUNDARY.search(text, heading_end)
    if boundary:
        candidates.append(boundary.start())
    if not candidates:
        raise RuntimeError(f"cannot locate answer boundary after offset {heading_start}")
    return min(candidates)


def wrap_and_move_after_examples(text: str) -> tuple[str, int, int]:
    examples = parse(text)
    all_headings = list(HEADING.finditer(text))
    edits: list[tuple[int, int, str]] = []
    insertions: list[tuple[int, int, str]] = []
    wrapped = 0
    moved = 0
    for index, example in enumerate(examples):
        if example.heading_start is None or example.heading_end is None:
            continue
        if example.heading_start < example.end:
            raise RuntimeError(f"inside-example heading survived for {example.label}")
        after_heading = consume_pairing(text, example.heading_end)
        if text.startswith(r"\begin{solution}", after_heading):
            continue
        end = solution_end(text, example.heading_start, example.heading_end, all_headings)
        raw_answer = text[example.heading_end:end]
        trailing = TRAILING_SPACING.search(raw_answer)
        answer_end = example.heading_end + (trailing.start() if trailing else len(raw_answer))
        answer = text[example.heading_end:answer_end].strip()
        heading = text[example.heading_start:example.heading_end]
        solution = heading + "\n\\begin{solution}\n" + answer + "\n\\end{solution}\n"

        expected = consume_pairing(text, example.end)
        adjacent = example.heading_start == expected
        if adjacent:
            edits.append((example.heading_start, answer_end, solution.rstrip()))
            wrapped += 1
        else:
            edits.append((example.heading_start, end, ""))
            insertions.append((example.end, example.end, "\n" + solution.rstrip()))
            wrapped += 1
            moved += 1

    return apply_edits(text, edits + insertions), wrapped, moved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    totals = {"files": 0, "split_inside": 0, "wrapped": 0, "moved": 0}
    outputs: list[tuple[Path, str]] = []
    for path in chapter_files():
        original = path.read_text(encoding="utf-8")
        text, inside = split_inside_examples(original)
        text, wrapped, moved = wrap_and_move_after_examples(text)
        if text != original:
            outputs.append((path, text))
            totals["files"] += 1
        totals["split_inside"] += inside
        totals["wrapped"] += wrapped
        totals["moved"] += moved
    print(totals)
    if not args.apply:
        print("dry-run only; pass --apply to write the mechanical rewrite")
        return 0
    for path, text in outputs:
        path.write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

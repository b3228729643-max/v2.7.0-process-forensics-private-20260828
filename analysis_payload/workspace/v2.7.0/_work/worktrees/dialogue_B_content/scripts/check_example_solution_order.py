#!/usr/bin/env python3
r"""Check one-to-one, adjacent worked-example/solution structure.

Chapter-end exercises intentionally use a separate exercise/answer structure
and are outside this check.  The checker only scans chapter ``example``
environments and the existing ``\SLExampleSolutionHeading`` interface.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src" / "讲义源码"
REPORT = ROOT / "work_state" / "reports" / "example_solution_order.json"

EXAMPLE_BEGIN = re.compile(r"\\begin\{example\}(?:\[[^\]]*\])?")
EXAMPLE_END = re.compile(r"\\end\{example\}")
EXAMPLE_LABEL = re.compile(r"\\label\{(exm:[^{}]+)\}")
HEADING = re.compile(r"\\SLExampleSolutionHeading\{(exm:[^{}]+)\}")


def without_comments(text: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


def consume_pairing_tokens(text: str, position: int) -> int:
    """Consume only whitespace and explicitly allowed pairing tokens."""
    patterns = [
        re.compile(r"\s+"),
        re.compile(r"\\phantomsection\b"),
        re.compile(r"\\label\{[^{}]+\}"),
        re.compile(r"\\Needspace\*?\{[^{}]+\}"),
        re.compile(r"\\par\b"),
        re.compile(r"\\smallskip\b|\\medskip\b"),
    ]
    while position < len(text):
        for pattern in patterns:
            match = pattern.match(text, position)
            if match:
                position = match.end()
                break
        else:
            break
    return position


def line_at(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def chapter_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_ROOT.glob("第*册_*/chapters/V*-C*.tex")
        if path.is_file()
    )


def inspect_file(path: Path) -> tuple[list[dict], list[dict]]:
    original = path.read_text(encoding="utf-8")
    text = without_comments(original)
    headings: dict[str, list[re.Match[str]]] = {}
    for match in HEADING.finditer(text):
        headings.setdefault(match.group(1), []).append(match)

    examples: list[dict] = []
    used_headings: set[int] = set()
    for begin in EXAMPLE_BEGIN.finditer(text):
        end = EXAMPLE_END.search(text, begin.end())
        if not end:
            examples.append({
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "line": line_at(text, begin.start()),
                "label": None,
                "status": "unclosed_example",
            })
            continue
        block = text[begin.start():end.end()]
        labels = EXAMPLE_LABEL.findall(block)
        label = labels[0] if labels else None
        issues: list[str] = []
        if len(labels) != 1:
            issues.append("missing_or_multiple_example_labels")
        matches = headings.get(label, []) if label else []
        if len(matches) != 1:
            issues.append("missing_or_duplicate_solution_heading")

        expected = consume_pairing_tokens(text, end.end())
        adjacent = False
        solution_environment = False
        heading_line = None
        if len(matches) == 1:
            heading = matches[0]
            used_headings.add(heading.start())
            heading_line = line_at(text, heading.start())
            adjacent = heading.start() == expected
            if not adjacent:
                issues.append("order_error")
            after_heading = consume_pairing_tokens(text, heading.end())
            solution_environment = text.startswith(r"\begin{solution}", after_heading)
            if not solution_environment:
                issues.append("missing_solution_environment")

        relation = None
        if len(matches) == 1:
            relation = "inside_example" if matches[0].start() < end.start() else "after_example"
        examples.append({
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "line": line_at(text, begin.start()),
            "heading_line": heading_line,
            "example_end_line": line_at(text, end.end()),
            "heading_relation": relation,
            "label": label,
            "adjacent": adjacent,
            "solution_environment": solution_environment,
            "issues": issues,
            "status": "PASS" if not issues else "FAIL",
        })

    orphan_headings = [
        {
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "line": line_at(text, match.start()),
            "label": match.group(1),
        }
        for match in HEADING.finditer(text)
        if match.start() not in used_headings
    ]
    return examples, orphan_headings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print full JSON report")
    args = parser.parse_args()

    all_examples: list[dict] = []
    all_orphans: list[dict] = []
    for path in chapter_files():
        examples, orphans = inspect_file(path)
        all_examples.extend(examples)
        all_orphans.extend(orphans)

    labels = [entry["label"] for entry in all_examples if entry.get("label")]
    duplicate_labels = sorted({label for label in labels if labels.count(label) > 1})
    failing = [entry for entry in all_examples if entry.get("status") != "PASS"]
    report = {
        "schema_version": 1,
        "scope": "body teaching examples in 37 chapter files; chapter-end exercises excluded",
        "example_count": len(all_examples),
        "paired_adjacent_count": sum(entry.get("status") == "PASS" for entry in all_examples),
        "orphan_examples": sum("missing_or_duplicate_solution_heading" in entry.get("issues", []) for entry in all_examples),
        "orphan_solutions": len(all_orphans),
        "duplicate_pairs": len(duplicate_labels),
        "order_errors": sum("order_error" in entry.get("issues", []) for entry in all_examples),
        "missing_solution_environments": sum("missing_solution_environment" in entry.get("issues", []) for entry in all_examples),
        "duplicate_labels": duplicate_labels,
        "failures": failing,
        "orphan_solution_headings": all_orphans,
        "result": "PASS" if not failing and not all_orphans and not duplicate_labels else "FAIL",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report if args.json else {key: value for key, value in report.items() if key not in {"failures", "orphan_solution_headings"}}, ensure_ascii=False, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Map legacy reason-like algorithm statuses to the central status set."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


MAPPINGS = {
    r"\mathtt{numerical\_stop}": r"\mathtt{numerical\_failure}",
    r"\mathtt{stagnated}": r"\mathtt{budget\_stop}",
    r"\mathtt{no\_weak\_edge}": r"\mathtt{converged}",
    r"\mathtt{no\_feasible\_path}": r"\mathtt{completed}",
}
STATUS_LINE_RE = re.compile(
    r"(?m)^(?P<prefix>[ \t]*status=\{)(?P<body>[^\r\n]*)(?P<suffix>\},[ \t]*)$"
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
    temp = path.with_name(path.name + ".m07status.tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def dedupe_status_line(match: re.Match[str]) -> str:
    items = match.group("body").split("、")
    unique: list[str] = []
    for item in items:
        if item not in unique:
            unique.append(item)
    return match.group("prefix") + "、".join(unique) + match.group("suffix")


def main() -> int:
    options = parse_args()
    root = options.chapters_root.resolve()
    if options.mode == "apply" and options.report is None:
        raise SystemExit("--report is required in apply mode")

    counts: Counter[str] = Counter()
    by_file: dict[str, dict[str, int]] = defaultdict(dict)
    changed: list[tuple[Path, str, bool]] = []
    status_lines_deduplicated = 0

    for path in sorted(root.rglob("*.tex")):
        text, bom = read(path)
        transformed = text
        relative = str(path.relative_to(root)).replace("\\", "/")
        for old, new in MAPPINGS.items():
            count = transformed.count(old)
            if count:
                counts[old] += count
                by_file[relative][old] = count
                transformed = transformed.replace(old, new)
        before_lines = STATUS_LINE_RE.findall(transformed)
        deduped = STATUS_LINE_RE.sub(dedupe_status_line, transformed)
        after_lines = STATUS_LINE_RE.findall(deduped)
        status_lines_deduplicated += sum(
            1 for before, after in zip(before_lines, after_lines) if before[1] != after[1]
        )
        transformed = deduped
        if transformed != text:
            changed.append((path, transformed, bom))

    summary = {
        "mode": options.mode,
        "changed_files": len(changed),
        "literal_replacements": dict(sorted(counts.items())),
        "total_literal_replacements": sum(counts.values()),
        "status_lines_deduplicated": status_lines_deduplicated,
    }
    if not counts:
        raise SystemExit("no legacy status literals found")
    if options.mode == "check":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    for path, transformed, bom in changed:
        write_atomic(path, transformed, bom)
    report_path = options.report.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {**summary, "result": "APPLIED", "files": by_file}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**summary, "result": "APPLIED", "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

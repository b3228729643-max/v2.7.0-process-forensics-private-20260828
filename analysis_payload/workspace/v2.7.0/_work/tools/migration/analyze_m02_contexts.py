#!/usr/bin/env python3
"""Read-only context extractor for the M02 935 self-check migration."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SELF_CHECK_RE = re.compile(
    r"^\\paragraph\{读前自检：(?P<title>.*)。\}(?P<question>.*)\\par\s*$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--r02", required=True, type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=935)
    parser.add_argument("--after-lines", type=int, default=18)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    r02 = json.loads(args.r02.read_text(encoding="utf-8"))
    expected = r02["mapping"]
    actual: list[dict[str, object]] = []
    for path in sorted(source_root.glob("第*册_*/chapters/V*-C*.tex")):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for index, line in enumerate(lines):
            match = SELF_CHECK_RE.match(line)
            if not match:
                continue
            actual.append(
                {
                    "source_file": "src/讲义源码/" + path.relative_to(source_root).as_posix(),
                    "current_line": index + 1,
                    "title": match.group("title"),
                    "question": match.group("question"),
                    "after": [
                        {"line": j + 1, "text": lines[j]}
                        for j in range(index + 1, min(len(lines), index + 1 + args.after_lines))
                    ],
                }
            )
    if len(actual) != len(expected):
        raise SystemExit(f"mapping size mismatch: actual={len(actual)} expected={len(expected)}")
    for ordinal, (old, current) in enumerate(zip(expected, actual), start=1):
        if int(old["csv_ordinal"]) != ordinal:
            raise SystemExit(f"non-contiguous R02 ordinal at {ordinal}")
        if old["source_file"].replace("\\", "/") != current["source_file"]:
            raise SystemExit(f"source mismatch at {ordinal}")
        if old["title"] != current["title"]:
            raise SystemExit(f"title mismatch at {ordinal}: {old['title']!r} != {current['title']!r}")
        if args.start <= ordinal <= args.end:
            print(
                json.dumps(
                    {
                        "csv_ordinal": ordinal,
                        "source_file": current["source_file"],
                        "original_line": old["original_line"],
                        **{key: value for key, value in current.items() if key != "source_file"},
                    },
                    ensure_ascii=False,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

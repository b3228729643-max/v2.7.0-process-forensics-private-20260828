from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path

import pdfplumber


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def page_chars(path: Path, page_number: int) -> list[dict]:
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[page_number - 1]
        return [
            {
                "text": str(char.get("text", "")),
                "x0": float(char["x0"]),
                "top": float(char["top"]),
                "x1": float(char["x1"]),
                "bottom": float(char["bottom"]),
            }
            for char in page.chars
        ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    before = page_chars(args.before, args.page)
    after = page_chars(args.after, args.page)
    before_text = [char["text"] for char in before]
    after_text = [char["text"] for char in after]
    matcher = difflib.SequenceMatcher(a=before_text, b=after_text, autojunk=False)

    matched: list[tuple[dict, dict]] = []
    for block in matcher.get_matching_blocks():
        for offset in range(block.size):
            matched.append((before[block.a + offset], after[block.b + offset]))

    # The target figure and caption occupy the upper part of the page.  The
    # body gate deliberately starts below 285 pt so it tests downstream page
    # integration without treating the authorized figure geometry as drift.
    downstream = [
        (left, right)
        for left, right in matched
        if left["top"] >= 285.0 and right["top"] >= 285.0
    ]
    deltas = [
        {
            "dx0": right["x0"] - left["x0"],
            "dtop": right["top"] - left["top"],
            "dx1": right["x1"] - left["x1"],
            "dbottom": right["bottom"] - left["bottom"],
        }
        for left, right in downstream
    ]

    maxima = {
        key: max((abs(item[key]) for item in deltas), default=0.0)
        for key in ("dx0", "dtop", "dx1", "dbottom")
    }
    vertical_delta_counts = Counter(round(item["dtop"], 6) for item in deltas)
    horizontal_exact = maxima["dx0"] <= 1e-6 and maxima["dx1"] <= 1e-6
    bounded_vertical = maxima["dtop"] <= 0.6 + 1e-6 and maxima["dbottom"] <= 0.6 + 1e-6
    report = {
        "schema_version": 1,
        "page_physical": args.page,
        "before_path": str(args.before.resolve()),
        "before_sha256": sha256(args.before),
        "after_path": str(args.after.resolve()),
        "after_sha256": sha256(args.after),
        "before_char_count": len(before),
        "after_char_count": len(after),
        "matched_char_count": len(matched),
        "downstream_matched_char_count": len(downstream),
        "downstream_gate_top_pt": 285.0,
        "downstream_max_abs_coordinate_delta_pt": maxima,
        "downstream_dtop_delta_counts_pt": {
            str(key): value for key, value in sorted(vertical_delta_counts.items())
        },
        "downstream_exact_coordinate_match": all(value <= 1e-6 for value in maxima.values()),
        "downstream_horizontal_exact": horizontal_exact,
        "downstream_vertical_shift_bounded_0_6pt": bounded_vertical,
        "result": "PASS_PAGE_INTEGRATION"
        if horizontal_exact and bounded_vertical
        else "REVIEW",
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

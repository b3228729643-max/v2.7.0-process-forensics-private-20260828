#!/usr/bin/env python3
"""Freeze the 92 M02 route records against the current retained boxes."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path


BOX_RE = re.compile(r"^\\begin\{keypointbox\}\[title=\{(?P<title>.*)\}\]$")
EXPECTED_STEPS = ("输入", "初始化", "核心更新", "数学停止", "输出")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--r02-routes", required=True, type=Path)
    parser.add_argument("--m07", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--print-records", action="store_true")
    parser.add_argument(
        "--print-range-json", nargs=2, type=int, metavar=("START", "END")
    )
    return parser.parse_args()


def normalize_title(value: str) -> str:
    value = value.removesuffix("：执行契约")
    value = value.replace(r"\kNN{}", "").replace("C4.5", "C4 5")
    value = re.sub(r"\\[A-Za-z]+(?:\{\})?", "", value)
    value = re.sub(r"[\s.：:，，（）()\-]", "", value)
    return value


def scan_boxes(source_root: Path) -> list[dict[str, object]]:
    boxes: list[dict[str, object]] = []
    for path in sorted(source_root.glob("第*册_*/chapters/V*-C*.tex")):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        relative = path.relative_to(source_root).as_posix()
        for index, line in enumerate(lines):
            match = BOX_RE.fullmatch(line)
            if not match:
                continue
            title = match.group("title")
            if not (
                title.endswith("：五步阅读")
                or title.endswith("：证明阅读检查")
            ):
                continue
            end = index + 1
            while end < len(lines) and lines[end] != r"\end{keypointbox}":
                end += 1
            if end >= len(lines):
                raise SystemExit(f"unterminated keypointbox: {relative}:{index + 1}")
            body = lines[index + 1 : end]
            excerpt = " ".join(item.strip() for item in body if item.strip())
            if len(excerpt) > 420:
                excerpt = excerpt[:420].rstrip() + "…"
            boxes.append(
                {
                    "source_file": relative,
                    "line": index + 1,
                    "end_line": end + 1,
                    "title": title,
                    "body": body,
                    "excerpt": excerpt,
                }
            )
    return boxes


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    routes = json.loads(args.r02_routes.read_text(encoding="utf-8"))["mapping"]
    m07 = json.loads(args.m07.read_text(encoding="utf-8"))["mapping"]
    boxes = scan_boxes(source_root)
    if len(routes) != 92 or len(m07) != 88:
        raise SystemExit("unexpected R02/M07 counts")
    algorithm_routes = [row for row in routes if row["category"] == "algorithm"]
    proof_routes = [row for row in routes if row["category"] == "proof"]
    if len(algorithm_routes) != 88 or len(proof_routes) != 4:
        raise SystemExit("route categories are not 88 algorithm + 4 proof")

    for position, (route, action) in enumerate(zip(algorithm_routes, m07), start=1):
        if route["source_file"] != action["source_file"]:
            raise SystemExit(f"algorithm route/M07 path mismatch at {position}")
        if normalize_title(str(route["title"])) != normalize_title(str(action["title"])):
            raise SystemExit(f"algorithm route/M07 title mismatch at {position}")

    five_boxes = [
        box for box in boxes if str(box["title"]).endswith("：五步阅读")
    ]
    proof_boxes = [
        box for box in boxes if str(box["title"]).endswith("：证明阅读检查")
    ]
    retained_rows = [
        (index, row)
        for index, row in enumerate(m07, start=1)
        if row["action"] == "COMPACT_TO_FIVE_STEPS"
    ]
    if len(retained_rows) != 59 or len(proof_boxes) != 4:
        raise SystemExit(
            "route inputs do not contain 59 retained algorithm rows + 4 proof boxes"
        )

    used: set[int] = set()
    retained_target: dict[int, dict[str, object]] = {}
    retained_match_ratio: dict[int, float] = {}
    for m07_ordinal, row in retained_rows:
        candidates = [
            (index, box)
            for index, box in enumerate(five_boxes)
            if index not in used and box["source_file"] == row["source_file"]
        ]
        if not candidates:
            raise SystemExit(f"no five-step candidate for M07 {m07_ordinal}")
        target_norm = normalize_title(str(row["title"]))
        ranked = sorted(
            candidates,
            key=lambda item: (
                -difflib.SequenceMatcher(
                    None,
                    target_norm,
                    normalize_title(
                        str(item[1]["title"]).removesuffix("：五步阅读")
                    ),
                ).ratio(),
                abs(int(item[1]["line"]) - int(row["original_line"])),
            ),
        )
        chosen_index, chosen = ranked[0]
        ratio = difflib.SequenceMatcher(
            None,
            target_norm,
            normalize_title(str(chosen["title"]).removesuffix("：五步阅读")),
        ).ratio()
        if ratio < 0.60:
            raise SystemExit(
                f"weak five-step match for M07 {m07_ordinal}: {ratio:.3f}"
            )
        used.add(chosen_index)
        retained_target[m07_ordinal] = chosen
        retained_match_ratio[m07_ordinal] = ratio
    if len(used) != 59:
        raise SystemExit("did not uniquely match all 59 retained five-step boxes")

    merge_target: dict[int, int] = {}
    for m07_ordinal, row in enumerate(m07, start=1):
        if row["action"] != "REMOVE_DUPLICATE":
            continue
        candidates = [
            index
            for index, other in retained_rows
            if other["source_file"] == row["source_file"]
            and normalize_title(str(other["title"]))
            == normalize_title(str(row["title"]))
        ]
        if len(candidates) != 1:
            raise SystemExit(
                f"REMOVE_DUPLICATE M07 {m07_ordinal} has {len(candidates)} merge targets"
            )
        merge_target[m07_ordinal] = candidates[0]
    if len(merge_target) != 29:
        raise SystemExit("did not resolve 29 duplicate merge targets")

    proof_target: dict[tuple[str, str], dict[str, object]] = {}
    for box in proof_boxes:
        base = str(box["title"]).removesuffix("：证明阅读检查")
        proof_target[(str(box["source_file"]), normalize_title(base))] = box

    records: list[dict[str, object]] = []
    algorithm_position = 0
    for route_ordinal, route in enumerate(routes, start=1):
        if route["category"] == "proof":
            key = (str(route["source_file"]), normalize_title(str(route["title"])))
            target = proof_target.get(key)
            if target is None:
                raise SystemExit(
                    f"proof route {route_ordinal} has no current proof-check box"
                )
            labels = [
                str(number)
                for number in range(1, 6)
                if any(
                    f"\\textbf{{{number}.}}" in line for line in target["body"]
                )
            ]
            record = {
                "route_ordinal": route_ordinal,
                "original_source_file": route["source_file"],
                "original_line": route["original_line"],
                "original_title": route["title"],
                "category": "proof",
                "original_reader_question": route["reader_question"],
                "current_action": "RETAIN_PROOF_CHECK_BOX",
                "current_source_file": "src/讲义源码/" + str(target["source_file"]),
                "current_box_title": target["title"],
                "current_line": target["line"],
                "current_box_end_line": target["end_line"],
                "merged_into": None,
                "m07_ordinal": None,
                "m07_action": None,
                "proof_steps_present": labels,
                "answer_anchor_excerpt": target["excerpt"],
            }
        else:
            algorithm_position += 1
            m07_ordinal = algorithm_position
            action = m07[m07_ordinal - 1]
            if action["action"] == "COMPACT_TO_FIVE_STEPS":
                target_ordinal = m07_ordinal
                current_action = "RETAIN_FIVE_STEP_BOX"
                merged = None
            else:
                target_ordinal = merge_target[m07_ordinal]
                current_action = "REMOVE_DUPLICATE"
                merge_box = retained_target[target_ordinal]
                merged = {
                    "m07_ordinal": target_ordinal,
                    "source_file": "src/讲义源码/"
                    + str(merge_box["source_file"]),
                    "current_box_title": merge_box["title"],
                    "current_line": merge_box["line"],
                }
            target = retained_target[target_ordinal]
            labels = [
                label
                for label in EXPECTED_STEPS
                if any(f"\\textbf{{{label}。}}" in line for line in target["body"])
            ]
            record = {
                "route_ordinal": route_ordinal,
                "original_source_file": route["source_file"],
                "original_line": route["original_line"],
                "original_title": route["title"],
                "category": "algorithm",
                "original_reader_question": route["reader_question"],
                "current_action": current_action,
                "current_source_file": "src/讲义源码/" + str(target["source_file"]),
                "current_box_title": target["title"],
                "current_line": target["line"],
                "current_box_end_line": target["end_line"],
                "merged_into": merged,
                "m07_ordinal": m07_ordinal,
                "m07_action": action["action"],
                "five_step_labels_present": labels,
                "retained_match_ratio": retained_match_ratio[target_ordinal],
                "answer_anchor_excerpt": target["excerpt"],
            }
        records.append(record)

    counts = Counter(str(record["current_action"]) for record in records)
    audit = {
        "records": len(records),
        "algorithm_routes": sum(
            record["category"] == "algorithm" for record in records
        ),
        "proof_routes": sum(record["category"] == "proof" for record in records),
        "current_action_counts": dict(counts),
        "remove_duplicate_merged": sum(
            record["merged_into"] is not None for record in records
        ),
        "retained_five_step_boxes_with_all_labels": sum(
            record["current_action"] == "RETAIN_FIVE_STEP_BOX"
            and record.get("five_step_labels_present") == list(EXPECTED_STEPS)
            for record in records
        ),
        "retained_proof_boxes_with_five_steps": sum(
            record.get("proof_steps_present") == ["1", "2", "3", "4", "5"]
            for record in records
        ),
        "current_five_step_boxes_scanned": len(five_boxes),
        "current_five_step_boxes_not_in_r02_routes": len(five_boxes) - len(used),
        "unmapped_current_five_step_titles": [
            box["title"]
            for index, box in enumerate(five_boxes)
            if index not in used
        ],
        "minimum_retained_match_ratio": min(retained_match_ratio.values()),
        "mapping_fields_nonempty": all(
            record["original_source_file"]
            and record["original_line"]
            and record["original_title"]
            and record["current_action"]
            and record["current_box_title"]
            and record["current_line"]
            for record in records
        ),
    }
    if (
        audit["records"] != 92
        or audit["algorithm_routes"] != 88
        or audit["proof_routes"] != 4
    ):
        raise SystemExit("route audit cardinalities changed unexpectedly")
    if (
        counts != Counter(
            {
                "RETAIN_FIVE_STEP_BOX": 59,
                "REMOVE_DUPLICATE": 29,
                "RETAIN_PROOF_CHECK_BOX": 4,
            }
        )
        or audit["remove_duplicate_merged"] != 29
        or audit["retained_five_step_boxes_with_all_labels"] != 59
        or audit["retained_proof_boxes_with_five_steps"] != 4
        or not audit["mapping_fields_nonempty"]
    ):
        raise SystemExit(
            "route evidence did not satisfy 59 + 29 + 4 acceptance: "
            + json.dumps(audit, ensure_ascii=False, sort_keys=True)
        )

    result = {
        "task_id": "M02-SA2-R2",
        "mode": "R02_92_to_current_boxes",
        "audit": audit,
        "mapping": records,
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    if args.print_range_json:
        start, end = args.print_range_json
        print(
            json.dumps(
                [
                    row
                    for row in records
                    if start <= int(row["route_ordinal"]) <= end
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.print_records:
        print(payload, end="")
    else:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

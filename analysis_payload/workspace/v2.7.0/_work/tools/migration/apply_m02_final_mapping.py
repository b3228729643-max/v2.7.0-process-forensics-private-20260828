#!/usr/bin/env python3
"""Apply the frozen M02 ordinal mapping with exact line-boundary checks."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


SELF_CHECK_RE = re.compile(
    r"^\\paragraph\{读前自检：(?P<title>.*)。\}(?P<question>.*)\\par\s*$"
)
EXPECTED_RECORDS = 935
EXPECTED_FILES = 37


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--mapping", required=True, type=Path)
    parser.add_argument("--r02", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def decode_source(raw: bytes) -> tuple[str, bool]:
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    return raw.decode("utf-8-sig"), has_bom


def encode_source(text: str, has_bom: bool) -> bytes:
    payload = text.encode("utf-8")
    return (b"\xef\xbb\xbf" + payload) if has_bom else payload


def split_line(line: str) -> tuple[str, str]:
    body = line.rstrip("\r\n")
    return body, line[len(body) :]


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    frozen = json.loads(args.mapping.read_text(encoding="utf-8"))
    r02 = json.loads(args.r02.read_text(encoding="utf-8"))
    mapping = frozen["mapping"]
    original = r02["mapping"]
    if len(mapping) != EXPECTED_RECORDS or len(original) != EXPECTED_RECORDS:
        raise SystemExit("mapping count is not 935")
    if [int(row["csv_ordinal"]) for row in mapping] != list(range(1, EXPECTED_RECORDS + 1)):
        raise SystemExit("frozen ordinals are not contiguous")

    by_file: dict[str, list[tuple[dict[str, object], dict[str, object]]]] = defaultdict(list)
    for new, old in zip(mapping, original):
        if int(new["csv_ordinal"]) != int(old["csv_ordinal"]):
            raise SystemExit(f"R02 ordinal mismatch at {new['csv_ordinal']}")
        if str(new["source_file"]).replace("\\", "/") != str(old["source_file"]).replace("\\", "/"):
            raise SystemExit(f"R02 path mismatch at {new['csv_ordinal']}")
        if new["title"] != old["title"]:
            raise SystemExit(f"R02 title mismatch at {new['csv_ordinal']}")
        by_file[str(new["source_file"]).replace("\\", "/")].append((new, old))
    if len(by_file) != EXPECTED_FILES:
        raise SystemExit(f"mapping spans {len(by_file)} files, expected 37")

    prepared: dict[Path, bytes] = {}
    per_file: list[dict[str, object]] = []
    total_replacements = 0
    for relative, pairs in sorted(by_file.items()):
        path = source_root / Path(relative)
        raw = path.read_bytes()
        text, has_bom = decode_source(raw)
        lines = text.splitlines(keepends=True)
        source_hits = []
        for index, line in enumerate(lines):
            body, _ = split_line(line)
            match = SELF_CHECK_RE.fullmatch(body)
            if match:
                source_hits.append((index, match))
        if len(source_hits) != len(pairs):
            raise SystemExit(f"{relative}: source {len(source_hits)} != mapping {len(pairs)}")

        before_nonself = [line for line in lines if not SELF_CHECK_RE.fullmatch(split_line(line)[0])]
        changed_lines = list(lines)
        for (new, old), (index, match) in zip(pairs, source_hits):
            ordinal = int(new["csv_ordinal"])
            if index + 1 != int(new["current_line"]):
                raise SystemExit(f"ordinal {ordinal}: current line {index + 1} != {new['current_line']}")
            if match.group("title") != new["title"]:
                raise SystemExit(f"ordinal {ordinal}: source title mismatch")
            if match.group("question") != old["reader_question"]:
                raise SystemExit(f"ordinal {ordinal}: source question is not the exact R02 original")
            final_question = str(new["final_question"])
            if "\n" in final_question or "\r" in final_question:
                raise SystemExit(f"ordinal {ordinal}: final question contains a line break")
            _, ending = split_line(lines[index])
            changed_lines[index] = (
                f"\\paragraph{{读前自检：{new['title']}。}}{final_question}\\par" + ending
            )
            total_replacements += 1

        after_nonself = [line for line in changed_lines if not SELF_CHECK_RE.fullmatch(split_line(line)[0])]
        if before_nonself != after_nonself:
            raise SystemExit(f"{relative}: a non-self-check line would change")
        new_raw = encode_source("".join(changed_lines), has_bom)
        if raw == new_raw:
            raise SystemExit(f"{relative}: no byte change prepared")
        prepared[path] = new_raw
        per_file.append(
            {
                "source_file": relative,
                "replacements": len(pairs),
                "line_count_before": len(lines),
                "line_count_after": len(changed_lines),
                "bom_preserved": has_bom,
                "non_self_check_lines_exact": True,
            }
        )

    if total_replacements != EXPECTED_RECORDS:
        raise SystemExit(f"prepared {total_replacements} replacements, expected 935")

    if args.apply:
        for path, payload in prepared.items():
            path.write_bytes(payload)

        verified = 0
        for relative, pairs in sorted(by_file.items()):
            path = source_root / Path(relative)
            lines = path.read_text(encoding="utf-8-sig").splitlines()
            hits = []
            for index, line in enumerate(lines):
                match = SELF_CHECK_RE.fullmatch(line)
                if match:
                    hits.append((index, match))
            if len(hits) != len(pairs):
                raise SystemExit(f"post-apply count mismatch in {relative}")
            for (new, _), (index, match) in zip(pairs, hits):
                if (
                    index + 1 != int(new["current_line"])
                    or match.group("title") != new["title"]
                    or match.group("question") != new["final_question"]
                ):
                    raise SystemExit(f"post-apply mismatch at ordinal {new['csv_ordinal']}")
                verified += 1
        if verified != EXPECTED_RECORDS:
            raise SystemExit(f"post-apply verified {verified}, expected 935")

    report = {
        "task_id": "M02-SA2-R1",
        "mode": "apply" if args.apply else "dry_run",
        "mapping_records": len(mapping),
        "source_files": len(prepared),
        "prepared_replacements": total_replacements,
        "post_apply_verified": total_replacements if args.apply else 0,
        "all_titles_preserved": True,
        "all_line_counts_preserved": True,
        "all_non_self_check_lines_exact": True,
        "files": per_file,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply the frozen M02 R2 mapping with exact baseline and line checks."""

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
    parser.add_argument("--baseline", required=True, type=Path)
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


def identity(row: dict[str, object]) -> tuple[int, str, str]:
    return (
        int(row["csv_ordinal"]),
        str(row["source_file"]).replace("\\", "/"),
        str(row["title"]),
    )


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    final = json.loads(args.mapping.read_text(encoding="utf-8"))
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    r02 = json.loads(args.r02.read_text(encoding="utf-8"))
    mapping = final["mapping"]
    prior = baseline["mapping"]
    original = r02["mapping"]
    if any(len(rows) != EXPECTED_RECORDS for rows in (mapping, prior, original)):
        raise SystemExit("mapping count is not 935")
    if [int(row["csv_ordinal"]) for row in mapping] != list(
        range(1, EXPECTED_RECORDS + 1)
    ):
        raise SystemExit("final ordinals are not contiguous")

    by_file: dict[
        str,
        list[tuple[dict[str, object], dict[str, object], dict[str, object]]],
    ] = defaultdict(list)
    for new, old, source_identity in zip(mapping, prior, original):
        if identity(new) != identity(old) or identity(new) != identity(source_identity):
            raise SystemExit(f"identity mismatch at ordinal {new['csv_ordinal']}")
        by_file[identity(new)[1]].append((new, old, source_identity))
    if len(by_file) != EXPECTED_FILES:
        raise SystemExit(f"mapping spans {len(by_file)} files, expected 37")

    prepared: dict[Path, bytes] = {}
    per_file: list[dict[str, object]] = []
    verified_baseline = 0
    changed_questions = 0
    for relative, triples in sorted(by_file.items()):
        path = source_root / Path(relative)
        raw = path.read_bytes()
        text, has_bom = decode_source(raw)
        lines = text.splitlines(keepends=True)
        source_hits: list[tuple[int, re.Match[str]]] = []
        for index, line in enumerate(lines):
            body, _ = split_line(line)
            match = SELF_CHECK_RE.fullmatch(body)
            if match:
                source_hits.append((index, match))
        if len(source_hits) != len(triples):
            raise SystemExit(
                f"{relative}: source {len(source_hits)} != mapping {len(triples)}"
            )

        before_nonself = [
            line for line in lines if not SELF_CHECK_RE.fullmatch(split_line(line)[0])
        ]
        changed_lines = list(lines)
        file_changes = 0
        for (new, old, _), (index, match) in zip(triples, source_hits):
            ordinal = int(new["csv_ordinal"])
            if index + 1 != int(new["current_line"]):
                raise SystemExit(
                    f"ordinal {ordinal}: current line {index + 1} != {new['current_line']}"
                )
            if match.group("title") != str(new["title"]):
                raise SystemExit(f"ordinal {ordinal}: source title mismatch")
            if match.group("question") != str(old["final_question"]):
                raise SystemExit(
                    f"ordinal {ordinal}: source question is not the exact frozen baseline"
                )
            final_question = str(new["final_question"])
            if "\n" in final_question or "\r" in final_question:
                raise SystemExit(f"ordinal {ordinal}: final question contains a line break")
            _, ending = split_line(lines[index])
            changed_lines[index] = (
                f"\\paragraph{{读前自检：{new['title']}。}}{final_question}\\par" + ending
            )
            verified_baseline += 1
            if final_question != str(old["final_question"]):
                file_changes += 1
                changed_questions += 1

        after_nonself = [
            line
            for line in changed_lines
            if not SELF_CHECK_RE.fullmatch(split_line(line)[0])
        ]
        if before_nonself != after_nonself:
            raise SystemExit(f"{relative}: a non-self-check line would change")
        new_raw = encode_source("".join(changed_lines), has_bom)
        if file_changes and raw == new_raw:
            raise SystemExit(f"{relative}: changed questions produced no byte change")
        if not file_changes and raw != new_raw:
            raise SystemExit(f"{relative}: byte change without a question change")
        if file_changes:
            prepared[path] = new_raw
        per_file.append(
            {
                "source_file": relative,
                "mapped_questions": len(triples),
                "changed_question_bodies": file_changes,
                "line_count_before": len(lines),
                "line_count_after": len(changed_lines),
                "bom_preserved": has_bom,
                "non_self_check_lines_exact": True,
            }
        )

    if verified_baseline != EXPECTED_RECORDS:
        raise SystemExit(
            f"baseline verified {verified_baseline}, expected {EXPECTED_RECORDS}"
        )

    if args.apply:
        for path, payload in prepared.items():
            path.write_bytes(payload)

        verified_final = 0
        for relative, triples in sorted(by_file.items()):
            path = source_root / Path(relative)
            raw = path.read_bytes()
            text, _ = decode_source(raw)
            lines = text.splitlines(keepends=True)
            hits: list[tuple[int, re.Match[str]]] = []
            for index, line in enumerate(lines):
                match = SELF_CHECK_RE.fullmatch(split_line(line)[0])
                if match:
                    hits.append((index, match))
            if len(hits) != len(triples):
                raise SystemExit(f"post-apply count mismatch in {relative}")
            for (new, _, _), (index, match) in zip(triples, hits):
                if (
                    index + 1 != int(new["current_line"])
                    or match.group("title") != str(new["title"])
                    or match.group("question") != str(new["final_question"])
                ):
                    raise SystemExit(
                        f"post-apply mismatch at ordinal {new['csv_ordinal']}"
                    )
                verified_final += 1
        if verified_final != EXPECTED_RECORDS:
            raise SystemExit(
                f"post-apply verified {verified_final}, expected {EXPECTED_RECORDS}"
            )
    else:
        verified_final = 0

    report = {
        "task_id": "M02-SA2-R2",
        "mode": "apply" if args.apply else "dry_run",
        "mapping_records": len(mapping),
        "mapped_source_files": len(by_file),
        "changed_source_files": len(prepared),
        "baseline_verified": verified_baseline,
        "changed_question_bodies": changed_questions,
        "post_apply_verified": verified_final,
        "all_titles_preserved": True,
        "all_line_counts_preserved": True,
        "all_non_self_check_lines_exact": True,
        "files": per_file,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

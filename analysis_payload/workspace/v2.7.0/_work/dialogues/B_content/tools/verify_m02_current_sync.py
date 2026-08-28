from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


mapping_path = Path(sys.argv[1])
worktree = Path(sys.argv[2])
output_path = Path(sys.argv[3])

payload = json.loads(mapping_path.read_text(encoding="utf-8"))
records = payload["mapping"]


def canonicalize_visible_terms(text: str) -> str:
    text = re.sub(r"Dirichlet(?:--|—|–|-)多项(?:式)?", r"\\DirichletMultinomial{}", text)
    text = re.sub(r"Metropolis(?:--|—|–|-)Hastings", r"\\MetropolisHastings{}", text)
    text = re.sub(r"(?<!\\)PageRank", r"\\PageRank{}", text)
    text = re.sub(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)近邻", r"\\kNN{}", text)
    text = re.sub(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)均值", r"\\kMeans{}", text)
    text = re.sub(r"(?:\$[kK]\$|(?<![A-Za-z\\])[kK]|𝑘)折", r"\\kFold{}", text)
    return text


file_cache: dict[str, str] = {}
current_questions_by_file: dict[str, list[tuple[int, str]]] = {}
question_prefix_count = 0
for source_file in sorted({record["source_file"] for record in records}):
    text = (worktree / source_file).read_text(encoding="utf-8")
    file_cache[source_file] = text
    current_questions = [
        (number, line)
        for number, line in enumerate(text.splitlines(), 1)
        if line.startswith(r"\paragraph{读前自检：")
    ]
    current_questions_by_file[source_file] = current_questions
    question_prefix_count += len(current_questions)

records_by_file: dict[str, list[dict]] = {}
for record in records:
    records_by_file.setdefault(record["source_file"], []).append(record)
for file_records in records_by_file.values():
    file_records.sort(key=lambda item: (item["current_line"], item["csv_ordinal"]))

forbidden_phrases = (
    "需要解决的阅读阻塞",
    "核验路线",
    "首次调用处",
    "下方严格细节保留",
    "原文",
    "相邻正文",
    "该对象",
    "这里",
    "本例",
)
line_pattern = re.compile(r"^\\paragraph\{读前自检：(.*?)。\}(.*)\\par$")
results = []
mode_counts: Counter[str] = Counter()
failures = []
historical_question_changes = []
current_question_texts = []

for source_file in sorted(records_by_file):
    file_records = records_by_file[source_file]
    current_questions = current_questions_by_file[source_file]
    if len(file_records) != len(current_questions):
        failures.append(
            {
                "source_file": source_file,
                "reason": "question_count_mismatch",
                "mapping_count": len(file_records),
                "current_count": len(current_questions),
            }
        )
        continue

    text = file_cache[source_file]
    for record, (current_line, current_source) in zip(file_records, current_questions, strict=True):
        match = line_pattern.fullmatch(current_source)
        if match is None:
            item = {
                "csv_ordinal": record["csv_ordinal"],
                "source_file": source_file,
                "historical_line": record["current_line"],
                "current_line": current_line,
                "title": record["title"],
                "match_mode": "invalid_current_structure",
                "status": "FAIL",
            }
            results.append(item)
            failures.append(item)
            continue

        current_title, current_question = match.groups()
        current_question_texts.append(current_question)
        historical_title = record["title"]
        historical_question = record["final_question"]
        canonical_title = canonicalize_visible_terms(historical_title)
        canonical_question = canonicalize_visible_terms(historical_question)
        if current_title == historical_title and current_question == historical_question:
            mode = "exact_r130"
        elif current_title == canonical_title and current_question == canonical_question:
            mode = "exact_after_required_term_canonicalization"
        else:
            mode = "current_revised"

        quality_failures = []
        if current_title not in {historical_title, canonical_title}:
            quality_failures.append("title_identity_changed")
        if len(current_question) < 38:
            quality_failures.append("question_too_short")
        if current_question.count("$") % 2:
            quality_failures.append("odd_math_delimiter")
        if current_question.count("{") != current_question.count("}"):
            quality_failures.append("brace_mismatch")
        for phrase in forbidden_phrases:
            if phrase in current_question:
                quality_failures.append(f"forbidden_phrase:{phrase}")

        excerpt = record.get("answer_anchor_excerpt") or ""
        canonical_excerpt = canonicalize_visible_terms(excerpt)
        excerpt_match = (not excerpt) or excerpt in text or canonical_excerpt in text
        passed = not quality_failures
        mode_counts[mode] += 1
        item = {
            "csv_ordinal": record["csv_ordinal"],
            "source_file": source_file,
            "historical_line": record["current_line"],
            "current_line": current_line,
            "historical_title": historical_title,
            "current_title": current_title,
            "match_mode": mode,
            "answer_anchor_match_informational": excerpt_match,
            "quality_failures": quality_failures,
            "status": "CURRENT_SOURCE_PASS" if passed else "FAIL",
        }
        results.append(item)
        if mode == "current_revised":
            historical_question_changes.append(
                {
                    "csv_ordinal": record["csv_ordinal"],
                    "source_file": source_file,
                    "current_line": current_line,
                    "historical_question": historical_question,
                    "current_question": current_question,
                }
            )
        if not passed:
            failures.append(item)

duplicate_current_lines = [
    {"source_file": key[0], "current_line": key[1], "count": count}
    for key, count in Counter(
        (item["source_file"], item["current_line"])
        for item in results
        if item["current_line"] is not None
    ).items()
    if count > 1
]

evidence = {
    "task_id": "B-M02-CURRENT-SYNC-R1",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "historical_mapping": str(mapping_path),
    "worktree": str(worktree),
    "records": len(records),
    "mapped_current_records": len(results),
    "source_files": len(file_cache),
    "question_prefix_count_in_mapped_files": question_prefix_count,
    "match_mode_counts": dict(mode_counts),
    "failures": failures,
    "historical_question_changes": historical_question_changes,
    "duplicate_current_lines": duplicate_current_lines,
    "acceptance": {
        "all_records_current": not failures,
        "all_unique_current_locations": not duplicate_current_lines,
        "all_current_questions_unique": len(set(current_question_texts)) == len(current_question_texts),
        "expected_records": len(records) == 935,
        "expected_files": len(file_cache) == 37,
    },
    "records_detail": results,
}

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: value for key, value in evidence.items() if key != "records_detail"}, ensure_ascii=False, indent=2))

if failures or duplicate_current_lines or len(records) != 935 or len(results) != 935 or len(file_cache) != 37:
    raise SystemExit(1)

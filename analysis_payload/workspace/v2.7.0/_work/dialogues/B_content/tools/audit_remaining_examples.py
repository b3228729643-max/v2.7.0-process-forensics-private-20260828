from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


inventory_path = Path(sys.argv[1])
candidate_csv = Path(sys.argv[2])
worktree = Path(sys.argv[3])
output_csv = Path(sys.argv[4])
output_json = Path(sys.argv[5])

with inventory_path.open("r", encoding="utf-8-sig", newline="") as handle:
    inventory_rows = list(csv.DictReader(handle))

with candidate_csv.open("r", encoding="utf-8-sig", newline="") as handle:
    candidate_rows = list(csv.DictReader(handle))

candidate_by_key = {row["例题号"]: row for row in candidate_rows}
target_rows = [
    row
    for row in inventory_rows
    if row["domain"] == "EXAMPLE"
    and row["current_state"] == "UNREVIEWED_CURRENT_SOURCE"
]

rows_by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
for row in inventory_rows:
    if row["domain"] == "EXAMPLE":
        rows_by_file[row["source_file"]].append(row)

block_by_key: dict[str, str] = {}
title_by_key: dict[str, str] = {}
for source_file, source_rows in rows_by_file.items():
    source = (worktree / source_file).read_text(encoding="utf-8")
    blocks = list(
        re.finditer(
            r"\\begin\{example\}\[(?P<title>.*?)\].*?\\end\{example\}.*?"
            r"\\SLExampleSolutionHeading\{.*?\}.*?\\begin\{solution\}"
            r"(?P<body>.*?)\\end\{solution\}",
            source,
            flags=re.DOTALL,
        )
    )
    if len(blocks) != len(source_rows):
        raise RuntimeError(
            f"example block count mismatch for {source_file}: "
            f"source={len(blocks)} inventory={len(source_rows)}"
        )
    for row, match in zip(source_rows, blocks, strict=True):
        block_by_key[row["object_key"]] = match.group("body")
        title_by_key[row["object_key"]] = " ".join(match.group("title").split())

stage_macros = {
    "read_translation": r"\\SLReadTranslation\b",
    "given": r"\\SolGiven\b",
    "method_trigger": r"\\SLMethodTrigger\b",
    "plan": r"\\SolPlan\b",
    "derive": r"\\SolDerive\b",
    "check": r"\\SolCheck\b",
    "answer": r"\\SolAnswer\b",
}

generic_patterns = {
    "generic_title_translation": "题目要求完成",
    "generic_matrix_route": "先标注每个矩阵/向量维数",
    "generic_candidate_isolation": "候选模型、验证数据与测试数据彼此隔离",
    "generic_uniform_protocol": "先固定比较协议，再逐项计算",
}

severity_points = {"高": 30, "中": 20, "低": 10, "无": 0, "": 0}
audit_rows: list[dict[str, object]] = []
for row in target_rows:
    key = row["object_key"]
    block = block_by_key[key]
    candidate = candidate_by_key[key]
    stage_counts = {
        name: len(re.findall(pattern, block)) for name, pattern in stage_macros.items()
    }
    missing = [name for name, count in stage_counts.items() if count == 0]
    duplicates = [
        f"{name}:{count}" for name, count in stage_counts.items() if count > 1
    ]
    generic_hits = [
        name for name, phrase in generic_patterns.items() if phrase in block
    ]
    issue = row["issue"]
    risk = severity_points.get(row["severity"], 0)
    risk += 7 * len(missing)
    if stage_counts["answer"] != 1:
        risk += 18
    if "错套" in issue:
        risk += 30
    if "工程状态码" in issue:
        risk += 25
    if "重复" in issue or "回收不够显式" in issue:
        risk += 18
    if "信息密度" in issue:
        risk += 12
    risk += 10 * len(generic_hits)
    audit_rows.append(
        {
            "task_id": row["task_id"],
            "object_key": key,
            "title": title_by_key[key],
            "source_file": row["source_file"],
            "source_line": row["source_line"],
            "severity": row["severity"],
            "issue": issue,
            "candidate_route": candidate["推荐解题路线"],
            "candidate_check": candidate["推荐核验"],
            "solution_chars": len(block),
            "missing_stages": ";".join(missing),
            "duplicate_stages": ";".join(duplicates),
            "answer_count": stage_counts["answer"],
            "generic_hits": ";".join(generic_hits),
            "risk_score": risk,
        }
    )

audit_rows.sort(key=lambda item: (-int(item["risk_score"]), item["task_id"]))
fieldnames = list(audit_rows[0])
with output_csv.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(audit_rows)

summary = {
    "target_examples": len(audit_rows),
    "missing_stage_counts": dict(
        Counter(
            stage
            for row in audit_rows
            for stage in str(row["missing_stages"]).split(";")
            if stage
        )
    ),
    "answer_count_distribution": dict(
        Counter(str(row["answer_count"]) for row in audit_rows)
    ),
    "duplicate_stage_rows": sum(
        1 for row in audit_rows if str(row["duplicate_stages"])
    ),
    "generic_hit_counts": dict(
        Counter(
            hit
            for row in audit_rows
            for hit in str(row["generic_hits"]).split(";")
            if hit
        )
    ),
    "candidate_issue_counts": dict(Counter(row["issue"] for row in audit_rows)),
    "top_risk": audit_rows[:15],
}
output_json.write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False, indent=2))

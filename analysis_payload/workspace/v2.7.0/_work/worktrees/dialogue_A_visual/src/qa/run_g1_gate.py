#!/usr/bin/env python3
"""Run the single formal v1.8.0 G1 source-freeze gate.

This runner composes the project-wide source/link audits, the independent
unittest suite, and the 199-row closure-table source mapping into one
machine-readable decision.  It does not build PDFs and therefore cannot be
used as G2 or G3 evidence.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa" / "gates" / "G1"


def run_command(name: str, arguments: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    log_path = OUT / f"{name}.log"
    log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    return {
        "command": arguments,
        "returncode": completed.returncode,
        "log": str(log_path.relative_to(ROOT).as_posix()),
    }


def closure_check() -> dict[str, object]:
    candidates = sorted((ROOT / "audit").glob("*v1.8.0*.csv"))
    findings: list[str] = []
    if len(candidates) != 1:
        return {
            "passed": False,
            "findings": [f"expected one v1.8.0 closure CSV, found {len(candidates)}"],
        }

    path = candidates[0]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = list(reader)

    if len(header) != 22:
        findings.append(f"expected 22 columns, found {len(header)}")
    if len(rows) != 199:
        findings.append(f"expected 199 issue rows, found {len(rows)}")

    priority_counts = Counter(row[1] for row in rows if len(row) > 1)
    expected_priorities = {"P1": 4, "P2": 182, "P3": 13}
    if dict(priority_counts) != expected_priorities:
        findings.append(
            f"priority counts {dict(priority_counts)!r} != {expected_priorities!r}"
        )

    allowed = {
        "fixed_pending_verification",
        "verified",
        "not_applicable_verified",
    }
    status_counts = Counter(row[14] for row in rows if len(row) > 14)
    disallowed = sorted(set(status_counts) - allowed)
    if disallowed:
        findings.append(f"source gate has disallowed statuses: {disallowed}")

    evidence_columns = {
        12: "source file",
        13: "source anchor",
        15: "change summary",
        16: "verification command",
        17: "verification result",
        18: "evidence file",
    }
    ids = Counter(row[0] for row in rows if row)
    duplicates = sorted(issue_id for issue_id, count in ids.items() if count != 1)
    if duplicates:
        findings.append(f"non-unique issue IDs: {duplicates}")
    for row_number, row in enumerate(rows, start=2):
        if len(row) != 22:
            findings.append(f"CSV row {row_number} has {len(row)} columns")
            continue
        for index, label in evidence_columns.items():
            if not row[index].strip():
                findings.append(f"{row[0]}: empty {label}")

    return {
        "passed": not findings,
        "file": str(path.relative_to(ROOT).as_posix()),
        "rows": len(rows),
        "columns": len(header),
        "priority_counts": dict(priority_counts),
        "status_counts": dict(status_counts),
        "findings": findings,
    }


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    static_json = OUT / "static_source_audit.json"
    link_json = OUT / "link_and_label_audit.json"

    static_run = run_command(
        "static_source_audit",
        [sys.executable, "qa/static_source_audit.py", "--json", str(static_json)],
    )
    link_run = run_command(
        "link_and_label_audit",
        [sys.executable, "qa/link_and_label_audit.py", "--json", str(link_json)],
    )
    unittest_run = run_command(
        "full_unittest",
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    )

    static_result = load_json(static_json) if static_json.exists() else {}
    link_result = load_json(link_json) if link_json.exists() else {}
    closure_result = closure_check()
    test_log = (ROOT / str(unittest_run["log"])).read_text(encoding="utf-8")
    test_count_match = re.search(r"Ran\s+(\d+)\s+tests?", test_log)
    test_count = int(test_count_match.group(1)) if test_count_match else None

    checks = {
        "closure_table": closure_result,
        "static_source": {
            "passed": static_run["returncode"] == 0 and bool(static_result.get("passed")),
            "run": static_run,
            "summary": static_result.get("summary"),
        },
        "link_and_label": {
            "passed": link_run["returncode"] == 0 and bool(link_result.get("passed")),
            "run": link_run,
            "summary": link_result.get("summary"),
        },
        "independent_tests": {
            "passed": unittest_run["returncode"] == 0 and test_count == 228,
            "run": unittest_run,
            "tests_run": test_count,
        },
    }
    passed = all(bool(check["passed"]) for check in checks.values())
    report = {
        "schema_version": 1,
        "gate": "G1",
        "scope": "source-freeze static gate",
        "executed_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_root": str((ROOT / "讲义源码").resolve()),
        "passed": passed,
        "checks": checks,
        "limitations": [
            "G1 contains no candidate-PDF evidence and does not imply G2/G3 passage.",
            "H0 remains unavailable while the third authority PDF is missing.",
        ],
    }
    report_path = OUT / "G1_gate_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": "G1", "passed": passed, "report": str(report_path)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

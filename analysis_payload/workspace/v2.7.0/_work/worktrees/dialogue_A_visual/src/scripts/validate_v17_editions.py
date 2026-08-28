from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import fitz


WORKSPACE = Path(__file__).resolve().parents[1]
TEST_DIR = WORKSPACE / "tests"
EXPECTED_FULL_NAME = "统计学习方法初学者讲义_合并总册v1.7.0_完整解析版.pdf"
BLOCKER_RE = re.compile(
    r"LaTeX Error|Undefined control sequence|undefined references|"
    r"undefined citations|Missing character|Overfull \\hbox|"
    r"Overfull \\vbox|Float too large",
    re.I,
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def extract_text(pdf: Path, output: Path) -> str:
    executable = shutil.which("pdftotext")
    if not executable:
        raise RuntimeError("pdftotext is not available on PATH")
    subprocess.run(
        [executable, "-layout", str(pdf), str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return output.read_text(encoding="utf-8")


def pdf_evidence(pdf: Path) -> dict[str, object]:
    document = fitz.open(pdf)
    contract_links = 0
    launch_files: list[str] = []
    link_kinds: Counter[int] = Counter()
    for page in document:
        for link in page.get_links():
            link_kinds[link.get("kind", 0)] += 1
            if link.get("nameddest") == "SL:algorithm-contract":
                contract_links += 1
            if link.get("kind") == fitz.LINK_GOTOR and link.get("file"):
                launch_files.append(unquote(str(link["file"])))
    return {
        "pages": len(document),
        "contract_links": contract_links,
        "launch_files": dict(Counter(launch_files)),
        "link_kinds": {str(key): value for key, value in sorted(link_kinds.items())},
    }


def log_blockers(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if BLOCKER_RE.search(line):
            rows.append({"line": number, "text": line})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v1.7.0 student/full/default PDF editions.")
    parser.add_argument("--student", type=Path, required=True)
    parser.add_argument("--full", type=Path, required=True)
    parser.add_argument("--default", dest="default_pdf", type=Path, required=True)
    parser.add_argument("--student-log", type=Path, required=True)
    parser.add_argument("--full-log", type=Path, required=True)
    parser.add_argument("--default-log", type=Path, required=True)
    args = parser.parse_args()

    paths = {
        "student": args.student.resolve(),
        "full": args.full.resolve(),
        "default": args.default_pdf.resolve(),
    }
    logs = {
        "student": args.student_log.resolve(),
        "full": args.full_log.resolve(),
        "default": args.default_log.resolve(),
    }
    missing = [str(path) for path in (*paths.values(), *logs.values()) if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing validation inputs: " + ", ".join(missing))

    TEST_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v17-editions-") as temporary:
        temp = Path(temporary)
        texts = {
            name: extract_text(path, temp / f"{name}.txt")
            for name, path in paths.items()
        }

    pdfs = {name: pdf_evidence(path) for name, path in paths.items()}
    blockers = {name: log_blockers(path) for name, path in logs.items()}
    patterns = {
        "student_placeholder": r"完整解析入口",
        "full_answer_box": r"章末练习完整解析",
        "solution_heading": r"练习\s*\d+(?:\.\d+)*\s*(?:完整)?解析",
        "original_solution_section": r"【原书练习整理】解析",
    }
    counts = {
        edition: {
            name: len(re.findall(pattern, text))
            for name, pattern in patterns.items()
        }
        for edition, text in texts.items()
    }
    text_hashes = {
        name: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for name, text in texts.items()
    }

    checks = {
        "logs_have_no_blockers": all(not rows for rows in blockers.values()),
        "student_has_37_placeholders": counts["student"]["student_placeholder"] == 37,
        "student_has_no_solution_headings": counts["student"]["solution_heading"] == 0,
        "student_has_no_full_answer_boxes": counts["student"]["full_answer_box"] == 0,
        "student_has_no_original_solution_sections": counts["student"]["original_solution_section"] == 0,
        "full_has_37_answer_boxes": counts["full"]["full_answer_box"] == 37,
        "full_has_553_solution_headings": counts["full"]["solution_heading"] == 553,
        "default_has_37_answer_boxes": counts["default"]["full_answer_box"] == 37,
        "default_has_553_solution_headings": counts["default"]["solution_heading"] == 553,
        "default_and_full_text_match": text_hashes["default"] == text_hashes["full"],
        "student_is_shorter_than_full": pdfs["student"]["pages"] < pdfs["full"]["pages"],
        "default_and_full_pages_match": pdfs["default"]["pages"] == pdfs["full"]["pages"],
        "all_editions_have_70_algorithm_contract_links": all(
            evidence["contract_links"] == 70 for evidence in pdfs.values()
        ),
        "student_has_37_full_edition_launch_links": (
            pdfs["student"]["launch_files"].get(EXPECTED_FULL_NAME, 0) == 37
            and sum(pdfs["student"]["launch_files"].values()) == 37
        ),
    }
    passed = all(checks.values())
    report = {
        "generated_at": now_iso(),
        "passed": passed,
        "checks": checks,
        "paths": {name: str(path) for name, path in paths.items()},
        "logs": {name: str(path) for name, path in logs.items()},
        "pdfs": pdfs,
        "text_counts": counts,
        "text_sha256": text_hashes,
        "log_blockers": blockers,
    }
    (TEST_DIR / "v1.7_edition_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# v1.7.0 双版本与默认版审计",
        "",
        f"生成时间：{report['generated_at']}",
        f"结论：{'通过' if passed else '未通过'}（{sum(checks.values())}/{len(checks)} checks passed）",
        "",
        "| Check | 结果 |",
        "|---|---|",
    ]
    lines.extend(f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in checks.items())
    lines.append("")
    (TEST_DIR / "v1.7_edition_audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"checks": len(checks), "passed": passed, "failed": len(checks) - sum(checks.values())}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import csv
import hashlib
import json
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path(
    r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual"
    r"\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05"
    r"\fig_v5_c05_dependency_graph.tex"
)
EXPECTED_SOURCE_SHA256 = "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D"
EXCLUDED = {"MANIFEST.csv", "MANIFEST.json", "WRITE_STOPPED"}


def payload_rows() -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED:
            continue
        stat = path.stat()
        rows.append({"RELATIVE_PATH": rel, "BYTES": stat.st_size, "MTIME_NS": stat.st_mtime_ns})
    return rows


def parse_structured_files(include_manifests: bool) -> tuple[int, int]:
    json_count = 0
    csv_count = 0
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        if not include_manifests and rel in {"MANIFEST.csv", "MANIFEST.json"}:
            continue
        if path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
            json_count += 1
        elif path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                list(csv.DictReader(handle))
            csv_count += 1
    return json_count, csv_count


def main() -> None:
    marker = ROOT / "WRITE_STOPPED"
    if marker.exists():
        raise AssertionError("package is already sealed")

    required = [
        ROOT / "00_BEFORE_IDENTITY.md",
        ROOT / "01_NARROW_PATCH_DECISION.md",
        ROOT / "02_EXACT_DIFF.md",
        ROOT / "03_STATIC_VALIDATION.md",
        ROOT / "04_BUILD_SLOT_REQUEST.md",
        ROOT / "05_BUILD_ATTEMPT_01.md",
        ROOT / "06_RETRY_ROOT_CAUSE.md",
        ROOT / "MODEL_ROUTE.md",
        ROOT / "build" / "latexmk.stdout.log",
        ROOT / "build" / "latexmk.stderr.log",
        ROOT / "build" / "v260_FIG-P654-01_standalone.log",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise AssertionError(f"required files missing: {missing}")

    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"target source identity changed: {source_sha}")

    pdfs = sorted((ROOT / "build").glob("*.pdf"))
    if pdfs:
        raise AssertionError(f"unexpected PDF in failed build package: {pdfs}")

    combined_log = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (
            ROOT / "build" / "latexmk.stdout.log",
            ROOT / "build" / "latexmk.stderr.log",
            ROOT / "build" / "v260_FIG-P654-01_standalone.log",
        )
    )
    if "no writeable cache path" not in combined_log:
        raise AssertionError("expected luaotfload writable-cache failure not found")
    if "Fatal error occurred" not in combined_log or "no output PDF" not in combined_log:
        raise AssertionError("expected no-output-PDF terminal diagnostic not found")

    status = {
        "figure_id": "FIG-P654-01",
        "role": "SA2=gpt-5.6-sol/max",
        "state": "BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
        "source_sha256": source_sha,
        "invocation_count": 1,
        "latexmk_pid": 10084,
        "latexmk_exit": 12,
        "natural_exit": True,
        "pre_tex_processes": "NONE",
        "post_tex_processes": "NONE",
        "slot_release": "P654_BUILD_SLOT_RELEASED",
        "pdf_count": 0,
        "pdf_identity": None,
        "failure_phase": "pre-document luaotfload initialization",
        "root_cause": "no writable luaotfload cache path",
        "native_300dpi_run": False,
        "object_denominator_run": False,
        "unordered_pair_denominator_run": False,
        "target_height_measured_after_patch": False,
        "sa2_pass_claimed": False,
        "fresh_sa1_started": False,
        "sa3_started": False,
        "git_commit_created": False,
        "retry_request": "P654_RETRY_ROOT_CAUSE_READY_REQUEST_BUILD_SLOT",
    }
    (ROOT / "PACKAGE_STATUS.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "RESULT.txt").write_text("BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2\n", encoding="utf-8")

    pre_json_count, pre_csv_count = parse_structured_files(include_manifests=False)
    (ROOT / "TERMINAL_CROSSCHECK.txt").write_text(
        "\n".join(
            [
                "FIGURE_ID=FIG-P654-01",
                "MODEL_ROUTE=SA2=gpt-5.6-sol/max",
                "SOURCE_SHA256=" + source_sha,
                "INVOCATION_COUNT=1",
                "LATEXMK_PID=10084",
                "LATEXMK_EXIT=12",
                "NATURAL_EXIT=TRUE",
                "PRE_TEX_PROCESSES=NONE",
                "POST_TEX_PROCESSES=NONE",
                "P654_BUILD_SLOT_RELEASED=TRUE",
                "PDF_COUNT=0",
                "ROOT_CAUSE=PRE_DOCUMENT_LUAOTFLOAD_NO_WRITABLE_CACHE_PATH",
                "NATIVE_300DPI_RUN=FALSE",
                "OBJECT_N116_RUN=FALSE",
                "UNORDERED_PAIR_C6670_RUN=FALSE",
                "ADS_PRESEAL_COUNT=0",
                f"STRUCTURED_PREMANIFEST_JSON_PARSE_COUNT={pre_json_count}",
                f"STRUCTURED_PREMANIFEST_CSV_PARSE_COUNT={pre_csv_count}",
                "RESULT=BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
                "RETRY_REQUEST=P654_RETRY_ROOT_CAUSE_READY_REQUEST_BUILD_SLOT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rows = payload_rows()
    with (ROOT / "MANIFEST.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["RELATIVE_PATH", "BYTES", "MTIME_NS"])
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "MANIFEST.json").write_text(
        json.dumps(
            {
                "package": "FIG-P654-01 STRICT_R4 SA2 narrow source patch build failure",
                "payload_scope": "all ordinary files recursively except MANIFEST.csv, MANIFEST.json, and WRITE_STOPPED",
                "payload_file_count": len(rows),
                "files": rows,
                "result": "BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_json = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    with (ROOT / "MANIFEST.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        manifest_csv = list(csv.DictReader(handle))
    csv_normalized = [
        {"RELATIVE_PATH": row["RELATIVE_PATH"], "BYTES": int(row["BYTES"]), "MTIME_NS": int(row["MTIME_NS"])}
        for row in manifest_csv
    ]
    current = payload_rows()
    if manifest_json["files"] != current or csv_normalized != current:
        raise AssertionError("manifest payload mismatch")
    final_json_count, final_csv_count = parse_structured_files(include_manifests=True)

    time.sleep(0.05)
    marker.write_text(
        "\n".join(
            [
                "FIGURE_ID=FIG-P654-01",
                "MODEL_ROUTE=SA2=gpt-5.6-sol/max",
                "LATEXMK_PID=10084",
                "LATEXMK_EXIT=12",
                "PDF_COUNT=0",
                "MANIFEST_PAYLOAD_MATCH=TRUE",
                f"PAYLOAD_FILE_COUNT={len(current)}",
                f"JSON_PARSE_COUNT={final_json_count}",
                f"CSV_PARSE_COUNT={final_csv_count}",
                "ADS_PRESEAL_COUNT=0",
                "RESULT=BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
                "RETRY_REQUEST=P654_RETRY_ROOT_CAUSE_READY_REQUEST_BUILD_SLOT",
                "NO_WRITES_PERMITTED_AFTER_THIS_MARKER=TRUE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "payload_file_count": len(current),
                "json_parse_count": final_json_count,
                "csv_parse_count": final_csv_count,
                "pdf_count": 0,
                "result": "BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
            }
        )
    )


if __name__ == "__main__":
    main()

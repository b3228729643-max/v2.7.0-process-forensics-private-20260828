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


def parse_structured(include_manifests: bool) -> tuple[int, int]:
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
        raise AssertionError("R5 package is already sealed")
    required = [
        ROOT / "00_RETRY_AUTHORITY_AND_IDENTITY.md",
        ROOT / "01_RETRY_INVOCATION.md",
        ROOT / "02_FAILURE_AND_GATE_STATUS.md",
        ROOT / "03_R4_R5_READ_ONLY_COMPARISON.md",
        ROOT / "MODEL_ROUTE.md",
        ROOT / "build" / "latexmk.stdout.log",
        ROOT / "build" / "latexmk.stderr.log",
        ROOT / "build" / "v260_FIG-P654-01_standalone.log",
        ROOT / "texmf-var",
        ROOT / "texmf-cache",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise AssertionError(f"required paths missing: {missing}")
    if any((ROOT / "texmf-var").iterdir()) or any((ROOT / "texmf-cache").iterdir()):
        raise AssertionError("cache directories were expected to remain empty after failed initialization")
    if list((ROOT / "build").glob("*.pdf")):
        raise AssertionError("unexpected PDF exists in no-candidate package")
    source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise AssertionError(f"source identity changed: {source_sha}")
    logs = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (
            ROOT / "build" / "latexmk.stdout.log",
            ROOT / "build" / "latexmk.stderr.log",
            ROOT / "build" / "v260_FIG-P654-01_standalone.log",
        )
    )
    if "no writeable cache path" not in logs or "Fatal error occurred" not in logs or "no output PDF" not in logs:
        raise AssertionError("expected pre-document cache/no-PDF diagnostics not found")

    status = {
        "figure_id": "FIG-P654-01",
        "role": "SA2=gpt-5.6-sol/max",
        "state": "BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
        "source_sha256": source_sha,
        "r5_controller_count": 1,
        "latexmk_pid": 16296,
        "latexmk_exit": 12,
        "natural_exit": True,
        "pre_tex_processes": "NONE",
        "post_tex_processes": "NONE",
        "slot_release": "P654_RETRY_BUILD_SLOT_RELEASED",
        "controller_shell_texmfvar_assignment": str(ROOT / "texmf-var"),
        "controller_shell_texmfcache_assignment": str(ROOT / "texmf-cache"),
        "wrapper_env_inheritance_mode": "Start-Process default inheritance intended; no explicit -Environment override",
        "actual_latexmk_env_visible_values": "NOT_CAPTURED",
        "actual_lualatex_env_visible_values": "NOT_CAPTURED",
        "kpsewhich_run": False,
        "engine_cache_resolution": "UNKNOWN_NOT_CAPTURED",
        "child_write_probe": "NOT_CAPTURED",
        "cache_directories_empty_after_exit": True,
        "pdf_count": 0,
        "pdf_identity": None,
        "failure_phase": "pre-document luaotfload initialization",
        "first_fatal_line_number": 12,
        "first_fatal_line": "luaotfload | load : FATAL ERROR",
        "document_boundary": "wrapper line 1; ctexbook.cls not loaded; target business source not read",
        "inner_lualatex_return_code": 1,
        "outer_exit_12_source": "latexmk/runscript controller after failed lualatex rule",
        "native_300dpi_run": False,
        "object_N116_run": False,
        "unordered_pairs_C6670_run": False,
        "target_height_measured_after_patch": False,
        "third_build_started": False,
        "sa2_pass_claimed": False,
        "fresh_sa1_started": False,
        "sa3_started": False,
        "git_commit_created": False,
    }
    (ROOT / "PACKAGE_STATUS.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "RESULT.txt").write_text("BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2\n", encoding="utf-8")
    pre_json, pre_csv = parse_structured(include_manifests=False)
    (ROOT / "TERMINAL_CROSSCHECK.txt").write_text(
        "\n".join(
            [
                "FIGURE_ID=FIG-P654-01",
                "MODEL_ROUTE=SA2=gpt-5.6-sol/max",
                "SOURCE_SHA256=" + source_sha,
                "R5_CONTROLLER_COUNT=1",
                "LATEXMK_PID=16296",
                "LATEXMK_EXIT=12",
                "NATURAL_EXIT=TRUE",
                "PRE_TEX_PROCESSES=NONE",
                "POST_TEX_PROCESSES=NONE",
                "P654_RETRY_BUILD_SLOT_RELEASED=TRUE",
                "CONTROLLER_SHELL_TEXMFVAR_ASSIGNED=TRUE",
                "CONTROLLER_SHELL_TEXMFCACHE_ASSIGNED=TRUE",
                "ACTUAL_LATEXMK_ENV_VALUES=NOT_CAPTURED",
                "ACTUAL_LUALATEX_ENV_VALUES=NOT_CAPTURED",
                "KPSEWHICH_RUN=FALSE",
                "ENGINE_CACHE_RESOLUTION=UNKNOWN_NOT_CAPTURED",
                "CHILD_WRITE_PROBE=NOT_CAPTURED",
                "CACHE_DIRECTORIES_EMPTY_AFTER_EXIT=TRUE",
                "FIRST_FATAL_LINE_NUMBER=12",
                "FIRST_FATAL_LINE=luaotfload | load : FATAL ERROR",
                "DOCUMENT_BOUNDARY=WRAPPER_LINE_1_BEFORE_CTEXBOOK_CLASS_AND_TARGET_SOURCE",
                "INNER_LUALATEX_RETURN_CODE=1",
                "OUTER_EXIT_12_SOURCE=LATEXMK_RUNSCRIPT_AFTER_FAILED_ENGINE_RULE",
                "PDF_COUNT=0",
                "NATIVE_300DPI_RUN=FALSE",
                "OBJECT_N116_RUN=FALSE",
                "UNORDERED_PAIR_C6670_RUN=FALSE",
                "THIRD_BUILD_STARTED=FALSE",
                "ADS_PRESEAL_COUNT=0",
                f"STRUCTURED_PREMANIFEST_JSON_PARSE_COUNT={pre_json}",
                f"STRUCTURED_PREMANIFEST_CSV_PARSE_COUNT={pre_csv}",
                "RESULT=BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
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
                "package": "FIG-P654-01 STRICT_R5 SA2 writable-cache retry build failure",
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
    csv_rows = [
        {"RELATIVE_PATH": row["RELATIVE_PATH"], "BYTES": int(row["BYTES"]), "MTIME_NS": int(row["MTIME_NS"])}
        for row in manifest_csv
    ]
    current = payload_rows()
    if manifest_json["files"] != current or csv_rows != current:
        raise AssertionError("manifest payload mismatch")
    final_json, final_csv = parse_structured(include_manifests=True)
    time.sleep(0.05)
    marker.write_text(
        "\n".join(
            [
                "FIGURE_ID=FIG-P654-01",
                "MODEL_ROUTE=SA2=gpt-5.6-sol/max",
                "LATEXMK_PID=16296",
                "LATEXMK_EXIT=12",
                "PDF_COUNT=0",
                "MANIFEST_PAYLOAD_MATCH=TRUE",
                f"PAYLOAD_FILE_COUNT={len(current)}",
                f"JSON_PARSE_COUNT={final_json}",
                f"CSV_PARSE_COUNT={final_csv}",
                "ADS_PRESEAL_COUNT=0",
                "RESULT=BUILD_FAIL_NO_CANDIDATE_CONTINUE_SA2",
                "NO_THIRD_BUILD_PERMITTED=TRUE",
                "NO_WRITES_PERMITTED_AFTER_THIS_MARKER=TRUE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"payload_file_count": len(current), "json_parse_count": final_json, "csv_parse_count": final_csv, "pdf_count": 0, "result": status["state"]}))


if __name__ == "__main__":
    main()

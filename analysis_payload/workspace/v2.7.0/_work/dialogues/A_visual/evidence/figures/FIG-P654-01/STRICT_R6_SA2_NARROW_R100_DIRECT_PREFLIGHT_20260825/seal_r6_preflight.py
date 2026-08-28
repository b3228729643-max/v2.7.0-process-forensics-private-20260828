from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "texcache"
PROBE = CACHE / "P654_R6_CHILD_WRITE_PROBE.txt"
CHILD = ROOT / "CHILD_PREFLIGHT_ATTEMPT2.json"
PARENT = ROOT / "PARENT_PREFLIGHT_RESULT_ATTEMPT2.json"
REPO = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual")
SOURCE_REL = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex"
WRAPPER_REL = "src/讲义源码/合并总册/v260_FIG-P654-01_standalone.tex"
SOURCE = REPO / SOURCE_REL
WRAPPER = REPO / WRAPPER_REL
SOURCE_SHA = "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D"
WRAPPER_SHA = "FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1"
PROBE_SHA = "4ECE7048D6D816959FD437DC55A8C7A3AED6ED6C4320C474F6D5B965225C21C8"
EXCLUDED = {"MANIFEST.csv", "MANIFEST.json", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


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
        raise AssertionError("R6 package already sealed")
    required = [
        ROOT / "00_PARENT_LAUNCH_ENCODING_NOTE.md",
        ROOT / "01_DIRECT_PREFLIGHT_PASS.md",
        ROOT / "02_SOURCE_WRAPPER_GIT_PREFLIGHT.md",
        ROOT / "03_DIRECT_LUALATEX_DECISION.md",
        ROOT / "MODEL_ROUTE.md",
        ROOT / "child_env_kpse_probe.ps1",
        ROOT / "run_direct_parent_preflight.ps1",
        ROOT / "CHILD_PREFLIGHT.json",
        ROOT / "PARENT_PREFLIGHT_RESULT.json",
        CHILD,
        PARENT,
        PROBE,
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise AssertionError(f"required preflight evidence missing: {missing}")
    if list(ROOT.rglob("*.pdf")):
        raise AssertionError("R6 diagnostic package must not contain a PDF")

    child = json.loads(CHILD.read_text(encoding="utf-8"))
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    binding = parent["exact_environment_binding"]
    if parent["pass"] is not True or child["pass"] is not True:
        raise AssertionError("accepted attempt-2 preflight is not PASS")
    parent_env = parent["parent_environment"]
    child_env = child["environment"]
    for name in ("TEXMFVAR", "TEXMFCACHE", "TEXMFCONFIG"):
        if parent_env[name] != binding or child_env[name] != binding:
            raise AssertionError(f"environment mismatch: {name}")
    rows = child["kpsewhich"]
    if len(rows) != 3 or {row["variable"] for row in rows} != {"TEXMFVAR", "TEXMFCACHE", "TEXMFCONFIG"}:
        raise AssertionError("kpsewhich variable denominator mismatch")
    for row in rows:
        checks = (
            row["env_visible_value"] == binding,
            row["var_value_exit"] == 0,
            row["var_value_raw"] == binding,
            row["var_value_exact_expected"] is True,
            row["var_value_canonical_expected"] is True,
            row["expand_exit"] == 0,
            row["expand_raw"] == binding,
            row["expand_exact_expected"] is True,
            row["expand_canonical_expected"] is True,
        )
        if not all(checks):
            raise AssertionError(f"kpsewhich resolution failed: {row['variable']}")

    cache_entries = list(CACHE.iterdir())
    if cache_entries != [PROBE]:
        raise AssertionError(f"texcache must contain exactly the probe: {cache_entries}")
    probe_stat = PROBE.stat()
    probe_ticks = probe_stat.st_mtime_ns // 100 + 621355968000000000
    recorded_probe = child["probe"]
    if Path(recorded_probe["absolute_path"]) != PROBE:
        raise AssertionError("probe path mismatch")
    if probe_stat.st_size != recorded_probe["bytes"] or probe_stat.st_size != 42:
        raise AssertionError("probe byte mismatch")
    if probe_ticks != recorded_probe["mtime_ticks_utc"]:
        raise AssertionError("probe mtime mismatch")
    if sha256(PROBE) != recorded_probe["sha256"] or sha256(PROBE) != PROBE_SHA:
        raise AssertionError("probe SHA mismatch")

    if sha256(SOURCE) != SOURCE_SHA:
        raise AssertionError("target source SHA changed")
    if sha256(WRAPPER) != WRAPPER_SHA:
        raise AssertionError("wrapper SHA changed")
    expected_path = SOURCE_REL.encode("utf-8")
    names = git("diff", "--name-only", "-z")
    if names.returncode != 0 or names.stdout.split(b"\0")[:-1] != [expected_path]:
        raise AssertionError("Git diff scope is not exactly the target source")
    numstat = git("diff", "--numstat", "-z")
    if numstat.returncode != 0 or numstat.stdout != b"1\t1\t" + expected_path + b"\0":
        raise AssertionError(f"Git numstat mismatch: {numstat.stdout!r}")
    status = git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status.returncode != 0 or status.stdout != b" M " + expected_path + b"\0":
        raise AssertionError(f"Git status scope mismatch: {status.stdout!r}")
    if git("diff", "--check").returncode != 0:
        raise AssertionError("git diff --check failed")
    if git("diff", "--quiet", "--", WRAPPER_REL).returncode != 0:
        raise AssertionError("standalone wrapper has a Git diff")

    status_record = {
        "figure_id": "FIG-P654-01",
        "role": "SA2 root diagnostic",
        "result": "DIRECT_PREFLIGHT_PASS_AWAITING_BUILD_SLOT",
        "typesetting_invocations": 0,
        "parent_pid": parent["parent_pid"],
        "child_pid": child["child_process"]["pid"],
        "exact_binding": binding,
        "environment_variable_count": 3,
        "environment_unique_value_count": 1,
        "kpsewhich_variable_rows": 3,
        "kpsewhich_checks": 6,
        "kpsewhich_failures": 0,
        "probe": recorded_probe,
        "texcache_entry_count": 1,
        "source_sha256": SOURCE_SHA,
        "wrapper_sha256": WRAPPER_SHA,
        "git_diff_file_count": 1,
        "git_numstat": {"insertions": 1, "deletions": 1},
        "current_slot_owner": "B-P05 R2",
        "direct_lualatex_started": False,
        "request": "P654_R6_DIRECT_PREFLIGHT_READY_REQUEST_BUILD_SLOT",
        "p608_precedent_isolation": "P654 root-diagnostic only; forbidden from P608 fresh-SA1 context/evidence",
    }
    (ROOT / "PACKAGE_STATUS.json").write_text(json.dumps(status_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "RESULT.txt").write_text("DIRECT_PREFLIGHT_PASS_AWAITING_BUILD_SLOT\n", encoding="utf-8")
    pre_json, pre_csv = parse_structured(include_manifests=False)
    (ROOT / "TERMINAL_CROSSCHECK.txt").write_text(
        "\n".join(
            [
                "FIGURE_ID=FIG-P654-01",
                "ROLE=SA2_ROOT_DIAGNOSTIC",
                "TYPESETTING_INVOCATIONS=0",
                "PARENT_PID=" + str(parent["parent_pid"]),
                "CHILD_PID=" + str(child["child_process"]["pid"]),
                "ENVIRONMENT_VARIABLES=3",
                "ENVIRONMENT_UNIQUE_VALUES=1",
                "KPSEWHICH_ROWS=3",
                "KPSEWHICH_READ_EXPAND_CHECKS=6",
                "KPSEWHICH_FAILURES=0",
                "TEXCACHE_ENTRY_COUNT=1",
                "PROBE_BYTES=42",
                "PROBE_SHA256=" + PROBE_SHA,
                "SOURCE_SHA256=" + SOURCE_SHA,
                "WRAPPER_SHA256=" + WRAPPER_SHA,
                "GIT_DIFF_FILE_COUNT=1",
                "GIT_NUMSTAT=1_INSERTION_1_DELETION",
                "GIT_DIFF_CHECK=PASS",
                "DIRECT_LUALATEX_STARTED=FALSE",
                "CURRENT_SLOT_OWNER=B-P05_R2",
                "ADS_PRESEAL_COUNT=0",
                f"STRUCTURED_PREMANIFEST_JSON_PARSE_COUNT={pre_json}",
                f"STRUCTURED_PREMANIFEST_CSV_PARSE_COUNT={pre_csv}",
                "RESULT=DIRECT_PREFLIGHT_PASS_AWAITING_BUILD_SLOT",
                "REQUEST=P654_R6_DIRECT_PREFLIGHT_READY_REQUEST_BUILD_SLOT",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rows = payload_rows()
    with (ROOT / "MANIFEST.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["RELATIVE_PATH", "BYTES", "MTIME_NS"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    (ROOT / "MANIFEST.json").write_text(
        json.dumps(
            {
                "package": "FIG-P654-01 STRICT_R6 SA2 direct-controller preflight",
                "payload_scope": "all ordinary files recursively except MANIFEST.csv, MANIFEST.json, and WRITE_STOPPED",
                "payload_file_count": len(manifest_rows),
                "files": manifest_rows,
                "result": "DIRECT_PREFLIGHT_PASS_AWAITING_BUILD_SLOT",
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
                "ROLE=SA2_ROOT_DIAGNOSTIC",
                "TYPESETTING_INVOCATIONS=0",
                "MANIFEST_PAYLOAD_MATCH=TRUE",
                f"PAYLOAD_FILE_COUNT={len(current)}",
                f"JSON_PARSE_COUNT={final_json}",
                f"CSV_PARSE_COUNT={final_csv}",
                "ADS_PRESEAL_COUNT=0",
                "RESULT=DIRECT_PREFLIGHT_PASS_AWAITING_BUILD_SLOT",
                "REQUEST=P654_R6_DIRECT_PREFLIGHT_READY_REQUEST_BUILD_SLOT",
                "NO_WRITES_PERMITTED_AFTER_THIS_MARKER=TRUE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"payload_file_count": len(current), "json_parse_count": final_json, "csv_parse_count": final_csv, "result": status_record["result"]}))


if __name__ == "__main__":
    main()

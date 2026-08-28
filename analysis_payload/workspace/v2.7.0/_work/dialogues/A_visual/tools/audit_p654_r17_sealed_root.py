from __future__ import annotations

import csv
import hashlib
import json
import stat
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825")
REPORT_JSON = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R17_ROOT_AUDIT.json")
REPORT_MD = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P654_R17_ROOT_AUDIT.md")
CONTROLS = {"MANIFEST.csv", "MANIFEST.json", "WRITE_STOPPED.json"}
POWERSHELL7 = Path(r"D:\PowerShell7\pwsh.exe")
EPOCH_TICKS = 621355968000000000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ticks(path: Path) -> int:
    return path.stat().st_mtime_ns // 100 + EPOCH_TICKS


def utc_7digit(value: int) -> str:
    unix_ticks = value - EPOCH_TICKS
    seconds, fraction = divmod(unix_ticks, 10_000_000)
    stamp = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:07d}Z"


def enumerate_files() -> list[Path]:
    return sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())


def snapshot(files: list[Path]) -> dict[str, tuple[int, str, int]]:
    return {p.relative_to(ROOT).as_posix(): (p.stat().st_size, sha256(p), ticks(p)) for p in files}


def ads_rows() -> list[dict[str, object]]:
    root_literal = str(ROOT).replace("'", "''")
    command = (
        f"$root='{root_literal}'; $rows=@(); "
        "Get-ChildItem -LiteralPath $root -Recurse -File | ForEach-Object { $f=$_.FullName; "
        "Get-Item -LiteralPath $f -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' } | "
        "ForEach-Object { $rows += [pscustomobject]@{path=$f;stream=$_.Stream;length=$_.Length} } }; "
        "$rows | ConvertTo-Json -Depth 4 -Compress"
    )
    run = subprocess.run([str(POWERSHELL7), "-NoProfile", "-Command", command], capture_output=True, text=True, encoding="utf-8")
    if run.returncode != 0:
        raise RuntimeError(run.stderr)
    if not run.stdout.strip():
        return []
    value = json.loads(run.stdout)
    return value if isinstance(value, list) else [value]


def main() -> None:
    files_before = enumerate_files()
    before = snapshot(files_before)
    rel_paths = set(before)
    if not CONTROLS <= rel_paths:
        raise RuntimeError("missing seal controls")
    payload_paths = sorted(rel_paths - CONTROLS)

    with (ROOT / "MANIFEST.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    json_rows = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    stopped = json.loads((ROOT / "WRITE_STOPPED.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

    if len(csv_rows) != len(json_rows) or len(csv_rows) != len(payload_paths):
        raise RuntimeError("manifest denominator mismatch")
    if len({r["relative_path"] for r in csv_rows}) != len(csv_rows):
        raise RuntimeError("duplicate manifest CSV path")
    if len({r["relative_path"] for r in json_rows}) != len(json_rows):
        raise RuntimeError("duplicate manifest JSON path")
    csv_map = {r["relative_path"]: r for r in csv_rows}
    json_map = {r["relative_path"]: r for r in json_rows}
    if set(csv_map) != set(json_map) or set(csv_map) != set(payload_paths):
        raise RuntimeError("manifest/FS path-set mismatch")

    field_mismatches = []
    fs_mismatches = []
    for rel in payload_paths:
        csv_row, json_row = csv_map[rel], json_map[rel]
        for field in ["relative_path", "bytes", "sha256", "mtime_utc_ticks", "mtime_utc_7digit"]:
            if str(csv_row[field]) != str(json_row[field]):
                field_mismatches.append({"path": rel, "field": field})
        size, digest, value_ticks = before[rel]
        expected = {
            "bytes": str(size),
            "sha256": digest,
            "mtime_utc_ticks": str(value_ticks),
            "mtime_utc_7digit": utc_7digit(value_ticks),
        }
        for field, value in expected.items():
            if str(csv_row[field]) != value:
                fs_mismatches.append({"path": rel, "field": field, "manifest": csv_row[field], "fs": value})
    if field_mismatches or fs_mismatches:
        raise RuntimeError(f"identity mismatch csv_json={len(field_mismatches)} fs={len(fs_mismatches)}")

    parse_failures = []
    for path in files_before:
        rel = path.relative_to(ROOT).as_posix()
        try:
            if path.suffix.lower() == ".json":
                json.loads(path.read_text(encoding="utf-8-sig"))
            elif path.suffix.lower() == ".csv":
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    list(csv.reader(handle))
            elif path.suffix.lower() == ".png":
                with Image.open(path) as image:
                    image.verify()
            elif path.suffix.lower() == ".pdf":
                document = fitz.open(path)
                if document.page_count < 1:
                    raise RuntimeError("zero pages")
                document.close()
        except Exception as exc:
            parse_failures.append({"path": rel, "error": repr(exc)})
    if parse_failures:
        raise RuntimeError(f"parse failures={len(parse_failures)}")

    ads = ads_rows()
    forbidden = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}]
    symlinks = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_symlink()]
    readonly_failures = [
        p.relative_to(ROOT).as_posix()
        for p in files_before
        if not (p.stat().st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
    ]
    write_ticks = ticks(ROOT / "WRITE_STOPPED.json")
    non_strict = [p.relative_to(ROOT).as_posix() for p in files_before if p.name != "WRITE_STOPPED.json" and ticks(p) >= write_ticks]

    payload_ext = Counter((Path(rel).suffix.lower() or "<none>") for rel in payload_paths)
    control_ext = Counter({".csv": 1, ".json": 2})
    ordinary_ext = Counter((p.suffix.lower() or "<none>") for p in files_before)
    extension_mismatch = {ext: {"ordinary": ordinary_ext[ext], "payload": payload_ext[ext], "control": control_ext[ext]} for ext in set(ordinary_ext) | set(payload_ext) | set(control_ext) if ordinary_ext[ext] != payload_ext[ext] + control_ext[ext]}

    hard_assertions = {
        "ordinary_equals_payload_plus_3": len(files_before) == len(payload_paths) + 3,
        "wstop_payload_count": stopped["payload_file_count"] == len(payload_paths),
        "wstop_control_count": stopped["control_file_count"] == 3,
        "wstop_ordinary_total": stopped["ordinary_file_total"] == len(files_before),
        "wstop_manifest_csv_identity": stopped["manifest_csv_sha256"] == sha256(ROOT / "MANIFEST.csv") and stopped["manifest_csv_bytes"] == (ROOT / "MANIFEST.csv").stat().st_size,
        "wstop_manifest_json_identity": stopped["manifest_json_sha256"] == sha256(ROOT / "MANIFEST.json") and stopped["manifest_json_bytes"] == (ROOT / "MANIFEST.json").stat().st_size,
        "extension_equations": not extension_mismatch,
        "ads_zero": not ads,
        "forbidden_zero": not forbidden,
        "symlink_zero": not symlinks,
        "all_files_readonly": not readonly_failures,
        "write_stopped_strictly_latest": not non_strict,
        "result_denominators": result["denominators"]["object"] == 114 and result["denominators"]["unordered_pair_actual"] == 6441 and result["denominators"]["critical_pair"] == 173,
        "result_route_is_fail": result["final_verdict"] == "FAIL_TO_SA2_SOURCE_R3_REQUIRED" and result["a_local_pass"] is False,
    }
    if not all(hard_assertions.values()):
        raise RuntimeError(f"hard assertion failed: {[k for k,v in hard_assertions.items() if not v]}")

    files_after = enumerate_files()
    after = snapshot(files_after)
    postseal_changes = sorted(set(before) ^ set(after)) + sorted(path for path in set(before) & set(after) if before[path] != after[path])
    if postseal_changes:
        raise RuntimeError(f"read-only audit changed root: {postseal_changes[:5]}")

    report = {
        "figure_uid": "FIG-P654-01",
        "round": "STRICT_R17_SA2_R16B_R102_DIRECT_BUILD_20260825",
        "root_decision": "ROOT_ACCEPT_R17_FAIL_TO_SA2_SOURCE_R3_REQUIRED",
        "sealed_root": str(ROOT),
        "ordinary_file_count": len(files_before),
        "payload_file_count": len(payload_paths),
        "control_file_count": 3,
        "extension_counts": {"payload": dict(sorted(payload_ext.items())), "control": dict(sorted(control_ext.items())), "ordinary": dict(sorted(ordinary_ext.items()))},
        "manifest_csv_rows": len(csv_rows),
        "manifest_json_rows": len(json_rows),
        "csv_json_field_mismatches": len(field_mismatches),
        "manifest_fs_mismatches": len(fs_mismatches),
        "parse_failures": len(parse_failures),
        "ads_nondefault_streams": len(ads),
        "forbidden_cache_or_bytecode": len(forbidden),
        "symlinks": len(symlinks),
        "readonly_failures": len(readonly_failures),
        "write_stopped_ticks": str(write_ticks),
        "non_strictly_earlier_files": len(non_strict),
        "postseal_changes_from_readonly_audit": len(postseal_changes),
        "hard_assertions": hard_assertions,
        "accepted_content_route": {
            "glyph_failures": ["G0040", "G0059", "G0064", "G0065"],
            "pair_failures": ["P06198", "P06219"],
            "source_role_ratio_failure": True,
            "status": "SA2_CONTINUE_NO_COMMIT_NO_FRESH_ROLE",
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(
        "# P654 R17 independent sealed-root audit\n\n"
        "Decision: **ROOT_ACCEPT_R17_FAIL_TO_SA2_SOURCE_R3_REQUIRED**.\n\n"
        f"The sealed root contains {len(payload_paths)} payload files + 3 controls = {len(files_before)} ordinary files. "
        "Both manifests match each other and the final filesystem in path, bytes, SHA-256, exact NTFS ticks, and 7-digit UTC display with zero differences. "
        "All JSON/CSV/PNG/PDF payloads parse; ADS, Python cache/bytecode, symlinks, and read-only failures are zero. "
        "WRITE_STOPPED is strictly latest and the read-only audit caused zero root writes.\n\n"
        "The evidence is accepted as a truthful FAIL route: G0040/G0059/G0064/G0065 fail the frozen D/E gate; P06198/P06219 fail 3px native clearance; the frozen source formula role also fails its source-size gate. "
        "P654 remains SA2; no commit, fresh SA1/SA3, LOCAL PASS, or A_LOCAL_PASS is authorized.\n",
        encoding="utf-8",
    )
    print(json.dumps({"decision": report["root_decision"], "payload": len(payload_paths), "ordinary": len(files_before), "manifest_fs_diff": 0, "postseal_changes": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

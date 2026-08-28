from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P637-01\sa1_r103_fresh_isolated_v1")
MANIFEST_NAME = "MANIFEST.json"
MARKER_NAME = "WRITE_STOPPED"
CONTROL_FILES = {"build_machine_evidence.py", "seal_recordset.py"}
EXTERNAL_INPUTS = [
    Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf"),
    Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_gibbs_axis_path.tex"),
    Path(r"D:\Users\ASUS\.codex\attachments\99aa1e8a-0c07-4cb3-a04c-e66d4f1f29f3\goal-objective.md"),
    Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\OVERLAP-RECHECK-20260823\STRICT-PIXEL-TYPOGRAPHY-PROTOCOL.md"),
    Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\audits\STRICT-GOAL-20260823\STRICT_FIGURE_EVIDENCE_SCHEMA.md"),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def timestamp_fields(path: Path) -> dict[str, object]:
    stat = path.stat()
    seconds, remainder_ns = divmod(stat.st_mtime_ns, 1_000_000_000)
    base = datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "mtime_utc_ns": f"{base}.{remainder_ns:09d}Z",
        "mtime_unix_ns": stat.st_mtime_ns,
        "windows_filetime_100ns": stat.st_mtime_ns // 100 + 116444736000000000,
        "mtime_remainder_below_100ns": stat.st_mtime_ns % 100,
    }


def file_record(path: Path, relative_path: str | None = None, record_class: str | None = None) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    record: dict[str, object] = {
        "resolved_path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }
    if relative_path is not None:
        record["relative_path"] = relative_path
    if record_class is not None:
        record["record_class"] = record_class
    record.update(timestamp_fields(resolved))
    return record


def main() -> None:
    root = ROOT.resolve(strict=True)
    files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in {MANIFEST_NAME, MARKER_NAME}:
            continue
        record_class = "control" if relative in CONTROL_FILES else "payload"
        files.append(file_record(path, relative, record_class))

    canonical_entries = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    recordset_sha256 = hashlib.sha256(canonical_entries).hexdigest().upper()
    payload_count = sum(item["record_class"] == "payload" for item in files)
    control_count = sum(item["record_class"] == "control" for item in files)
    external = [file_record(path) for path in EXTERNAL_INPUTS]

    manifest = {
        "schema": "FIGURE_EVIDENCE_CLOSED_MANIFEST_V1",
        "handoff_id": "C-FIG-P637-01-R103-SA1-FRESH-ISOLATED-V1",
        "figure_uid": "FIG-P637-01",
        "root_resolved_path": str(root),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "closure_model": {
            "payload": "Every evidence-root file except the two control scripts, MANIFEST.json, and WRITE_STOPPED.",
            "control": "build_machine_evidence.py and seal_recordset.py; both are hashed entries.",
            "seal": "MANIFEST.json; self-excluded because hashing it inside itself cannot close. Its final hash is recorded in WRITE_STOPPED and reported externally.",
            "self": "WRITE_STOPPED; created strictly after manifest completion and read-only conversion, and excluded from this entry set.",
            "manifest_entry_included": False,
            "write_stopped_entry_included": False,
        },
        "entry_counts": {
            "payload": payload_count,
            "control": control_count,
            "manifested_total": len(files),
            "seal": 1,
            "self_marker": 1,
        },
        "recordset_digest": {
            "algorithm": "SHA-256",
            "canonicalization": "UTF-8 canonical JSON of the sorted files array; ensure_ascii=false; sort_keys=true; separators=(',', ':').",
            "sha256": recordset_sha256,
        },
        "external_whitelisted_inputs": external,
        "files": files,
    }

    output = root / MANIFEST_NAME
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest_path": str(output),
        "manifested_total": len(files),
        "payload": payload_count,
        "control": control_count,
        "recordset_sha256": recordset_sha256,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

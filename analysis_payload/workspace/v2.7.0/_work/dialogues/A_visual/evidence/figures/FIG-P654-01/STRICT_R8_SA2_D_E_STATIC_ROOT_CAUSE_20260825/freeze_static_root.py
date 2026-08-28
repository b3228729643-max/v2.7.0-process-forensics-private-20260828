from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_dependency_graph.tex")
EXPECTED_SOURCE_SHA = "EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D"
EXCLUDED = {"STATIC_PAYLOAD_MANIFEST.json", "STATIC_FREEZE.json", "WRITE_STOPPED"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


summary = json.loads((ROOT / "STATIC_RECOMPUTE_SUMMARY.json").read_text(encoding="utf-8-sig"))
assert summary["element_count"] == 95
assert summary["unique_element_count"] == 95
assert summary["mapped_exactly_once"] is True
assert summary["taxonomy_failure_count"] == 0
assert summary["legacy_frozen_group_failure_count"] == 8
assert summary["source_same_role_failure_count"] == 0
assert summary["source_hierarchy_failure_count"] == 0
assert summary["conclusion"] == "TAXONOMY_STATIC_PASS_SOURCE_UNCHANGED"
assert sha256(SOURCE) == EXPECTED_SOURCE_SHA

json_errors: list[str] = []
csv_errors: list[str] = []
for path in sorted(ROOT.glob("*.json")):
    if path.name in EXCLUDED:
        continue
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        json_errors.append(f"{path.name}: {exc!r}")
for path in sorted(ROOT.glob("*.csv")):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        if not rows or not rows[0]:
            raise ValueError("missing header")
        width = len(rows[0])
        if any(len(row) != width for row in rows[1:]):
            raise ValueError("row width mismatch")
    except Exception as exc:
        csv_errors.append(f"{path.name}: {exc!r}")
assert not json_errors and not csv_errors

cache_artifacts = [
    path.relative_to(ROOT).as_posix()
    for path in ROOT.rglob("*")
    if path.name == "__pycache__" or path.suffix == ".pyc"
]
assert not cache_artifacts

entries: list[dict[str, object]] = []
for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
    rel = path.relative_to(ROOT).as_posix()
    if rel in EXCLUDED:
        continue
    stat = path.stat()
    entries.append(
        {
            "relative_path": rel,
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256(path),
        }
    )

manifest = {
    "generated_at_utc": now(),
    "payload_file_count": len(entries),
    "entries": entries,
}
write_json(ROOT / "STATIC_PAYLOAD_MANIFEST.json", manifest)

freeze = {
    "status": "P654_TAXONOMY_STATIC_FREEZE_READY_REQUEST_BUILD_SLOT",
    "frozen_at_utc": now(),
    "source_path": str(SOURCE),
    "source_bytes": SOURCE.stat().st_size,
    "source_sha256": sha256(SOURCE),
    "source_changed_during_r8": False,
    "taxonomy_policy_sha256": sha256(ROOT / "TAXONOMY_POLICY.json"),
    "mapping_ledger_sha256": sha256(ROOT / "TYPOGRAPHIC_TAXONOMY_ELEMENT_LEDGER.csv"),
    "report_sha256": sha256(ROOT / "STATIC_ROOT_CAUSE_AND_OPTIONS.md"),
    "generator_sha256": sha256(ROOT / "build_static_taxonomy.py"),
    "manifest_sha256": sha256(ROOT / "STATIC_PAYLOAD_MANIFEST.json"),
    "element_count": 95,
    "group_count": 10,
    "taxonomy_failures": 0,
    "legacy_failures_reproduced": 8,
    "tex_run_by_r8": False,
    "tex_slot_owner_at_freeze": "B-P06-R2",
    "tex_authorized_for_a": False,
    "commit_created": False,
}
write_json(ROOT / "STATIC_FREEZE.json", freeze)

stop = {
    "status": "WRITE_STOPPED",
    "written_at_utc": now(),
    "static_freeze_sha256": sha256(ROOT / "STATIC_FREEZE.json"),
    "static_payload_manifest_sha256": sha256(ROOT / "STATIC_PAYLOAD_MANIFEST.json"),
    "instruction": "R8 static root is immutable. No further writes are permitted.",
}
write_json(ROOT / "WRITE_STOPPED", stop)

print(
    json.dumps(
        {
            "status": freeze["status"],
            "payload_files": len(entries),
            "source_sha256": freeze["source_sha256"],
            "write_stopped": True,
        },
        ensure_ascii=False,
    )
)

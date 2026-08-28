from __future__ import annotations

import csv
import ctypes
import hashlib
import itertools
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P632-01\sa3_r110_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.json"
WSTOP = ROOT / "WRITE_STOPPED"
EXCLUDED = {"MANIFEST.json", "WRITE_STOPPED"}
FILE_ATTRIBUTE_READONLY = 0x1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def set_readonly(path: Path) -> None:
    kernel32 = ctypes.windll.kernel32
    attrs = kernel32.GetFileAttributesW(str(path))
    if attrs == 0xFFFFFFFF:
        raise OSError(f"GetFileAttributesW failed: {path}")
    if not kernel32.SetFileAttributesW(str(path), attrs | FILE_ATTRIBUTE_READONLY):
        raise OSError(f"SetFileAttributesW failed: {path}")


def parse_and_validate() -> dict:
    json_paths = sorted(p for p in ROOT.rglob("*.json") if p.name != MANIFEST.name)
    for path in json_paths:
        json.loads(path.read_text(encoding="utf-8-sig"))

    csv_paths = sorted(ROOT.rglob("*.csv"))
    tables = {}
    for path in csv_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            tables[path.name] = list(csv.DictReader(stream))

    required_counts = {
        "objects_machine.csv": 14,
        "pairs_machine.csv": 91,
        "object_adjudication_manual.csv": 14,
        "pair_adjudication_manual.csv": 91,
        "text_spans_machine.csv": 151,
        "glyphs_machine.csv": 413,
        "text_glyph_adjudication_manual.csv": 22,
        "roi_adjudication_manual.csv": 6,
        "view_adjudication_manual.csv": 7,
        "hard_gate_adjudication_manual.csv": 12,
    }
    for name, expected in required_counts.items():
        actual = len(tables[name])
        if actual != expected:
            raise RuntimeError(f"row-count mismatch {name}: {actual} != {expected}")

    objects = [row["object_id"] for row in tables["objects_machine.csv"]]
    expected_pairs = set(itertools.combinations(objects, 2))
    manual_pairs = {(row["object_a"], row["object_b"]) for row in tables["pair_adjudication_manual.csv"]}
    if manual_pairs != expected_pairs:
        raise RuntimeError("manual pair set is not the complete unordered denominator")
    if len({row["pair_id"] for row in tables["pair_adjudication_manual.csv"]}) != 91:
        raise RuntimeError("manual pair ids are not unique")

    manual_files = [
        "object_adjudication_manual.csv",
        "pair_adjudication_manual.csv",
        "text_glyph_adjudication_manual.csv",
        "roi_adjudication_manual.csv",
        "view_adjudication_manual.csv",
        "hard_gate_adjudication_manual.csv",
    ]
    for name in manual_files:
        for row in tables[name]:
            if row.get("manual_decision") != "PASS":
                raise RuntimeError(f"non-PASS manual row in {name}")

    if WSTOP.exists():
        raise RuntimeError("WRITE_STOPPED already exists; refusing a second seal")
    if MANIFEST.exists():
        raise RuntimeError("MANIFEST already exists; refusing to overwrite")

    reparse = [p for p in ROOT.rglob("*") if p.is_symlink()]
    cache = [p for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() == ".pyc" or p.name == ".cache"]
    if reparse or cache:
        raise RuntimeError("reparse/cache/pyc object present")

    return {
        "json_parsed_before_manifest": len(json_paths),
        "csv_parsed": len(csv_paths),
        "reparse_point_count": 0,
        "cache_or_pyc_count": 0,
        "manual_fail_count": 0,
        "unordered_pair_coverage": 91,
    }


def main() -> None:
    validation = parse_and_validate()
    entries = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name not in EXCLUDED):
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(ROOT.resolve(strict=True))
        except ValueError as exc:
            raise RuntimeError(f"path escapes root: {path}") from exc
        entries.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    manifest_payload = {
        "schema": "SA3_ISOLATED_EVIDENCE_MANIFEST_V1",
        "uid": "FIG-P632-01",
        "handoff_id": "C-FIG-P632-01-R110-SA3-FRESH-ISOLATED-V1",
        "outcome": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "evidence_root": str(ROOT),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(entries),
        "entry_total_bytes": sum(item["bytes"] for item in entries),
        "excluded_from_entries": [
            {"path": "MANIFEST.json", "reason": "manifest self-hash exclusion"},
            {"path": "WRITE_STOPPED", "reason": "last-write seal marker exclusion"}
        ],
        "validation_before_marker": validation,
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    parsed_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if parsed_manifest["entry_count"] != len(entries):
        raise RuntimeError("manifest entry-count self-check failed")
    for item in parsed_manifest["entries"]:
        path = ROOT / Path(item["path"])
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"manifest path/bytes/SHA mismatch: {item['path']}")

    for path in sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        set_readonly(path)
    set_readonly(ROOT)

    time.sleep(1.25)
    seal_time = datetime.now(timezone.utc).isoformat()
    marker = (
        "WRITE_STOPPED\n"
        "uid=FIG-P632-01\n"
        "handoff_id=C-FIG-P632-01-R110-SA3-FRESH-ISOLATED-V1\n"
        "outcome=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE\n"
        f"manifest_sha256={sha256(MANIFEST)}\n"
        f"seal_utc={seal_time}\n"
    )
    with WSTOP.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(marker)
    set_readonly(WSTOP)
    set_readonly(ROOT)

    print(f"SEALED_ROOT={ROOT}")
    print(f"MANIFEST_BYTES={MANIFEST.stat().st_size}")
    print(f"MANIFEST_SHA256={sha256(MANIFEST)}")
    print(f"WSTOP_BYTES={WSTOP.stat().st_size}")
    print(f"WSTOP_SHA256={sha256(WSTOP)}")


if __name__ == "__main__":
    main()

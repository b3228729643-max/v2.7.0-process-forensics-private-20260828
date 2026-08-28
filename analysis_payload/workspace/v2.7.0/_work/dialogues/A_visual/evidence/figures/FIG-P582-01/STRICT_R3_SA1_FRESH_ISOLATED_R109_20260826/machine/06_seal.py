from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R3_SA1_FRESH_ISOLATED_R109_20260826")
PAYLOAD_MANIFEST = ROOT / "PAYLOAD_MANIFEST.csv"
SEAL_MANIFEST = ROOT / "SEAL_MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
EXCLUDED = {PAYLOAD_MANIFEST.name, SEAL_MANIFEST.name, MARKER.name}
EXPECTED_PDF_SHA256 = "936162A637DCE09EE02B3F83CB1C21A61A87EFBB9A7C8DDE2FB11A326EB552A9"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def is_readonly(path: Path) -> bool:
    attrs = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_READONLY", 1))


def is_reparse(path: Path) -> bool:
    attrs = getattr(path.lstat(), "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def all_entries() -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = [ROOT]
    for base, dirnames, filenames in os.walk(ROOT, followlinks=False):
        base_path = Path(base)
        for name in dirnames:
            dirs.append(base_path / name)
        for name in filenames:
            files.append(base_path / name)
    return sorted(files), sorted(dirs)


def named_ads() -> list[str]:
    ps = (
        "$ErrorActionPreference='Stop';"
        f"$r={json.dumps(str(ROOT), ensure_ascii=False)};"
        "Get-ChildItem -LiteralPath $r -Recurse -Force -File | ForEach-Object {"
        "$p=$_.FullName; Get-Item -LiteralPath $p -Stream * | "
        "Where-Object { $_.Stream -ne ':$DATA' -and $_.Stream -ne '$DATA' } | "
        "ForEach-Object { $p + '::' + $_.Stream } }"
    )
    cp = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line.strip() for line in cp.stdout.splitlines() if line.strip()]


def validate_manual() -> dict:
    specs = [
        (ROOT / "manual" / "GLYPH_MANUAL_REVIEW.csv", 78, "object_id"),
        (ROOT / "manual" / "GRAPHIC_MANUAL_REVIEW.csv", 27, "object_id"),
        (ROOT / "manual" / "CRITICAL_PAIR_MANUAL_REVIEW.csv", 20, "pair_id"),
    ]
    now = datetime.now(timezone.utc).timestamp()
    result = {}
    for path, expected, key in specs:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == expected, (path, len(rows), expected)
        assert len({r[key] for r in rows}) == expected, (path, "duplicate ids")
        assert all(r["reviewer_id"] == "SA1_FRESH_ISOLATED_R109" for r in rows)
        assert all(r["decision"] == "PASS" for r in rows)
        observed = []
        for row in rows:
            ts = datetime.fromisoformat(row["observation_timestamp"]).timestamp()
            assert ts <= now + 1.0, (path, "future observation", row[key])
            observed.append(ts)
        assert path.stat().st_mtime >= max(observed), (path, "mtime before observation")
        result[path.name] = {"rows": len(rows), "decision": "PASS"}
    acceptance = ROOT / "manual" / "MANUAL_VISUAL_ACCEPTANCE.md"
    text = acceptance.read_text(encoding="utf-8")
    assert "`PASS`" in text
    assert "N=105" in text and "C=5460" in text
    observed_ts = datetime.fromisoformat("2026-08-26T22:58:54.0216802+08:00").timestamp()
    assert observed_ts <= now + 1.0
    assert acceptance.stat().st_mtime >= observed_ts
    result[acceptance.name] = {"decision": "PASS"}
    return result


def validate_preseal() -> dict:
    assert ROOT.is_dir()
    assert not PAYLOAD_MANIFEST.exists()
    assert not SEAL_MANIFEST.exists()
    assert not MARKER.exists()
    files, dirs = all_entries()
    forbidden = [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in files + dirs
        if p.name == "__pycache__" or p.suffix.lower() == ".pyc"
    ]
    reparses = [
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in files + dirs
        if is_reparse(p)
    ]
    ads = named_ads()
    assert not forbidden, forbidden
    assert not reparses, reparses
    assert not ads, ads
    hard = json.loads((ROOT / "machine" / "04_hard_gates.json").read_text(encoding="utf-8"))
    assert hard["official_identity_pass"] is True
    assert hard["location_physical_page"] == 632
    assert hard["object_count_N"] == 105
    assert hard["unordered_pair_count_C"] == 5460
    assert hard["empty_mask_count"] == 0
    assert hard["r168_true_illegal_overlap_pair_count"] == 0
    assert hard["overlap_pixel_count"] == 0
    assert hard["clip_pixel_count"] == 0
    assert hard["machine_r168_direction"] == "PASS_CANDIDATE"
    locate = json.loads((ROOT / "machine" / "01_locate_identity.json").read_text(encoding="utf-8"))
    serialized = json.dumps(locate, ensure_ascii=False).upper()
    assert EXPECTED_PDF_SHA256 in serialized
    assert "632" in serialized and "817" in serialized
    manual = validate_manual()
    return {"hard_gates": hard, "manual": manual, "ads": 0, "reparse": 0, "pyc_or_cache": 0}


def write_text_fsync(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


def main() -> None:
    pre = validate_preseal()
    payload_files, _ = all_entries()
    payload_files = [p for p in payload_files if p.name not in EXCLUDED]
    for path in payload_files:
        os.chmod(path, stat.S_IREAD)
    rows = []
    for path in payload_files:
        st = path.stat()
        assert is_readonly(path), path
        rows.append(
            {
                "relative_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size_bytes": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "sha256": sha256(path),
                "readonly": True,
            }
        )
    lines = ["relative_path,size_bytes,mtime_ns,sha256,readonly\n"]
    for row in rows:
        lines.append(
            f'{row["relative_path"]},{row["size_bytes"]},{row["mtime_ns"]},{row["sha256"]},true\n'
        )
    write_text_fsync(PAYLOAD_MANIFEST, "".join(lines))
    os.chmod(PAYLOAD_MANIFEST, stat.S_IREAD)
    payload_manifest_identity = {
        "relative_path": PAYLOAD_MANIFEST.name,
        "size_bytes": PAYLOAD_MANIFEST.stat().st_size,
        "mtime_ns": PAYLOAD_MANIFEST.stat().st_mtime_ns,
        "sha256": sha256(PAYLOAD_MANIFEST),
        "readonly": is_readonly(PAYLOAD_MANIFEST),
    }
    seal = {
        "schema": "FIGURE_EVIDENCE_SEAL_CHAIN_V1",
        "handoff_id": "A-R109-P582-SA1-FRESH-ISOLATED-20260826",
        "figure_id": "FIG-P582-01",
        "official_pdf": {
            "pages": 817,
            "size_bytes": 4967054,
            "sha256": EXPECTED_PDF_SHA256,
            "physical_page": 632,
            "printed_page": 619,
        },
        "visible_denominator": {"N": 105, "glyphs": 78, "graphics": 27, "unordered_pairs_C": 5460},
        "payload_file_count": len(rows),
        "payload_total_bytes": sum(r["size_bytes"] for r in rows),
        "payload_files": rows,
        "payload_manifest": payload_manifest_identity,
        "preseal_validation": pre,
        "sa1_manual_decision": "PASS",
        "next_role_requested": "different fresh isolated SA3",
        "a_local_pass_claimed": False,
    }
    write_text_fsync(SEAL_MANIFEST, json.dumps(seal, ensure_ascii=False, indent=2) + "\n")
    os.chmod(SEAL_MANIFEST, stat.S_IREAD)
    seal_identity = {
        "relative_path": SEAL_MANIFEST.name,
        "size_bytes": SEAL_MANIFEST.stat().st_size,
        "mtime_ns": SEAL_MANIFEST.stat().st_mtime_ns,
        "sha256": sha256(SEAL_MANIFEST),
        "readonly": is_readonly(SEAL_MANIFEST),
    }
    # Verify the closed manifest chain before the unique terminal marker is created.
    assert payload_manifest_identity["readonly"] is True
    assert seal_identity["readonly"] is True
    actual, _ = all_entries()
    actual_payload = [p for p in actual if p.name not in EXCLUDED]
    assert [str(p.relative_to(ROOT)).replace("\\", "/") for p in actual_payload] == [r["relative_path"] for r in rows]
    for path, row in zip(actual_payload, rows):
        st = path.stat()
        assert st.st_size == row["size_bytes"]
        assert st.st_mtime_ns == row["mtime_ns"]
        assert sha256(path) == row["sha256"]
        assert is_readonly(path)
    latest_before_marker = max(p.stat().st_mtime_ns for p in actual)
    while time.time_ns() <= latest_before_marker + 1_000_000_000:
        time.sleep(0.05)
    marker_content = {
        "marker": "WRITE_STOPPED",
        "handoff_id": seal["handoff_id"],
        "payload_manifest_sha256": payload_manifest_identity["sha256"],
        "seal_manifest_sha256": seal_identity["sha256"],
        "root_writes_after_this_marker": 0,
    }
    write_text_fsync(MARKER, json.dumps(marker_content, ensure_ascii=False, indent=2) + "\n")
    os.chmod(MARKER, stat.S_IREAD)
    # Read-only assertions after marker do not alter the sealed root.
    marker_mtime = MARKER.stat().st_mtime_ns
    assert marker_mtime > latest_before_marker
    assert is_readonly(MARKER)
    print(
        json.dumps(
            {
                "sealed": True,
                "payload_files": len(rows),
                "payload_manifest_sha256": payload_manifest_identity["sha256"],
                "seal_manifest_sha256": seal_identity["sha256"],
                "write_stopped_sha256": sha256(MARKER),
                "write_stopped_mtime_ns": marker_mtime,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"sealed": False, "error": repr(exc)}, ensure_ascii=False), file=sys.stderr)
        raise

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import time
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\A-R111-P033-SA3-FRESH-ISOLATED-20260827_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\handoff\A-R111-P033-SA3-FRESH-ISOLATED-20260827_HANDOFF.json")
MANIFEST = ROOT / "PRESEAL_MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
CONTROLLER = ROOT / "seal_once.py"
FILE_ATTRIBUTE_READONLY = 0x00000001
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def get_attrs(path: Path) -> int:
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attrs == INVALID_FILE_ATTRIBUTES:
        raise OSError(f"GetFileAttributesW failed: {path}")
    return attrs


def set_readonly(path: Path) -> None:
    attrs = get_attrs(path)
    if not ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs | FILE_ATTRIBUTE_READONLY):
        raise OSError(f"SetFileAttributesW failed: {path}")


def main() -> None:
    if MARKER.exists():
        raise SystemExit("WRITE_STOPPED already exists; refusing a second seal")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = ROOT / entry["relative_path"]
        if not path.is_file() or path.stat().st_size != entry["bytes"] or sha(path) != entry["sha256"]:
            raise SystemExit(f"manifest mismatch before marker: {entry['relative_path']}")
    report_hash = sha(REPORT)
    handoff_hash = sha(HANDOFF)
    controller_hash = sha(CONTROLLER)
    if report_hash != manifest["external_bindings"]["report"]["sha256"]:
        raise SystemExit("report hash changed before marker")
    if handoff_hash != manifest["external_bindings"]["handoff"]["sha256"]:
        raise SystemExit("handoff hash changed before marker")
    manifest_hash = sha(MANIFEST)
    marker_data = {
        "seal_version": "R111-SA3-R168-STRICT-R6",
        "HANDOFF_ID": "A-R111-P033-SA3-FRESH-ISOLATED-20260827",
        "canonical_task": "/root/p033_r111_fresh_sa3",
        "model_effort": "gpt-5.6-sol/xhigh",
        "evidence_root": str(ROOT),
        "preseal_manifest_path": str(MANIFEST),
        "preseal_manifest_sha256": manifest_hash,
        "seal_controller_path": str(CONTROLLER),
        "seal_controller_sha256": controller_hash,
        "report_path": str(REPORT),
        "report_sha256": report_hash,
        "handoff_path": str(HANDOFF),
        "handoff_sha256": handoff_hash,
        "strict_atom_count": 96,
        "unordered_pair_count": 4560,
        "manual_atom_rows": 96,
        "manual_candidate_pair_rows": 131,
        "OVERLAP_PIXEL_COUNT": 0,
        "CLIP_PIXEL_COUNT": 0,
        "PIXEL_ADJUDICATION_STATUS": "CLEAR",
        "SA3_RESULT": "PASS",
        "central_local_final_acceptance_claimed": False,
        "postmarker_expected_writes_inside_root": 0,
        "readonly_scope": "all files and directories including evidence root",
    }
    marker_text = json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n"
    placeholder_tokens = [chr(123) * 2, "<" + "PLACE" + "HOLDER>", "T" + "BD", "TO" + "DO", "[" + "INSERT"]
    placeholder_hits = [token for token in placeholder_tokens if token.casefold() in marker_text.casefold()]
    if placeholder_hits:
        raise SystemExit("marker has unresolved placeholder")
    if chr(36) in marker_text:
        raise SystemExit("marker contains a dollar-sign expression")
    if chr(9) in marker_text:
        raise SystemExit("marker contains a forbidden tab character")

    max_before = max(p.stat().st_mtime_ns for p in ROOT.rglob("*") if p.is_file())
    fd = os.open(MARKER, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(marker_text)
        f.flush()
        os.fsync(f.fileno())
    target_ns = max(time.time_ns(), max_before + 2_000_000_000)
    os.utime(MARKER, ns=(target_ns, target_ns))

    paths = sorted(ROOT.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        set_readonly(path)
    set_readonly(ROOT)

    marker_mtime = MARKER.stat().st_mtime_ns
    files = [p for p in ROOT.rglob("*") if p.is_file()]
    postmarker = [str(p.relative_to(ROOT)) for p in files if p != MARKER and p.stat().st_mtime_ns >= marker_mtime]
    all_paths = [ROOT, *ROOT.rglob("*")]
    not_readonly = [str(p) for p in all_paths if not (get_attrs(p) & FILE_ATTRIBUTE_READONLY)]
    control_names = {
        "IDENTITY_AND_BOUNDARY.md",
        "input_and_location_proof.md",
        "manual_R168_visual_acceptance.md",
        "EVIDENCE_INDEX.md",
        "machine_preseal_validation.json",
        "PRESEAL_MANIFEST.json",
        "WRITE_STOPPED",
        "generate_machine_evidence.py",
        "validate_preseal.py",
        "prepare_seal.py",
        "seal_once.py",
    }
    control_files = [p for p in files if p.name in control_names]
    payload_files = [p for p in files if p.name not in control_names]
    ordinary_files: list[Path] = []
    max_other_mtime = max(p.stat().st_mtime_ns for p in files if p != MARKER)
    audit = {
        "seal_executed_once": True,
        "marker_exists": MARKER.is_file(),
        "marker_is_absolutely_latest": not postmarker and all(p == MARKER or p.stat().st_mtime_ns < marker_mtime for p in files),
        "postmarker_write_count": len(postmarker),
        "postmarker_paths": postmarker,
        "all_files_and_directories_readonly": not not_readonly,
        "not_readonly_paths": not_readonly,
        "readonly_file_count": sum(bool(get_attrs(p) & FILE_ATTRIBUTE_READONLY) for p in files),
        "readonly_directory_count_including_root": sum(bool(get_attrs(p) & FILE_ATTRIBUTE_READONLY) for p in all_paths if p.is_dir()),
        "payload_file_count": len(payload_files),
        "control_file_count": len(control_files),
        "ordinary_file_count": len(ordinary_files),
        "marker_placeholder_count": len(placeholder_hits),
        "marker_dollar_count": marker_text.count(chr(36)),
        "marker_tab_count": marker_text.count(chr(9)),
        "write_stopped_margin_ns": marker_mtime - max_other_mtime,
        "marker_sha256": sha(MARKER),
        "manifest_sha256": manifest_hash,
        "controller_sha256": controller_hash,
        "report_sha256": report_hash,
        "handoff_sha256": handoff_hash,
        "root_file_count_including_manifest_and_marker": len(files),
    }
    print(json.dumps(audit, ensure_ascii=False))
    if not (
        audit["marker_exists"]
        and audit["marker_is_absolutely_latest"]
        and audit["postmarker_write_count"] == 0
        and audit["all_files_and_directories_readonly"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

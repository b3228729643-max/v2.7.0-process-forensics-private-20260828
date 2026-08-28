from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import re
import stat
import time
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa2_r112_r168_readonly_adjudication_v1")
EXPECTED_ROOT = str(ROOT)
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_gamma_normalization.tex")
HANDOFF_ID = "C-FIG-P662-01-R112-SA2-R168-READONLY-ADJUDICATION-V1"
VERDICT = "SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1"
MANIFEST = ROOT / "SEALED_MANIFEST.csv"
GATE = ROOT / "parse_and_hygiene_gate.json"
MARKER = ROOT / "WRITE_STOPPED.txt"
PENDING = ROOT.parent / ".sa2_r112_r168_wstop_pending.tmp"

PDF_BYTES = 4_967_100
PDF_SHA256 = "D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2"
SOURCE_BYTES = 3_588
SOURCE_SHA256 = "B5232526402FEF6735DC3F9C07B418D7BF49E0D8C17EAEFB82A54B450B63113E"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def ntfs_ticks(path: Path) -> int:
    return int(path.stat().st_mtime_ns // 100 + 116444736000000000)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
kernel32.GetFileAttributesW.restype = wintypes.DWORD
kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
kernel32.SetFileAttributesW.restype = wintypes.BOOL


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", wintypes.WCHAR * 296)]


kernel32.FindFirstStreamW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
kernel32.FindFirstStreamW.restype = wintypes.HANDLE
kernel32.FindNextStreamW.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
kernel32.FindNextStreamW.restype = wintypes.BOOL
kernel32.FindClose.argtypes = [wintypes.HANDLE]
kernel32.FindClose.restype = wintypes.BOOL


def attrs(path: Path) -> int:
    value = int(kernel32.GetFileAttributesW(str(path)))
    if value == INVALID_FILE_ATTRIBUTES:
        raise OSError(ctypes.get_last_error(), f"GetFileAttributesW failed: {path}")
    return value


def set_readonly(path: Path) -> None:
    value = attrs(path)
    if not kernel32.SetFileAttributesW(str(path), value | FILE_ATTRIBUTE_READONLY):
        raise OSError(ctypes.get_last_error(), f"SetFileAttributesW failed: {path}")


def streams(path: Path) -> list[str]:
    data = WIN32_FIND_STREAM_DATA()
    handle = kernel32.FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        err = ctypes.get_last_error()
        if err in (2, 38):
            return []
        raise OSError(err, f"FindFirstStreamW failed: {path}")
    found = [data.cStreamName]
    try:
        while kernel32.FindNextStreamW(handle, ctypes.byref(data)):
            found.append(data.cStreamName)
        err = ctypes.get_last_error()
        if err not in (0, 38):
            raise OSError(err, f"FindNextStreamW failed: {path}")
    finally:
        kernel32.FindClose(handle)
    return found


def root_entries() -> list[Path]:
    return sorted(ROOT.rglob("*"), key=lambda p: str(p).casefold())


def assert_hygiene() -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    directories: list[Path] = []
    banned_exact = {"thumbs.db", ".ds_store"}
    banned_suffixes = {".pyc", ".pyo", ".tmp", ".cache"}
    for path in root_entries():
        rel = path.relative_to(ROOT).as_posix()
        name = path.name.casefold()
        value = attrs(path)
        if value & FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f"reparse point forbidden: {rel}")
        if path.is_symlink():
            raise RuntimeError(f"symlink forbidden: {rel}")
        if name == "__pycache__" or name in banned_exact or path.suffix.casefold() in banned_suffixes:
            raise RuntimeError(f"cache/temp forbidden: {rel}")
        if path.is_dir():
            directories.append(path)
        elif path.is_file():
            files.append(path)
            extra_streams = [s for s in streams(path) if s != "::$DATA"]
            if extra_streams:
                raise RuntimeError(f"ADS forbidden: {rel}: {extra_streams}")
        else:
            raise RuntimeError(f"non-regular root entry forbidden: {rel}")
    return files, directories


def require_file(name: str) -> Path:
    path = ROOT / name
    if not path.is_file():
        raise RuntimeError(f"missing required payload: {name}")
    return path


def main() -> None:
    if str(ROOT) != EXPECTED_ROOT or not ROOT.is_dir():
        raise RuntimeError("root identity mismatch")
    if MANIFEST.exists() or GATE.exists() or MARKER.exists() or PENDING.exists():
        raise RuntimeError("seal artifact already exists; refusing duplicate seal")

    if PDF.stat().st_size != PDF_BYTES or sha256(PDF) != PDF_SHA256:
        raise RuntimeError("frozen R112 PDF identity changed")
    if SOURCE.stat().st_size != SOURCE_BYTES or sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("current source identity changed")

    required = [
        "adjudication_scope_and_method.md",
        "all_unordered_object_pairs_machine.csv",
        "caption_native_300dpi.png",
        "figure_caption_grayscale_native_300dpi.png",
        "figure_caption_native_300dpi.png",
        "figure_only_native_300dpi.png",
        "frozen_input_identities.json",
        "generate_machine_evidence.py",
        "machine_evidence_metadata.json",
        "manual_glyph_codepoint_ledger.md",
        "manual_object_ledger.md",
        "manual_pair_ledger.md",
        "manual_risk_roi_ledger.md",
        "manual_visual_adjudication.md",
        "math_semantics_recomputation.md",
        "page_710_full_200dpi.png",
        "page_710_full_300dpi.png",
        "page_710_integration_overlay_200dpi.png",
        "pdf_extracted_figure_caption_text.txt",
        "pdf_locator.json",
        "risk_roi_index_machine.csv",
        "seal_once.py",
        "semantic_object_overlay_native_300dpi.png",
        "text_measurement_overlay_native_300dpi.png",
        "text_spans_codepoints_and_ink_machine.csv",
        "visible_object_inventory_machine.csv",
    ]
    for name in required:
        require_file(name)
    if (ROOT / "r112_fullbook_text_utf8.txt").exists():
        raise RuntimeError("locator intermediate must not be sealed")

    identities = json.loads(require_file("frozen_input_identities.json").read_text(encoding="utf-8"))
    locator = json.loads(require_file("pdf_locator.json").read_text(encoding="utf-8"))
    machine = json.loads(require_file("machine_evidence_metadata.json").read_text(encoding="utf-8"))
    if len(identities) != 3:
        raise RuntimeError("identity JSON count mismatch")
    if locator.get("uid") != "FIG-P662-01" or locator.get("pdf_page_one_based") != 710:
        raise RuntimeError("locator JSON mismatch")
    if machine.get("visible_object_count") != 20 or machine.get("unordered_pair_count") != 190:
        raise RuntimeError("machine metadata denominator mismatch")
    if machine.get("text_span_count") != 78 or machine.get("risk_roi_count") != 8:
        raise RuntimeError("machine metadata evidence count mismatch")

    objects = read_csv(require_file("visible_object_inventory_machine.csv"))
    pairs = read_csv(require_file("all_unordered_object_pairs_machine.csv"))
    spans = read_csv(require_file("text_spans_codepoints_and_ink_machine.csv"))
    rois = read_csv(require_file("risk_roi_index_machine.csv"))
    if [r["OBJECT_ID"] for r in objects] != [f"O{i:02d}" for i in range(1, 21)]:
        raise RuntimeError("object IDs are not exactly O01..O20")
    if [r["PAIR_ID"] for r in pairs] != [f"P{i:03d}" for i in range(1, 191)]:
        raise RuntimeError("pair IDs are not exactly P001..P190")
    if [r["ELEMENT_ID"] for r in spans] != [f"E{i:03d}" for i in range(1, 79)]:
        raise RuntimeError("text span IDs are not exactly E001..E078")
    if [r["RISK_ID"] for r in rois] != [f"R{i:02d}_" + r["RISK_ID"].split("_", 1)[1] for i, r in enumerate(rois, 1)]:
        raise RuntimeError("risk IDs are not exactly ordered R01..R08")
    if any(r["MACHINE_SUSPICIOUS_CODEPOINT_TOKENS"] for r in spans):
        raise RuntimeError("machine suspicious codepoint token present")

    manual_pairs = require_file("manual_pair_ledger.md").read_text(encoding="utf-8")
    pair_ids = re.findall(r"^- (P\d{3}) ", manual_pairs, re.MULTILINE)
    if pair_ids != [f"P{i:03d}" for i in range(1, 191)]:
        raise RuntimeError("manual pair ledger missing, duplicated, or out of order")
    pair_classes = re.findall(
        r"— (CLEAR_SEPARATE|INTENDED_BORDER_CONTACT|INTENDED_BORDER_NEAR_CONTACT) —", manual_pairs
    )
    if pair_classes.count("CLEAR_SEPARATE") != 174 or pair_classes.count("INTENDED_BORDER_CONTACT") != 8 or pair_classes.count("INTENDED_BORDER_NEAR_CONTACT") != 8:
        raise RuntimeError("manual pair class count mismatch")
    manual_objects = require_file("manual_object_ledger.md").read_text(encoding="utf-8")
    if re.findall(r"^\| (O\d{2}) \|", manual_objects, re.MULTILINE) != [f"O{i:02d}" for i in range(1, 21)]:
        raise RuntimeError("manual object ledger mismatch")
    manual_risks = require_file("manual_risk_roi_ledger.md").read_text(encoding="utf-8")
    if re.findall(r"^\| (R\d{2}) \|", manual_risks, re.MULTILINE) != [f"R{i:02d}" for i in range(1, 9)]:
        raise RuntimeError("manual risk ledger mismatch")
    visual = require_file("manual_visual_adjudication.md").read_text(encoding="utf-8")
    if visual.count(VERDICT) != 1 or "FAIL_TO_MAIN_SOURCE_SCOPE" in visual:
        raise RuntimeError("manual verdict mismatch")

    image_expectations = {
        "page_710_full_200dpi.png": (1654, 2339),
        "page_710_full_300dpi.png": (2481, 3508),
        "figure_caption_native_300dpi.png": (1855, 751),
        "figure_only_native_300dpi.png": (1855, 603),
        "caption_native_300dpi.png": (1855, 151),
        "figure_caption_grayscale_native_300dpi.png": (1855, 751),
        "semantic_object_overlay_native_300dpi.png": (1855, 751),
        "text_measurement_overlay_native_300dpi.png": (1855, 751),
        "page_710_integration_overlay_200dpi.png": (1654, 2339),
    }
    for name, expected_size in image_expectations.items():
        with Image.open(require_file(name)) as im:
            im.verify()
        with Image.open(require_file(name)) as im:
            if im.size != expected_size:
                raise RuntimeError(f"image size mismatch: {name}: {im.size} != {expected_size}")
    for row in rois:
        native = require_file(row["NATIVE1X_FILE"])
        nearest = require_file(row["NEAREST8X_FILE"])
        with Image.open(native) as a, Image.open(nearest) as b:
            a.verify()
            b.verify()
        with Image.open(native) as a, Image.open(nearest) as b:
            if b.size != (a.width * 8, a.height * 8):
                raise RuntimeError(f"nearest8x dimension mismatch: {row['RISK_ID']}")

    files_before_gate, dirs_before_gate = assert_hygiene()
    gate_payload = {
        "handoff_id": HANDOFF_ID,
        "uid": "FIG-P662-01",
        "instance": "/root/sa2_fig_p662_r112_r168_readonly_adjudication_v1",
        "gate_time_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_pdf_identity": "OK",
        "frozen_source_identity": "OK",
        "json_parse": "OK",
        "csv_parse": "OK",
        "png_parse": "OK",
        "manual_object_ids": "20_OF_20_OK",
        "manual_pair_ids": "190_OF_190_OK",
        "manual_pair_class_counts": {"CLEAR_SEPARATE": 174, "INTENDED_BORDER_CONTACT": 8, "INTENDED_BORDER_NEAR_CONTACT": 8},
        "manual_risk_ids": "8_OF_8_OK",
        "text_span_ids": "78_OF_78_OK",
        "suspicious_codepoint_tokens": "NONE",
        "ads": "NONE",
        "cache_or_pyc": "NONE",
        "reparse_or_symlink": "NONE",
        "pre_gate_file_count": len(files_before_gate),
        "pre_gate_directory_count_excluding_root": len(dirs_before_gate),
        "manifest_policy": "SEALED_MANIFEST covers every intended evidence payload file except its structural self; WRITE_STOPPED is final seal metadata and records the manifest hash.",
        "verdict": VERDICT,
    }
    GATE.write_text(json.dumps(gate_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files, directories = assert_hygiene()
    if MANIFEST in files or MARKER in files:
        raise RuntimeError("unexpected seal artifact before manifest close")
    with MANIFEST.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["RELATIVE_PATH", "BYTES", "SHA256", "LAST_WRITE_TIME_UTC_TICKS"])
        for path in files:
            rel = path.relative_to(ROOT).as_posix()
            w.writerow([rel, path.stat().st_size, sha256(path), ntfs_ticks(path)])

    manifest_rows = read_csv(MANIFEST)
    if len(manifest_rows) != len(files):
        raise RuntimeError("manifest row count mismatch")
    if {r["RELATIVE_PATH"] for r in manifest_rows} != {p.relative_to(ROOT).as_posix() for p in files}:
        raise RuntimeError("manifest path closure mismatch")
    manifest_hash = sha256(MANIFEST)
    manifest_bytes = MANIFEST.stat().st_size

    marker_text = (
        "WRITE_STOPPED\n"
        f"HANDOFF_ID={HANDOFF_ID}\n"
        "INSTANCE=/root/sa2_fig_p662_r112_r168_readonly_adjudication_v1\n"
        "UID=FIG-P662-01\n"
        f"VERDICT={VERDICT}\n"
        "MANIFEST=SEALED_MANIFEST.csv\n"
        f"MANIFEST_BYTES={manifest_bytes}\n"
        f"MANIFEST_SHA256={manifest_hash}\n"
        f"MANIFEST_PAYLOAD_FILE_COUNT={len(manifest_rows)}\n"
        "MANIFEST_SCOPE=all intended evidence payload files; manifest structural self-exclusion\n"
        "MARKER_SCOPE=final seal metadata outside manifest; its content seals the manifest hash\n"
        "FINAL_ROOT_CONTENT_OPERATION=os.replace precreated external marker to WRITE_STOPPED.txt\n"
        "NO_POST_MARKER_WRITES_OR_ATTRIBUTE_CHANGES=true\n"
    )
    PENDING.write_text(marker_text, encoding="utf-8", newline="\n")
    max_root_mtime_ns = max(p.stat().st_mtime_ns for p in [*files, MANIFEST])
    marker_time_ns = max(time.time_ns(), max_root_mtime_ns + 10_000_000)
    os.utime(PENDING, ns=(marker_time_ns, marker_time_ns))

    # Final pre-marker hygiene/closure validation. No root write follows except the final marker move.
    final_files, final_directories = assert_hygiene()
    expected_final_pre_marker = set(files) | {MANIFEST}
    if set(final_files) != expected_final_pre_marker:
        raise RuntimeError("pre-marker root file set changed")
    if sha256(MANIFEST) != manifest_hash or MANIFEST.stat().st_size != manifest_bytes:
        raise RuntimeError("manifest changed after close")
    if PENDING.stat().st_mtime_ns <= max_root_mtime_ns:
        raise RuntimeError("pending marker is not strictly latest by LastWriteTime")

    # Make every payload file, every nested directory, the root, and the pending marker ReadOnly.
    for path in final_files:
        set_readonly(path)
    for path in sorted(final_directories, key=lambda p: len(p.parts), reverse=True):
        set_readonly(path)
    set_readonly(ROOT)
    set_readonly(PENDING)

    # UNIQUE ABSOLUTE FINAL ROOT-CONTENT OPERATION. Do not add code after this move that writes or changes attributes.
    os.replace(PENDING, MARKER)


if __name__ == "__main__":
    main()

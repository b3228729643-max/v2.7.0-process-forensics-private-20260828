from __future__ import annotations

import csv
import ctypes
import hashlib
import itertools
import json
import os
import time
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa3_r110_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_coordinate_sweep.tex")
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"
VALIDATION = ROOT / "VALIDATION.json"
EXPECTED_PDF_SHA = "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3"
EXPECTED_SOURCE_SHA = "903DE12067AF0B33F316EC09D65F6803F6BD212D64EB838F2FD8F264748F520E"
FILE_ATTRIBUTE_READONLY = 0x00000001
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(not field for field in reader.fieldnames):
            raise RuntimeError(f"invalid CSV header: {path}")
        rows = list(reader)
        if any(None in row for row in rows):
            raise RuntimeError(f"ragged CSV row: {path}")
        return list(reader.fieldnames), rows


def get_attrs(path: Path) -> int:
    value = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if value == INVALID_FILE_ATTRIBUTES:
        raise ctypes.WinError()
    return int(value)


def set_readonly(path: Path) -> None:
    attrs = get_attrs(path)
    if not ctypes.windll.kernel32.SetFileAttributesW(str(path), attrs | FILE_ATTRIBUTE_READONLY):
        raise ctypes.WinError()


def extra_streams(path: Path) -> list[str]:
    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", ctypes.c_wchar * 296)]

    kernel32 = ctypes.windll.kernel32
    kernel32.FindFirstStreamW.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(WIN32_FIND_STREAM_DATA), ctypes.c_ulong]
    kernel32.FindFirstStreamW.restype = ctypes.c_void_p
    kernel32.FindNextStreamW.argtypes = [ctypes.c_void_p, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    kernel32.FindNextStreamW.restype = ctypes.c_int
    kernel32.FindClose.argtypes = [ctypes.c_void_p]
    data = WIN32_FIND_STREAM_DATA()
    handle = kernel32.FindFirstStreamW(str(path), 0, ctypes.byref(data), 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        error = ctypes.get_last_error()
        if error in (0, 38):
            return []
        raise ctypes.WinError(error)
    names: list[str] = []
    try:
        while True:
            names.append(data.cStreamName)
            if not kernel32.FindNextStreamW(handle, ctypes.byref(data)):
                break
    finally:
        kernel32.FindClose(handle)
    return [name for name in names if name != "::$DATA"]


def all_paths() -> tuple[list[Path], list[Path]]:
    files = sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())
    dirs = sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.relative_to(ROOT).as_posix(), reverse=True)
    return files, dirs


def main() -> None:
    if MARKER.exists() or MANIFEST.exists() or VALIDATION.exists():
        raise RuntimeError("seal artifacts already exist; refusing a second seal")
    if not ROOT.is_dir():
        raise RuntimeError("evidence root missing")
    root_resolved = ROOT.resolve()
    if PDF.stat().st_size != 4_967_063 or sha256(PDF) != EXPECTED_PDF_SHA:
        raise RuntimeError("official PDF identity mismatch")
    if SOURCE.stat().st_size != 4_352 or sha256(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("source identity mismatch")

    files, dirs = all_paths()
    if any(root_resolved not in path.resolve().parents for path in files + dirs):
        raise RuntimeError("path escaped evidence root")
    cache_paths = [p for p in files + dirs if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"} or p.name.lower() in {"thumbs.db", ".ds_store"}]
    reparse_paths = [p for p in files + dirs if get_attrs(p) & FILE_ATTRIBUTE_REPARSE_POINT]
    ads = {p.relative_to(ROOT).as_posix(): extra_streams(p) for p in files}
    ads = {k: v for k, v in ads.items() if v}
    if cache_paths or reparse_paths or ads:
        raise RuntimeError(f"cleanliness failure cache={cache_paths} reparse={reparse_paths} ads={ads}")

    csv_results: dict[str, int] = {}
    parsed_csv: dict[str, tuple[list[str], list[dict[str, str]]]] = {}
    for path in files:
        if path.suffix.lower() == ".csv":
            parsed_csv[path.name] = parse_csv(path)
            csv_results[path.relative_to(ROOT).as_posix()] = len(parsed_csv[path.name][1])
    json_results: list[str] = []
    for path in files:
        if path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            json_results.append(path.relative_to(ROOT).as_posix())

    objects = parsed_csv["objects_machine.csv"][1]
    pairs = parsed_csv["all_unordered_pairs_machine.csv"][1]
    texts = parsed_csv["text_spans_machine.csv"][1]
    manual_objects = parsed_csv["object_review_manual.csv"][1]
    manual_pairs = parsed_csv["relevant_close_pairs_manual.csv"][1]
    manual_text = parsed_csv["text_glyph_review_manual.csv"][1]
    manual_rois = parsed_csv["roi_review_manual.csv"][1]
    manual_views = parsed_csv["view_review_manual.csv"][1]
    object_ids = [r["object_id"] for r in objects]
    expected_pairs = {(a, b) for a, b in itertools.combinations(object_ids, 2)}
    actual_pairs = {(r["object_a"], r["object_b"]) for r in pairs}
    if len(objects) != 46 or len(set(object_ids)) != 46:
        raise RuntimeError("object denominator mismatch")
    if len(pairs) != 1035 or len({r["pair_id"] for r in pairs}) != 1035 or actual_pairs != expected_pairs:
        raise RuntimeError("all-pair denominator mismatch")
    if len(texts) != 47 or len({r["text_id"] for r in texts}) != 47:
        raise RuntimeError("text denominator mismatch")
    if len(manual_objects) != 46 or {r["object_id"] for r in manual_objects} != set(object_ids):
        raise RuntimeError("manual object coverage mismatch")
    if len(manual_pairs) != 38 or not {r["pair_id"] for r in manual_pairs}.issubset({r["pair_id"] for r in pairs}):
        raise RuntimeError("manual pair coverage mismatch")
    if len(manual_text) != 47 or {r["text_id"] for r in manual_text} != {r["text_id"] for r in texts}:
        raise RuntimeError("manual text coverage mismatch")
    if len(manual_rois) != 5 or len(manual_views) != 18:
        raise RuntimeError("manual ROI/view coverage mismatch")
    if any(r["decision"] != "PASS" for r in manual_objects + manual_pairs + manual_text + manual_rois + manual_views):
        raise RuntimeError("manual PASS family contains a non-PASS row")
    forbidden_machine_fields = {"reviewer", "decision", "pass", "fail", "boolean", "note", "manual_note"}
    for name in ("objects_machine.csv", "all_unordered_pairs_machine.csv", "text_spans_machine.csv"):
        header = {field.lower() for field in parsed_csv[name][0]}
        if header & forbidden_machine_fields:
            raise RuntimeError(f"machine file contains manual field: {name}")

    required_renders = [
        "page_0684_native300dpi.png",
        "figure_caption_complete_native300dpi.png",
        "figure_crop_native300dpi.png",
        "figure_crop_grayscale_native300dpi.png",
        "object_overlay_native300dpi.png",
        "semantic_overlay_native300dpi.png",
        "text_overlay_native300dpi.png",
    ] + [f"roi{i:02d}_{suffix}" for i, suffix in []]
    for name in required_renders:
        if not (ROOT / "renders" / name).is_file():
            raise RuntimeError(f"required render missing: {name}")
    for prefix in (
        "roi01_update_order_arrow",
        "roi02_updated_current_old_slots",
        "roi03_substep_state_formula",
        "roi04_round_state_equivalence_record",
        "roi05_caption_codepoints",
    ):
        for suffix in ("native1x.png", "nearest8x.png"):
            if not (ROOT / "renders" / f"{prefix}_{suffix}").is_file():
                raise RuntimeError(f"required ROI missing: {prefix}_{suffix}")

    validation = {
        "validation_stage": "pre_manifest_pre_wstop",
        "identity_ok": True,
        "path_containment_ok": True,
        "json_parse_ok": True,
        "csv_parse_ok": True,
        "object_count": 46,
        "object_unique_count": 46,
        "all_unordered_pair_count": 1035,
        "all_pair_formula_ok": True,
        "all_pair_combination_coverage_ok": True,
        "text_span_count": 47,
        "manual_object_count": 46,
        "manual_relevant_close_pair_count": 38,
        "manual_text_count": 47,
        "manual_roi_count": 5,
        "manual_view_count": 18,
        "machine_manual_field_separation_ok": True,
        "ads_count": 0,
        "cache_count": 0,
        "pyc_count": 0,
        "reparse_count": 0,
        "wstop_absent_before_seal": True,
        "outcome": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "csv_row_counts": csv_results,
        "json_files_parsed": json_results,
    }
    VALIDATION.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files, dirs = all_paths()
    payload = []
    for path in files:
        if path in (MANIFEST, MARKER):
            continue
        payload.append({
            "relative_path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest_data = {
        "schema": "SA3_R110_EVIDENCE_MANIFEST_V1",
        "root": str(ROOT),
        "handoff_id": "C-FIG-P634-01-R110-SA3-FRESH-ISOLATED-V1",
        "outcome": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "payload_file_count": len(payload),
        "payload": payload,
        "exclusions": {
            "manifest_self": {"relative_path": "MANIFEST.json", "excluded": True, "reason": "self-hash is undefined"},
            "write_stopped": {"relative_path": "WRITE_STOPPED", "excluded": True, "reason": "marker is written strictly after the complete manifest"},
        },
    }
    MANIFEST.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    loaded = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if loaded["payload_file_count"] != len(payload):
        raise RuntimeError("manifest count mismatch")
    for entry in loaded["payload"]:
        path = ROOT / Path(entry["relative_path"])
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"manifest entry mismatch: {entry['relative_path']}")

    max_before_marker = max(path.stat().st_mtime_ns for path in all_paths()[0])
    time.sleep(0.05)
    marker_data = {
        "marker": "WRITE_STOPPED",
        "handoff_id": "C-FIG-P634-01-R110-SA3-FRESH-ISOLATED-V1",
        "result": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "manifest_relative_path": "MANIFEST.json",
        "manifest_bytes": MANIFEST.stat().st_size,
        "manifest_sha256": sha256(MANIFEST),
        "payload_file_count": len(payload),
        "manifest_self_excluded": True,
        "wstop_excluded_from_manifest": True,
    }
    MARKER.write_text(json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if MARKER.stat().st_mtime_ns <= max_before_marker:
        raise RuntimeError("WRITE_STOPPED is not strict latest before readonly conversion")

    files, dirs = all_paths()
    for path in files:
        set_readonly(path)
    for path in dirs:
        set_readonly(path)
    set_readonly(ROOT)

    files, dirs = all_paths()
    marker_files = [p for p in files if p.name == "WRITE_STOPPED"]
    marker_ns = MARKER.stat().st_mtime_ns
    at_or_after_excluding_marker = [p for p in files if p != MARKER and p.stat().st_mtime_ns >= marker_ns]
    postmarker = [p for p in files if p != MARKER and p.stat().st_mtime_ns > marker_ns]
    final_ads = {p.relative_to(ROOT).as_posix(): extra_streams(p) for p in files}
    final_ads = {k: v for k, v in final_ads.items() if v}
    final_cache = [p for p in files + dirs if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}]
    final_reparse = [p for p in files + dirs if get_attrs(p) & FILE_ATTRIBUTE_REPARSE_POINT]
    nonreadonly_files = [p for p in files if not (get_attrs(p) & FILE_ATTRIBUTE_READONLY)]
    nonreadonly_dirs = [p for p in [ROOT] + dirs if not (get_attrs(p) & FILE_ATTRIBUTE_READONLY)]
    if len(marker_files) != 1 or at_or_after_excluding_marker or postmarker or final_ads or final_cache or final_reparse or nonreadonly_files or nonreadonly_dirs:
        raise RuntimeError(
            "post-seal validation failed: "
            f"markers={len(marker_files)} at_or_after={at_or_after_excluding_marker} postmarker={postmarker} "
            f"ads={final_ads} cache={final_cache} reparse={final_reparse} "
            f"nonreadonly_files={nonreadonly_files} nonreadonly_dirs={nonreadonly_dirs}"
        )

    key_paths = [ROOT / "REPORT.md", ROOT / "HANDOFF.json", MANIFEST, MARKER]
    result = {
        "sealed": True,
        "result": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
        "payload_file_count": len(payload),
        "total_file_count_including_manifest_and_wstop": len(files),
        "manifest_entry_validation_ok": True,
        "json_parse_ok": True,
        "csv_parse_ok": True,
        "ads_count": 0,
        "cache_count": 0,
        "pyc_count": 0,
        "reparse_count": 0,
        "marker_unique_count": 1,
        "marker_strict_latest": True,
        "at_or_after_excluding_marker_count": 0,
        "postmarker_count": 0,
        "readonly_file_count": len(files),
        "readonly_directory_count_including_root": len(dirs) + 1,
        "key_files": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in key_paths
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

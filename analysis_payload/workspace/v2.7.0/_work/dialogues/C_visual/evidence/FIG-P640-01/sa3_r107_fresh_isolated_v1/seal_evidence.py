from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import os
import stat
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P640-01\sa3_r107_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
EXPECTED_PDF_SHA = "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3"
REVIEWER = "SA3-R107-FRESH-ISOLATED-V1"
MANIFEST = ROOT / "ARTIFACT_MANIFEST.sha256"
SEAL = ROOT / "SEAL.json"
STOP = ROOT / "WRITE_STOPPED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def csv_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise AssertionError(f"empty CSV: {name}")
    return rows


def require_unique(rows: list[dict[str, str]], key: str, expected: int, name: str) -> set[str]:
    values = [row[key] for row in rows]
    if len(rows) != expected or len(set(values)) != expected or any(not value for value in values):
        raise AssertionError(f"count/unique failure: {name} {len(rows)} {len(set(values))} expected {expected}")
    return set(values)


def require_manual(rows: list[dict[str, str]], expected: int, key: str, name: str) -> set[str]:
    ids = require_unique(rows, key, expected, name)
    for index, row in enumerate(rows, 1):
        if row.get("reviewer") != REVIEWER:
            raise AssertionError(f"reviewer failure {name}:{index}")
        if row.get("decision") != "PASS":
            raise AssertionError(f"manual decision failure {name}:{index}")
        if any(value is None or value == "" for value in row.values()):
            raise AssertionError(f"blank manual cell {name}:{index}")
        if not row.get("note"):
            raise AssertionError(f"missing evidence-specific note {name}:{index}")
    return ids


def open_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        size = image.size
    if size[0] <= 0 or size[1] <= 0:
        raise AssertionError(f"invalid PNG dimensions: {path}")
    return size


def alternate_streams(path: Path) -> list[str]:
    if os.name != "nt":
        return []
    from ctypes import wintypes

    class WIN32_FIND_STREAM_DATA(ctypes.Structure):
        _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", wintypes.WCHAR * 296)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    find_first = kernel32.FindFirstStreamW
    find_first.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
    find_first.restype = wintypes.HANDLE
    find_next = kernel32.FindNextStreamW
    find_next.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    find_next.restype = wintypes.BOOL
    find_close = kernel32.FindClose
    find_close.argtypes = [wintypes.HANDLE]
    find_close.restype = wintypes.BOOL

    data = WIN32_FIND_STREAM_DATA()
    handle = find_first(str(path), 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        error = ctypes.get_last_error()
        if error in (2, 38):
            return []
        raise OSError(error, f"FindFirstStreamW failed for {path}")
    names: list[str] = []
    try:
        names.append(data.cStreamName)
        while find_next(handle, ctypes.byref(data)):
            names.append(data.cStreamName)
        error = ctypes.get_last_error()
        if error not in (0, 38):
            raise OSError(error, f"FindNextStreamW failed for {path}")
    finally:
        find_close(handle)
    return [name for name in names if name != "::$DATA"]


def main() -> None:
    if STOP.exists() or SEAL.exists() or MANIFEST.exists():
        raise AssertionError("seal artifacts already exist; refusing a second seal")

    identity = json.loads((ROOT / "machine" / "machine_identity.json").read_text(encoding="utf-8"))
    if PDF.stat().st_size != 4_967_249 or sha256(PDF) != EXPECTED_PDF_SHA:
        raise AssertionError("official PDF hash/size mismatch")
    with fitz.open(PDF) as doc:
        if doc.page_count != 817:
            raise AssertionError("official PDF page count mismatch")
    if identity["physical_page"] != 690 or identity["printed_page"] != 677 or identity["figure_no"] != "33.7":
        raise AssertionError("page/figure mapping mismatch")
    if identity["page_300dpi_native_dimensions"] != [2481, 3508]:
        raise AssertionError("native grid mismatch")

    glyph_machine = csv_rows("machine/machine_glyph_inventory.csv")
    glyph_manual = csv_rows("manual_glyph_review.csv")
    glyph_pixel = csv_rows("after_pixel_measurements.csv")
    glyph_ids = require_unique(glyph_machine, "glyph_id", 145, "machine glyph")
    if require_manual(glyph_manual, 145, "glyph_id", "manual glyph") != glyph_ids:
        raise AssertionError("manual/machine glyph ID mismatch")
    if require_unique(glyph_pixel, "glyph_id", 145, "pixel glyph") != glyph_ids:
        raise AssertionError("pixel/machine glyph ID mismatch")
    if any(row["mask_empty"] != "false" for row in glyph_machine):
        raise AssertionError("empty glyph mask")
    if any(row["missing_stroke_px"] != "0" or row["foreign_pixel_px"] != "0" for row in glyph_manual):
        raise AssertionError("manual glyph completeness/purity failure")
    if csv_rows_allow_empty(ROOT / "machine" / "machine_glyph_cross_mask_overlaps.csv"):
        raise AssertionError("glyph cross-mask overlap rows present")

    contact = csv_rows("machine/machine_glyph_contact_index.csv")
    if require_unique(contact, "glyph_id", 145, "contact glyph") != glyph_ids:
        raise AssertionError("contact glyph coverage mismatch")
    sheets = {row["sheet"] for row in contact}
    if len(sheets) != 29:
        raise AssertionError("contact sheet count mismatch")
    for sheet in sheets:
        open_png(ROOT / "glyphs" / "contact_sheets" / sheet)
    for row in glyph_machine:
        for field in ("mask_path", "native1x_triptych_path", "eightx_triptych_path"):
            open_png(ROOT / row[field])

    objects = csv_rows("machine/machine_semantic_object_inventory.csv")
    object_ids = require_unique(objects, "object_id", 28, "machine object")
    if require_manual(csv_rows("manual_object_review.csv"), 28, "object_id", "manual object") != object_ids:
        raise AssertionError("manual/machine object mismatch")
    breakdown = {
        "TEXT": sum(row["kind"] == "TEXT" for row in objects),
        "GRAPHIC": sum(row["kind"] == "GRAPHIC" for row in objects),
        "GRAPHIC_MATH_RULE": sum(row["kind"] == "GRAPHIC_MATH_RULE" for row in objects),
        "BACKGROUND": sum(row["kind"] == "BACKGROUND" for row in objects),
    }
    if breakdown != {"TEXT": 15, "GRAPHIC": 10, "GRAPHIC_MATH_RULE": 1, "BACKGROUND": 2}:
        raise AssertionError(f"object breakdown mismatch: {breakdown}")
    for row in objects:
        if int(row["raw_mask_pixel_count"]) <= 0:
            raise AssertionError(f"empty object mask {row['object_id']}")
        open_png(ROOT / row["mask_path"])

    drawings = csv_rows("machine/machine_pdf_drawing_inventory.csv")
    drawing_ids = require_unique(drawings, "pdf_drawing_index", 20, "machine drawing")
    if require_manual(csv_rows("manual_drawing_record_review.csv"), 20, "pdf_drawing_index", "manual drawing") != drawing_ids:
        raise AssertionError("manual/machine drawing mismatch")
    if sum(row["is_math_rule"] == "true" for row in drawings) != 1:
        raise AssertionError("math rule drawing count mismatch")
    if sum(row["is_opaque_background"] == "true" for row in drawings) != 2:
        raise AssertionError("opaque background drawing count mismatch")

    pairs = csv_rows("machine/machine_all_unordered_pairs.csv")
    pair_ids = require_unique(pairs, "pair_id", 378, "all unordered pairs")
    expected_pairs = {tuple(sorted((a, b))) for index, a in enumerate(sorted(object_ids)) for b in sorted(object_ids)[index + 1:]}
    actual_pairs = {tuple(sorted((row["object_a"], row["object_b"]))) for row in pairs}
    if expected_pairs != actual_pairs:
        raise AssertionError("C(N,2) object-pair coverage mismatch")
    raw_candidates = [row for row in pairs if int(row["raw_mask_overlap_px"]) > 0]
    if len(raw_candidates) != 12 or sum(int(row["raw_mask_overlap_px"]) for row in raw_candidates) != 5843:
        raise AssertionError("raw overlap candidate denominator mismatch")

    critical_machine = csv_rows("machine/machine_critical_relation_candidates.csv")
    critical_ids = require_unique(critical_machine, "pair_id", 42, "machine critical")
    if not critical_ids <= pair_ids:
        raise AssertionError("critical pair outside all-pair denominator")
    if require_manual(csv_rows("manual_critical_relation_review.csv"), 42, "pair_id", "manual critical") != critical_ids:
        raise AssertionError("manual/machine critical mismatch")
    critical_evidence = csv_rows("machine/machine_critical_evidence_index.csv")
    if require_unique(critical_evidence, "pair_id", 42, "critical evidence") != critical_ids:
        raise AssertionError("critical evidence ID mismatch")
    for row in critical_evidence:
        open_png(ROOT / row["native1x_path"])
        open_png(ROOT / row["eightx_path"])

    overlap_manual = csv_rows("after_overlap_report.csv")
    overlap_ids = require_manual(overlap_manual, 12, "pair_id", "manual overlap")
    raw_ids = {row["pair_id"] for row in raw_candidates}
    if overlap_ids != raw_ids:
        raise AssertionError("overlap candidate ID mismatch")
    if sum(int(row["overlap_candidate_pixel_count"]) for row in overlap_manual) != 5843:
        raise AssertionError("manual overlap pixel sum mismatch")
    if any(row["classification"] != "MASK_CONTAMINATION" for row in overlap_manual):
        raise AssertionError("overlap three-way classification mismatch")
    if sum(int(row["mask_contamination_pixel_count"]) for row in overlap_manual) != 5843:
        raise AssertionError("mask contamination pixel sum mismatch")
    if sum(int(row["true_collision_pixel_count"]) for row in overlap_manual) != 0:
        raise AssertionError("true collision nonzero")
    if sum(int(row["unresolved_pixel_count"]) for row in overlap_manual) != 0:
        raise AssertionError("unresolved pixel nonzero")

    require_manual(csv_rows("manual_peer_role_review.csv"), 24, "panel_role_script_id", "manual peer-role")
    views = csv_rows("manual_view_review.csv")
    require_manual(views, 9, "view_id", "manual view")
    for row in views:
        size = open_png(ROOT / row["path"])
        if f"{size[0]}x{size[1]}" != row["native_dimensions"]:
            raise AssertionError(f"view dimension mismatch {row['view_id']}: {size}")
        if row["actually_opened"] != "true":
            raise AssertionError(f"view not opened {row['view_id']}")
    require_manual(csv_rows("manual_hard_gate_review.csv"), 16, "gate_id", "manual hard gate")
    require_manual(csv_rows("after_font_audit.csv"), 15, "element_id", "font audit")

    summary = json.loads((ROOT / "machine" / "machine_summary.json").read_text(encoding="utf-8"))
    expected_summary = {
        "glyph_count": 145,
        "glyph_unique_id_count": 145,
        "glyph_empty_mask_count": 0,
        "glyph_cross_mask_overlap_pair_count": 0,
        "pdf_visible_drawing_record_count": 20,
        "pdf_drawing_record_unique_count": 20,
        "semantic_leaf_object_denominator_n": 28,
        "unordered_pair_expected_c_n_2": 378,
        "unordered_pair_emitted_count": 378,
        "critical_relation_candidate_count": 42,
        "critical_relation_evidence_count": 42,
        "pair_raw_overlap_candidate_count": 12,
        "pair_raw_overlap_candidate_pixels_sum_noncanonical": 5843,
        "contact_sheet_count": 29,
        "render_count": 9,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise AssertionError(f"machine summary mismatch {key}: {summary.get(key)} != {value}")

    result = parse_key_values(ROOT / "SA3_RESULT.txt")
    required_result = {
        "SA3_REVIEW_OUTCOME": "CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE",
        "LOCAL_PASS_COUNTED": "false",
        "GLOBAL_PASS_COUNTED": "false",
        "HARD_FAILURE_COUNT": "0",
        "UNRESOLVED_COUNT": "0",
        "OVERLAP_CANDIDATE_PIXEL_COUNT": "5843",
        "MASK_CONTAMINATION_PIXEL_COUNT": "5843",
        "OVERLAP_PIXEL_COUNT": "0",
        "CLIP_PIXEL_COUNT": "0",
        "PIXEL_ADJUDICATION_STATUS": "MASK_CONTAMINATION_CONFIRMED",
    }
    for key, value in required_result.items():
        if result.get(key) != value:
            raise AssertionError(f"result mismatch {key}")

    required_text = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    for token in (
        "SA3_MODEL = gpt-5.6-sol",
        "SA3_REASONING = xhigh",
        "SOURCE_FONT_PASS = true",
        "FONT_VISUAL_HARMONY_PASS = true",
        "OVERLAP_CANDIDATE_PIXEL_COUNT = 5843",
        "MASK_CONTAMINATION_PIXEL_COUNT = 5843",
        "OVERLAP_PIXEL_COUNT = 0",
        "CLIP_PIXEL_COUNT = 0",
        "SA3_REVIEW_OUTCOME = CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE",
    ):
        if token not in required_text:
            raise AssertionError(f"visual report token missing: {token}")

    all_files = sorted(path for path in ROOT.rglob("*") if path.is_file())
    py_cache = [path for path in ROOT.rglob("*") if path.name == "__pycache__" or path.suffix.lower() in {".pyc", ".pyo"}]
    if py_cache:
        raise AssertionError(f"cache/pyc present: {py_cache}")
    reparse = []
    ads = []
    folded = set()
    for path in all_files:
        relative = path.relative_to(ROOT).as_posix()
        if ":" in relative:
            raise AssertionError(f"colon/ADS-unsafe relative path: {relative}")
        folded_key = relative.casefold()
        if folded_key in folded:
            raise AssertionError(f"casefold path collision: {relative}")
        folded.add(folded_key)
        attrs = getattr(path.lstat(), "st_file_attributes", 0)
        if path.is_symlink() or (attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
            reparse.append(relative)
        for stream in alternate_streams(path):
            ads.append(f"{relative}{stream}")
    if reparse:
        raise AssertionError(f"reparse points present: {reparse}")
    if ads:
        raise AssertionError(f"alternate data streams present: {ads}")

    pngs = [path for path in all_files if path.suffix.lower() == ".png"]
    if len(pngs) != 590:
        raise AssertionError(f"ordinary PNG count mismatch: {len(pngs)} != 590")
    for path in pngs:
        open_png(path)

    manifest_targets = [path for path in all_files if path.name not in {MANIFEST.name, SEAL.name, STOP.name}]
    manifest_lines = [f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}" for path in manifest_targets]
    MANIFEST.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8", newline="\n")

    reparsed = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        path = ROOT / Path(relative)
        if not path.is_file() or sha256(path) != digest:
            raise AssertionError(f"manifest reparse/hash failure: {relative}")
        reparsed.append(relative)
    if len(reparsed) != len(manifest_targets) or len(set(reparsed)) != len(manifest_targets):
        raise AssertionError("manifest count/unique failure")

    manifest_sha = sha256(MANIFEST)
    seal_record = {
        "uid": "FIG-P640-01",
        "handoff_id": "C-FIG-P640-01-R107-SA3-FRESH-ISOLATED-V1",
        "reviewer": REVIEWER,
        "model": "gpt-5.6-sol",
        "reasoning": "xhigh",
        "fork_turns": "none",
        "official_round": "R107",
        "physical_page": 690,
        "printed_page": 677,
        "figure": "33.7",
        "artifact_manifest": MANIFEST.name,
        "artifact_manifest_sha256": manifest_sha,
        "manifest_target_count": len(manifest_targets),
        "ordinary_png_count_opened": len(pngs),
        "ads_count": 0,
        "reparse_point_count": 0,
        "cache_or_pyc_count": 0,
        "manual_counts": {
            "glyph": 145,
            "object": 28,
            "drawing_record": 20,
            "critical_relation": 42,
            "overlap_candidate": 12,
            "peer_role_script": 24,
            "view": 9,
            "hard_gate": 16,
            "font_object": 15,
        },
        "machine_counts": {
            "glyph": 145,
            "drawing_record": 20,
            "semantic_leaf_N": 28,
            "all_unordered_pairs": 378,
            "critical_relations": 42,
            "contact_sheets": 29,
            "raw_overlap_candidate_pairs": 12,
            "raw_overlap_candidate_pixels": 5843,
        },
        "canonical_overlap_pixel_count": 0,
        "clip_pixel_count": 0,
        "unresolved_count": 0,
        "hard_failure_count": 0,
        "outcome": "CANDIDATE_PASS_PENDING_MAIN_ACCEPTANCE",
        "local_pass_counted": False,
        "global_pass_counted": False,
        "validation": "PASS",
        "sealed": True,
    }
    SEAL.write_text(json.dumps(seal_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    seal_sha = sha256(SEAL)
    STOP.write_text(
        "WRITE_STOPPED=true\n"
        f"SEAL_SHA256={seal_sha}\n"
        f"ARTIFACT_MANIFEST_SHA256={manifest_sha}\n"
        "POST_SEAL_WRITES_EXPECTED=0\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"validation": "PASS", "sealed": True, "manifest_targets": len(manifest_targets), "png_opened": len(pngs), "manifest_sha256": manifest_sha, "seal_sha256": seal_sha}, ensure_ascii=False))


def csv_rows_allow_empty(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_key_values(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


if __name__ == "__main__":
    main()

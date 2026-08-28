from __future__ import annotations

import csv
import ctypes
from ctypes import wintypes
import hashlib
import itertools
import json
from pathlib import Path

import pdfplumber
from PIL import Image
from pypdf import PdfReader


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P656-01\sa1_r107_fresh_isolated_v1")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_C_visual\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_multinomial_counts.tex")
EXPECTED_PDF_SHA = "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3"
EXPECTED_SOURCE_SHA = "BC954A32F6FC8811F9557AD9A3147795CB6CB467DEAEF6195A3A0B1D9E855852"
OUTCOME = "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3"
MANIFEST_EXCLUSIONS = {"artifact_manifest.csv", "WRITE_STOPPED"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    require(path.is_file(), f"missing CSV: {name}")
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    require(rows, f"empty CSV: {name}")
    return rows


def unique_exact(rows: list[dict[str, str]], field: str, expected: list[str], label: str) -> None:
    values = [r[field] for r in rows]
    require(len(values) == len(set(values)), f"duplicate {label}")
    require(values == expected, f"missing/reordered {label}")


def check_manual(name: str, id_field: str, expected: list[str]) -> list[dict[str, str]]:
    rows = read_csv(name)
    unique_exact(rows, id_field, expected, name)
    for row in rows:
        for field in ("reviewer", "decision", "note"):
            require(row.get(field, "").strip(), f"blank {field} in {name}:{row.get(id_field)}")
        require(row["decision"] == "PASS", f"non-PASS in {name}:{row[id_field]}")
    return rows


class WIN32_FIND_STREAM_DATA(ctypes.Structure):
    _fields_ = [("StreamSize", ctypes.c_longlong), ("cStreamName", wintypes.WCHAR * 296)]


def streams(path: Path) -> list[str]:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    first = kernel32.FindFirstStreamW
    first.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(WIN32_FIND_STREAM_DATA), wintypes.DWORD]
    first.restype = wintypes.HANDLE
    nxt = kernel32.FindNextStreamW
    nxt.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_STREAM_DATA)]
    nxt.restype = wintypes.BOOL
    close = kernel32.FindClose
    close.argtypes = [wintypes.HANDLE]
    data = WIN32_FIND_STREAM_DATA()
    handle = first(str(path), 0, ctypes.byref(data), 0)
    invalid = ctypes.c_void_p(-1).value
    require(handle != invalid, f"FindFirstStreamW failed for {path}: {ctypes.get_last_error()}")
    out = [data.cStreamName]
    try:
        while nxt(handle, ctypes.byref(data)):
            out.append(data.cStreamName)
        require(ctypes.get_last_error() in (0, 38), f"FindNextStreamW failed for {path}: {ctypes.get_last_error()}")
    finally:
        close(handle)
    return out


require(ROOT.is_dir(), "assigned root missing")
require(not (ROOT / "WRITE_STOPPED").exists(), "WRITE_STOPPED already exists; refuse second seal")
require(PDF.stat().st_size == 4_967_249, "PDF byte identity mismatch")
require(sha256(PDF) == EXPECTED_PDF_SHA, "PDF SHA mismatch")
require(sha256(SOURCE) == EXPECTED_SOURCE_SHA, "source SHA mismatch")
reader = PdfReader(str(PDF))
require(len(reader.pages) == 817, "PDF page-count mismatch")
with pdfplumber.open(PDF) as doc:
    page = doc.pages[704]
    page_text = page.extract_text() or ""
    require("34.2" in page_text and "多项分布" in page_text and "计数向量" in page_text, "physical page 705 caption/content identity mismatch")
    require(abs(float(page.width) - 595.276) < 0.01 and abs(float(page.height) - 841.89) < 0.01, "page point geometry mismatch")

source_text = SOURCE.read_text(encoding="utf-8")
for snippet in (
    "1,1,1,2,3,3", "1,3,1,2,1,3", "3,1,2,1,3,1",
    r"\boldsymbol n=(n_1,n_2,n_3)=(3,1,2)", r"n_k\in\mathbb Z_{\ge0}",
    "计数向量，不是概率向量", r"{N!}/{\prod_k n_k!}",
    r"\label{fig:V5-C05-multinomial-counts}",
):
    require(snippet in source_text, f"source semantic snippet missing: {snippet}")
for forbidden in (r"\resizebox", r"\scalebox", "transform shape"):
    require(forbidden not in source_text, f"unexpected source scaling: {forbidden}")

glyph = read_csv("glyph_inventory_machine.csv")
pixel_alias = read_csv("after_pixel_measurements.csv")
drawing = read_csv("drawing_inventory_machine.csv")
pairs = read_csv("all_unordered_pairs_machine.csv")
overlap_alias = read_csv("after_overlap_report.csv")
critical = read_csv("critical_relations_machine.csv")
clips = read_csv("object_clip_machine.csv")
views = read_csv("view_inventory_machine.csv")
id_map = read_csv("id_safe_filename_map.csv")
punct = read_csv("punctuation_peer_machine.csv")
role = read_csv("role_height_summary_machine.csv")

gids = [f"G{i:03d}" for i in range(1, 91)]
dids = [f"D{i:03d}" for i in range(1, 26)]
object_ids = gids + dids
unique_exact(glyph, "element_id", gids, "glyph IDs")
unique_exact(drawing, "element_id", dids, "drawing IDs")
unique_exact(id_map, "element_id", object_ids, "safe filename IDs")
require(len({r["safe_filename"] for r in id_map}) == 115, "nonunique safe filenames")
require(len(glyph) == len(pixel_alias) == 90, "pixel alias denominator mismatch")
require(sha256(ROOT / "glyph_inventory_machine.csv") == sha256(ROOT / "after_pixel_measurements.csv"), "pixel alias byte mismatch")
require(all(r["machine_mask_nonempty"] == "True" for r in glyph), "empty glyph mask")
require(all(r["machine_mask_nonempty"] == "True" for r in drawing), "empty drawing mask")

expected_pairs = list(itertools.combinations(object_ids, 2))
require(len(pairs) == len(overlap_alias) == len(expected_pairs) == 6555, "all-pair denominator mismatch")
require(sha256(ROOT / "all_unordered_pairs_machine.csv") == sha256(ROOT / "after_overlap_report.csv"), "overlap alias byte mismatch")
for idx, (row, expected_pair) in enumerate(zip(pairs, expected_pairs), 1):
    require(row["pair_index"] == str(idx) and row["pair_id"] == f"P{idx:04d}", f"pair index/ID mismatch at {idx}")
    require((row["a_id"], row["b_id"]) == expected_pair, f"pair membership/order mismatch at {idx}")
nonzero = {r["pair_id"]: int(r["intersection_px"]) for r in pairs if int(r["intersection_px"]) > 0}
require(nonzero == {"P6539": 18, "P6541": 41, "P6555": 38}, f"frozen overlap mismatch: {nonzero}")
require(sum(nonzero.values()) == 97, "raw intersection pixel total mismatch")

crids = [f"CR{i:03d}" for i in range(1, 35)]
unique_exact(critical, "relation_id", crids, "critical relation IDs")
require(len(critical) == 34, "critical denominator mismatch")
critical_by_id = {r["relation_id"]: r for r in critical}
require((critical_by_id["CR027"]["a_ids"], critical_by_id["CR027"]["b_ids"], critical_by_id["CR027"]["intersection_px"], critical_by_id["CR027"]["clearance_px"]) == ("D020", "D021", "41", "0.000"), "CR027 mismatch")
require((critical_by_id["CR028"]["a_ids"], critical_by_id["CR028"]["b_ids"], critical_by_id["CR028"]["intersection_px"], critical_by_id["CR028"]["clearance_px"]) == ("D021", "D019", "0", "2.000"), "CR028 mismatch")
require((critical_by_id["CR029"]["a_ids"], critical_by_id["CR029"]["b_ids"], critical_by_id["CR029"]["intersection_px"], critical_by_id["CR029"]["clearance_px"]) == ("D024", "D025", "38", "0.000"), "CR029 mismatch")
require((critical_by_id["CR030"]["a_ids"], critical_by_id["CR030"]["b_ids"], critical_by_id["CR030"]["intersection_px"], critical_by_id["CR030"]["clearance_px"]) == ("D025", "D023", "0", "3.000"), "CR030 mismatch")

unique_exact(clips, "element_id", object_ids, "clip IDs")
require(len(clips) == 115 and sum(int(r["foreground_outside_crop_px"]) for r in clips) == 0, "clip gate mismatch")
require(all(r["machine_clip_status"] == "INSIDE" for r in clips), "non-INSIDE clip row")
vids = [f"V{i:02d}" for i in range(1, 11)]
unique_exact(views, "view_id", vids, "view IDs")
require(len(role) == 8, "role machine denominator mismatch")
require({r["element_id"] for r in punct} == {"G030", "G033", "G040", "G042", "G055", "G066"}, "punctuation inventory mismatch")

manual_glyph = check_manual("manual_glyph_ledger.csv", "element_id", gids)
for row in manual_glyph:
    require(row["original_match"] == row["overlay_complete"] == row["mask_only_pure"] == "true", f"glyph visual boolean mismatch: {row['element_id']}")
    require(row["missing_stroke_px"] == row["foreign_pixel_px"] == "0", f"glyph purity/completeness mismatch: {row['element_id']}")
    require((ROOT / row["sheet"]).is_file(), f"glyph sheet reference missing: {row['sheet']}")
manual_drawing = check_manual("manual_drawing_ledger.csv", "element_id", dids)
for row in manual_drawing:
    require(row["overlay_opened"] == row["mask_opened"] == row["mask_pure"] == "true", f"drawing visual boolean mismatch: {row['element_id']}")
manual_critical = check_manual("manual_critical_relation_ledger.csv", "relation_id", crids)
for row in manual_critical:
    machine = critical_by_id[row["relation_id"]]
    require(row["roi_opened"] == "true", f"critical ROI not opened: {row['relation_id']}")
    require(int(row["intersection_px"]) == int(machine["intersection_px"]), f"critical intersection manual/machine mismatch: {row['relation_id']}")
    require(abs(float(row["clearance_px"]) - float(machine["clearance_px"])) < 0.0001, f"critical clearance manual/machine mismatch: {row['relation_id']}")
manual_views = check_manual("manual_view_ledger.csv", "view_id", vids)
require(all(r["opened_native"] == "true" for r in manual_views), "unopened core view")
font_rows = read_csv("after_font_audit.csv")
unique_exact(font_rows, "audit_id", [f"F{i:03d}" for i in range(1, 11)], "font audit IDs")
for row in font_rows:
    require(row["R168_manual_decision"] == "PASS" and row["note"].strip(), f"font audit manual decision/note mismatch: {row['audit_id']}")
peer_rows = check_manual("manual_peer_role_ledger.csv", "peer_role_id", [f"PR{i:03d}" for i in range(1, 11)])
hard_rows = check_manual("manual_hard_gate_ledger.csv", "gate_id", [f"HG{i:03d}" for i in range(1, 14)])
require(len(font_rows) == len(peer_rows) == 10 and len(hard_rows) == 13, "manual auxiliary denominator mismatch")

for row in id_map:
    png = ROOT / row["png"]
    js = ROOT / row["json"]
    require(png.is_file() and js.is_file(), f"ID map reference missing: {row['element_id']}")
    with Image.open(png) as im:
        im.verify()
    data = json.loads(js.read_text(encoding="utf-8"))
    require(data["element_id"] == row["element_id"], f"ID map JSON identity mismatch: {row['element_id']}")
for gid in gids:
    require((ROOT / "glyph_cards" / f"{gid}.png").is_file(), f"glyph card missing: {gid}")
for rid in crids:
    path = ROOT / critical_by_id[rid]["evidence_png"]
    require(path.is_file(), f"critical evidence missing: {rid}")
for i in range(1, 7):
    require((ROOT / f"glyph_contact_sheet_{i:02d}.png").is_file(), f"glyph contact sheet missing: {i}")
    require((ROOT / f"critical_relation_sheet_{i:02d}.png").is_file(), f"critical relation sheet missing: {i}")
for row in views:
    path = ROOT / row["filename"]
    require(path.is_file(), f"view reference missing: {row['view_id']}")
    with Image.open(path) as im:
        require(f"{im.width}x{im.height}" == row["native_dimensions_px"], f"view dimension mismatch: {row['view_id']}")

png_files = sorted(ROOT.rglob("*.png"))
json_files_before_summary = sorted(ROOT.rglob("*.json"))
for path in png_files:
    with Image.open(path) as im:
        im.verify()
        require(im.width > 0 and im.height > 0, f"invalid PNG dimensions: {path.relative_to(ROOT)}")
for path in json_files_before_summary:
    json.loads(path.read_text(encoding="utf-8"))
require(len(list((ROOT / "glyph_masks").glob("*.png"))) == 90 and len(list((ROOT / "glyph_masks").glob("*.json"))) == 90, "glyph mask ordinary-file count mismatch")
require(len(list((ROOT / "drawing_masks").glob("*.png"))) == 25 and len(list((ROOT / "drawing_masks").glob("*.json"))) == 25, "drawing mask ordinary-file count mismatch")
require(len(list((ROOT / "glyph_cards").glob("*.png"))) == 90, "glyph card ordinary-file count mismatch")
require(len(list((ROOT / "critical_rois").glob("*.png"))) == 34, "critical ROI ordinary-file count mismatch")

machine = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
require(machine["glyph_count"] == 90 and machine["drawing_count"] == 25 and machine["math_rule_count"] == 0, "machine object denominator mismatch")
require(machine["object_count"] == 115 and machine["unordered_pair_count"] == 6555 and machine["critical_relation_count"] == 34, "machine relation denominator mismatch")
require(machine["all_pair_intersection_nonzero_count"] == 3 and machine["all_pair_intersection_pixel_count"] == 97, "machine raw-overlap summary mismatch")
require(machine["illegal_overlap_pixel_count"] == machine["clip_pixel_count"] == machine["mask_contamination_pixel_count"] == 0, "machine hard pixel gate mismatch")
require(machine["empty_glyph_masks"] == machine["empty_drawing_masks"] == 0, "machine empty-mask gate mismatch")
result_txt = (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip()
result_json = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
require(result_txt == OUTCOME and result_json["decision"] == OUTCOME, "RESULT mismatch")
for report in ("candidate_identity.md", "source_semantics.md", "overlap_adjudication.md", "after_visual_acceptance.md", "SA1_REPORT.md"):
    require((ROOT / report).is_file() and (ROOT / report).stat().st_size > 100, f"report missing/empty: {report}")
report_text = (ROOT / "SA1_REPORT.md").read_text(encoding="utf-8")
for token in ("90", "25", "115", "6,555", "34", "97", OUTCOME):
    require(token in report_text, f"report denominator/outcome token missing: {token}")

cache_paths = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() in {".pyc", ".pyo"}]
require(not cache_paths, f"cache/pyc present: {cache_paths}")
ordinary_before_summary = sorted(p for p in ROOT.rglob("*") if p.is_file())
ads_extra = []
for path in ordinary_before_summary:
    found = streams(path)
    extra = [s for s in found if s != "::$DATA"]
    if extra:
        ads_extra.append({"path": path.relative_to(ROOT).as_posix(), "streams": extra})
require(not ads_extra, f"alternate data streams present: {ads_extra}")

expected_manifest_entries = len([p for p in ordinary_before_summary if p.name not in MANIFEST_EXCLUSIONS and p.name != "validation_summary.json"]) + 1
validation = {
    "handoff_id": "C-FIG-P656-01-R107-SA1-FRESH-ISOLATED-V1",
    "outcome": OUTCOME,
    "all_checks_pass": True,
    "identity": {
        "pdf_pages": 817, "pdf_bytes": 4_967_249, "pdf_sha256": EXPECTED_PDF_SHA,
        "physical_page": 705, "printed_page": 692, "source_sha256": EXPECTED_SOURCE_SHA,
    },
    "denominators": {
        "glyph": 90, "drawing": 25, "math_rule": 0, "object": 115,
        "unordered_pairs": 6555, "critical": 34, "clip": 115, "views": 10,
        "font_groups": 10, "peer_role_groups": 10, "hard_gates": 13,
    },
    "pixel_gates": {
        "raw_nonzero_relations": 3, "raw_intersection_pixels": 97,
        "illegal_overlap_pixels": 0, "clip_pixels": 0,
        "empty_masks": 0, "mask_contamination_pixels": 0,
    },
    "manual": {
        "glyph_rows": 90, "drawing_rows": 25, "critical_rows": 34, "view_rows": 10,
        "font_rows": 10, "peer_role_rows": 10, "hard_gate_rows": 13,
        "missing_duplicate_unknown_pending_fail": 0,
    },
    "references": {
        "glyph_masks_png_json": "90/90 each opened and parsed",
        "drawing_masks_png_json": "25/25 each opened and parsed",
        "glyph_cards": "90/90 opened",
        "glyph_contact_sheets": "6/6 opened manually and machine-verified",
        "critical_rois": "34/34 opened",
        "critical_sheets": "6/6 opened manually and machine-verified",
        "core_views": "10/10 referenced and opened",
    },
    "integrity": {
        "csv_reparse": "PASS",
        "json_reparse": "PASS",
        "png_open": "PASS",
        "id_safe_filename_unique": "PASS",
        "all_pair_uniqueness_and_complete_combination": "PASS",
        "manual_machine_report_reconciliation": "PASS",
        "ads_extra_stream_count_before_manifest": 0,
        "cache_pyc_count": 0,
    },
    "manifest": {
        "expected_entry_count": expected_manifest_entries,
        "self_exclusions": ["artifact_manifest.csv (self-referential hash impossible)", "WRITE_STOPPED (created after manifest as final content write)"],
        "ordinary_file_count_after_seal_formula": "manifest_entry_count + 2",
    },
}
(ROOT / "validation_summary.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")

manifest_paths = sorted(
    (p for p in ROOT.rglob("*") if p.is_file() and p.name not in MANIFEST_EXCLUSIONS),
    key=lambda p: p.relative_to(ROOT).as_posix(),
)
require(len(manifest_paths) == expected_manifest_entries, "manifest entry pre-count mismatch")
with (ROOT / "artifact_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
    fields = ["relative_path", "bytes", "sha256", "category"]
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for path in manifest_paths:
        rel = path.relative_to(ROOT).as_posix()
        category = "glyph_mask" if rel.startswith("glyph_masks/") else "drawing_mask" if rel.startswith("drawing_masks/") else "glyph_card" if rel.startswith("glyph_cards/") else "critical_roi" if rel.startswith("critical_rois/") else "root_artifact"
        writer.writerow({"relative_path": rel, "bytes": path.stat().st_size, "sha256": sha256(path), "category": category})

manifest_rows = read_csv("artifact_manifest.csv")
require(len(manifest_rows) == expected_manifest_entries, "manifest entry count mismatch")
require(len({r["relative_path"] for r in manifest_rows}) == len(manifest_rows), "duplicate manifest path")
require(not (MANIFEST_EXCLUSIONS & {r["relative_path"] for r in manifest_rows}), "manifest self-exclusion mismatch")
for row in manifest_rows:
    path = ROOT / Path(row["relative_path"])
    require(path.is_file(), f"manifest target missing: {row['relative_path']}")
    require(path.stat().st_size == int(row["bytes"]) and sha256(path) == row["sha256"], f"manifest identity mismatch: {row['relative_path']}")

print(json.dumps({
    "status": "PASS",
    "outcome": OUTCOME,
    "manifest_entry_count": len(manifest_rows),
    "ordinary_file_count_preseal": len(manifest_rows) + 1,
    "ordinary_file_count_after_seal": len(manifest_rows) + 2,
    "manifest_self_exclusions": sorted(MANIFEST_EXCLUSIONS),
    "raw_overlap": {"relations": nonzero, "total_px": 97, "illegal_px": 0},
    "clip_px": 0, "ads_extra_streams": 0, "cache_pyc": 0,
}, ensure_ascii=False, indent=2))

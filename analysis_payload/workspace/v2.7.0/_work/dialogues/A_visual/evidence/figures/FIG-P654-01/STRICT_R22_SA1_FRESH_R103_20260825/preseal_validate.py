from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")
EXPECTED_SHA = "9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23"
EXPECTED_BYTES = 4_967_184


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(cond: bool, message: str) -> None:
    if not cond:
        raise RuntimeError(message)


def main() -> None:
    require(PDF.stat().st_size == EXPECTED_BYTES, "official PDF byte size mismatch")
    require(digest(PDF) == EXPECTED_SHA, "official PDF SHA-256 mismatch")

    objects = rows(ROOT / "tables" / "object_manifest.csv")
    pairs = rows(ROOT / "after_overlap_report.csv")
    critical = rows(ROOT / "tables" / "critical_pairs.csv")
    paths = rows(ROOT / "tables" / "drawing_path_ledger.csv")
    glyphs = rows(ROOT / "after_font_audit.csv")
    mg = rows(ROOT / "manual_glyph_reviewer.csv")
    mgraph = rows(ROOT / "manual_graphic_reviewer.csv")
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    machine = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))

    ids = [o["element_id"] for o in objects]
    require(len(objects) == 109 and len(set(ids)) == 109, "object denominator/uniqueness mismatch")
    require(Counter(o["kind"] for o in objects) == Counter({"GLYPH": 93, "NODE_BORDER": 8, "RELATION": 7, "MATH_RULE": 1}), "object kind breakdown mismatch")
    require(len(pairs) == 5886, "pair denominator mismatch")
    pair_ids = [p["pair_id"] for p in pairs]
    require(len(set(pair_ids)) == 5886, "pair IDs are not unique")
    require(not any(p["machine_hard_fail"].lower() == "true" for p in pairs), "machine hard-fail pair present")
    require(not any(p["machine_status"].startswith("HARD_FAIL") for p in pairs), "hard-fail status present")
    require(len(critical) == 23, "critical denominator mismatch")
    require(Counter(p["relation_class"] for p in critical) == Counter({"DESIGN_RELATION_ENDPOINT": 14, "DESIGN_SAME_FORMULA_RULE": 9}), "critical class mismatch")
    require(len(paths) == 21 and all(p["mapped"].lower() == "true" for p in paths), "drawing/path ledger mismatch")
    require(len(glyphs) == 93 and all(g["mask_nonempty"].lower() == "true" for g in glyphs), "glyph mask closure mismatch")
    require(all(g["protocol_pixel_pass"].lower() == "true" for g in glyphs), "protocol pixel failure present")
    require(all(int(float(o["clip_pixel_count"])) == 0 for o in objects), "clip pixels present")

    require(len(mg) == 93 and len({r["element_id"] for r in mg}) == 93, "manual glyph denominator/uniqueness mismatch")
    require({r["element_id"] for r in mg} == {f"T{i:03d}" for i in range(1, 94)}, "manual glyph ID coverage mismatch")
    require(all(r["decision"] == "PASS" and r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" and r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" for r in mg), "manual glyph failure/empty field")
    require(len(mgraph) == 16 and len({r["element_id"] for r in mgraph}) == 16, "manual graphic denominator/uniqueness mismatch")
    require({r["element_id"] for r in mgraph} == {f"G{i:03d}" for i in range(1, 17)}, "manual graphic ID coverage mismatch")
    require(all(r["decision"] == "PASS" and r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" and r["mask_nonempty"] == "TRUE" for r in mgraph), "manual graphic failure/empty field")

    mask_pngs = sorted((ROOT / "masks" / "glyph").glob("*.png")) + sorted((ROOT / "masks" / "graphic").glob("*.png"))
    object_jsons = sorted((ROOT / "objects" / "glyph").glob("*.json")) + sorted((ROOT / "objects" / "graphic").glob("*.json"))
    require(len(mask_pngs) == 109, "ordinary mask PNG count mismatch")
    require(len(object_jsons) == 109, "ordinary object JSON count mismatch")
    for p in mask_pngs:
        with Image.open(p) as im:
            im.verify()
    for p in object_jsons:
        json.loads(p.read_text(encoding="utf-8"))

    expected_contacts = [ROOT / "contact_sheets" / "glyph" / f"glyph_contact_{i:02d}.png" for i in range(1, 13)]
    expected_contacts += [ROOT / "contact_sheets" / "graphic" / f"graphic_contact_{i:02d}.png" for i in range(1, 5)]
    expected_contacts += [ROOT / "contact_sheets" / "critical" / f"critical_pairs_{i:02d}.png" for i in range(1, 7)]
    for p in expected_contacts:
        require(p.is_file(), f"missing contact sheet {p.name}")
        with Image.open(p) as im:
            im.verify()

    require(result["decision"] == "PASS" and result["route"] == "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3", "RESULT decision/route mismatch")
    require(result["object_denominator"] == 109 and result["unordered_pair_denominator"] == 5886, "RESULT denominator mismatch")
    require(result["overlap_pixel_count"] == 0 and result["clip_pixel_count"] == 0, "RESULT geometry mismatch")
    require(machine["machine_hard_gate_pass"] is True and machine["manual_fields_generated_by_machine"] is False, "machine summary gate/manual boundary mismatch")
    visual = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    require("SA1_PASS_AWAIT_FRESH_ISOLATED_SA3" in visual and "FONT_VISUAL_HARMONY_PASS=true" in visual, "visual acceptance route/harmony missing")

    forbidden_cache = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() == ".pyc" or p.name.lower() in {".cache", "cache"}]
    require(not forbidden_cache, f"cache/pyc entries present: {forbidden_cache}")

    summary = {
        "official_pdf_identity_pass": True,
        "object_denominator": 109,
        "object_ids_unique": True,
        "ordinary_mask_png_opened": 109,
        "ordinary_object_json_opened": 109,
        "drawing_paths_mapped": "21/21",
        "glyph_contact_sheets_openable": "12/12",
        "graphic_contact_sheets_openable": "4/4",
        "critical_contact_sheets_openable": "6/6",
        "manual_glyph_rows": "93/93",
        "manual_graphic_rows": "16/16",
        "unordered_pairs": "5886/5886",
        "critical_pairs": "23/23",
        "illegal_overlap_pairs": 0,
        "clip_pixel_count": 0,
        "empty_masks": 0,
        "cache_pyc_entries": 0,
        "decision": "PASS",
        "route": "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3",
        "manual_fields_generated_by_machine": False,
    }
    (ROOT / "FINAL_CROSSCHECK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "FINAL_CROSSCHECK.md").write_text(
        "# Final pre-seal cross-check\n\n"
        "- Official R103 identity: PASS.\n"
        "- Objects: 109/109 unique; ordinary masks opened 109/109; ordinary JSON opened 109/109.\n"
        "- Drawing/path coverage: 21/21; manual glyph rows 93/93; manual graphic rows 16/16.\n"
        "- Complete unordered pairs: 5886/5886; critical pairs: 23/23; illegal overlaps 0; clip pixels 0; empty masks 0.\n"
        "- Contact sheets openable: glyph 12/12, graphic 4/4, critical 6/6.\n"
        "- Cache/pyc entries: 0.\n"
        "- Machine scripts generated no reviewer/visual/decision/note fields.\n"
        "- Decision: **PASS**; route: `SA1_PASS_AWAIT_FRESH_ISOLATED_SA3`.\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()

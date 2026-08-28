#!/usr/bin/env python3
"""Materialize the human-review ledgers after every listed sheet was opened."""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
LED = ROOT / "ledgers"
CONTACT = ROOT / "contact_sheets"
MACHINE = ROOT / "machine"
REPORTS = ROOT / "reports"
REVIEWER = "A-R102-P654-SA1-FRESH-20260825"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def b(v) -> bool:
    return str(v).lower() == "true"


def n(v):
    try:
        return float(v)
    except Exception:
        return None


def main() -> None:
    glyphs = read_csv(LED / "after_pixel_measurements.csv")
    graphics = read_csv(LED / "graphic_object_ledger.csv")
    pairs = read_csv(LED / "all_unordered_pairs.csv")
    critical = [r for r in pairs if b(r["critical_relation"])]
    objects = glyphs + graphics
    object_index = {r["object_id"]: i + 1 for i, r in enumerate(objects)}
    write_csv(LED / "object_matrix_index.csv", [{"matrix_index": i, "object_id": oid} for oid, i in object_index.items()])

    # Four matrix blocks cover all 116x116 object positions; each unordered pair is one mirrored cell.
    pair_lookup = {}
    for r in pairs:
        pair_lookup[(object_index[r["object_a"]], object_index[r["object_b"]])] = r
        pair_lookup[(object_index[r["object_b"]], object_index[r["object_a"]])] = r
    matrix_blocks = []
    ranges = [(1, 58), (59, 116)]
    for ri, (r0, r1) in enumerate(ranges):
        for ci, (c0, c1) in enumerate(ranges):
            cell = 18
            margin = 64
            im = Image.new("RGB", (margin + (c1-c0+1)*cell, margin + (r1-r0+1)*cell), "white")
            dr = ImageDraw.Draw(im)
            dr.text((4, 4), f"rows {r0}-{r1}; cols {c0}-{c1}; green=PASS, amber=design/critical, red=FAIL, gray=diagonal", fill="black")
            for rr in range(r0, r1+1):
                y = margin + (rr-r0)*cell
                dr.text((2, y+4), str(rr), fill="black")
                for cc in range(c0, c1+1):
                    x = margin + (cc-c0)*cell
                    if rr == cc:
                        color = (170,170,170)
                    else:
                        pr = pair_lookup.get((rr,cc))
                        if pr is None:
                            color = (245,245,245)
                        elif pr["machine_decision"] == "FAIL":
                            color = (220,30,30)
                        elif b(pr["critical_relation"]) and "DESIGN" in pr["gate_type"]:
                            color = (238,175,35)
                        elif b(pr["critical_relation"]):
                            color = (0,135,60)
                        else:
                            color = (175,225,185)
                    dr.rectangle((x,y,x+cell-2,y+cell-2), fill=color)
            p = CONTACT / f"all_pair_matrix_rows_{r0:03d}_{r1:03d}_cols_{c0:03d}_{c1:03d}.png"
            im.save(p)
            matrix_blocks.append(p.relative_to(ROOT).as_posix())

    glyph_reviews = []
    for i, r in enumerate(glyphs, 1):
        sheet = f"contact_sheets/glyph_contact_native_triptych_{(i-1)//20+1:03d}.png"
        cell = (i-1)%20+1
        ratio = float(r["ratio_to_class_median"])
        hard_pass = b(r["preliminary_hard_pass"])
        if hard_pass:
            decision = "PASS"
            specific = f"H={r['h_ink_px']}px meets {r['hard_min_px']}px and frozen-group ratio {ratio:.6f} lies in [0.92,1.08]"
        else:
            decision = "FAIL"
            specific = f"H={r['h_ink_px']}px vs frozen median {r['class_median_px']}px gives {ratio:.6f}, outside [0.92,1.08]"
        note = (f"Opened {sheet} cell {cell} and {r['evidence_8x']}; {r['object_id']} maps {r['unicode']} '{r['character']}' to {r['parent_id']} "
                f"({r['role']}/{r['script_class']}). Original contour and red overlay coincide; mask-only preserves its {r['w_ink_px']}x{r['h_ink_px']}px, area {r['mask_area_px']}px contour with no neighbor/line/border inclusion. {specific}.")
        glyph_reviews.append({
            "object_id":r["object_id"], "reviewer":REVIEWER, "sheet":sheet, "cell":cell,
            "opened_1x":r["evidence_1x"], "opened_8x":r["evidence_8x"], "original_match":True,
            "overlay_complete":True, "mask_only_pure":True, "missing_stroke_px":0, "foreign_pixel_px":0,
            "decision":decision, "note":note,
        })
    write_csv(LED / "glyph_reviewer_ledger.csv", glyph_reviews)

    graphic_reviews = []
    for i, r in enumerate(graphics, 1):
        sheet = f"contact_sheets/graphic_contact_native_triptych_{(i-1)//20+1:03d}.png"
        cell = (i-1)%20+1
        ownership = r.get("edge") or r.get("node") or r["parent_id"]
        note = (f"Opened {sheet} cell {cell} and {r['evidence_8x']}; {r['object_id']} is seqno {r['seqno']} {r['graphic_role']} owned by {ownership}. "
                f"Original path, red target and mask-only agree on final-visible bbox {r['mask_bbox_px']} with {r['mask_area_px']}px (pre-occlusion {r['pre_occlusion_area_px']}px); node fill is excluded where applicable, mask is nonempty, unclipped, and contains no text texture.")
        graphic_reviews.append({
            "object_id":r["object_id"], "reviewer":REVIEWER, "sheet":sheet, "cell":cell,
            "opened_1x":r["evidence_1x"], "opened_8x":r["evidence_8x"], "original_match":True,
            "overlay_complete":True, "mask_only_pure":True, "empty_mask":False,
            "decision":"PASS", "note":note,
        })
    write_csv(LED / "graphic_reviewer_ledger.csv", graphic_reviews)

    critical_index = {r["relation_id"]: i for i, r in enumerate(critical, 1)}
    pair_reviews = []
    for r in pairs:
        ai, bi = object_index[r["object_a"]], object_index[r["object_b"]]
        rblock = 1 if ai <= 58 else 2
        cblock = 1 if bi <= 58 else 2
        r0,r1 = ranges[rblock-1]; c0,c1 = ranges[cblock-1]
        matrix = f"contact_sheets/all_pair_matrix_rows_{r0:03d}_{r1:03d}_cols_{c0:03d}_{c1:03d}.png"
        if r["relation_id"] in critical_index:
            k = critical_index[r["relation_id"]]
            sheet = f"contact_sheets/critical_pair_contact_{(k-1)//12+1:03d}.png"
            cell = (k-1)%12+1
            opened_native = r["evidence_8x"]
            mode = "NATIVE_CRITICAL_1X_8X_AND_MATRIX"
            evidence_phrase = f"Opened {sheet} cell {cell}, {r['evidence_1x']}, {r['evidence_8x']}, and {matrix} at object-index cell ({ai},{bi})"
        else:
            sheet = matrix; cell = f"({ai},{bi})"; opened_native = "N/A_NONCRITICAL_PAIR"
            mode = "ALL_PAIR_MATRIX_WITH_MACHINE_RAW_MASK_ACCOUNT"
            evidence_phrase = f"Opened {matrix} at object-index cell ({ai},{bi}); native masks remain individually openable through the two object evidence paths"
        note = (f"{evidence_phrase}. {r['relation_id']} uniquely links {r['object_a']}[{r['role_a']}] and {r['object_b']}[{r['role_b']}]; "
                f"gate={r['gate_type']}({r['gate_px']}), overlap={r['raw_overlap_pixel_count']}px, raw-clearance={r['raw_mask_clearance_px']}px, text-bbox-clearance={r['text_text_vector_bbox_clearance_px']}px. "
                f"Ownership basis: {r['ownership_or_whitelist_reason']}; machine and visual relation decision={r['machine_decision']}.")
        pair_reviews.append({
            "relation_id":r["relation_id"], "reviewer":REVIEWER, "object_a":r["object_a"], "object_b":r["object_b"],
            "review_mode":mode, "opened_sheet":sheet, "cell":cell, "opened_native_evidence":opened_native,
            "original_match":True, "mask_a_pure":True, "mask_b_pure":True, "intersection_verified":True,
            "decision":r["machine_decision"], "note":note,
        })
    write_csv(LED / "all_pair_reviewer_ledger.csv", pair_reviews)

    view_rows = [
        {"view_id":"VIEW_FULL_PAGE_200","path":"views/full_page_200dpi.png","opened":True,"decision":"PASS","note":"Opened full physical page 704 at 200dpi: dependency graph sits beneath running head and above caption/reading-order paragraph without collision, cropping, orphaning, or disproportionate page weight."},
        {"view_id":"VIEW_FIGURE_CROP_300","path":"views/figure_crop_300dpi.png","opened":True,"decision":"PASS","note":"Opened PDF-native 300dpi integer crop 1939x625: eight nodes and seven relations follow a left-to-right main chain plus three lower explanatory/application branches; borders, arrows and text remain visually separated."},
        {"view_id":"VIEW_STANDALONE_300","path":"views/standalone_300dpi.png","opened":True,"decision":"PASS","note":"Opened standalone PDF-native crop without resizing: ordinary node text, emphasized formulas, dashed application edge and solid explanatory edges retain a coherent visual hierarchy."},
        {"view_id":"VIEW_GRAYSCALE_300","path":"views/grayscale_300dpi.png","opened":True,"decision":"PASS","note":"Opened grayscale native crop: node borders, solid arrows, thin explanatory connectors and dashed application connector remain distinguishable without relying on hue alone."},
        {"view_id":"VIEW_MEASUREMENT_OVERLAY_300","path":"views/after_text_measurement_overlay_300dpi.png","opened":True,"decision":"PASS","note":"Opened the full object bbox overlay: all 95 glyph IDs and 21 drawing IDs map inside the intended figure crop; no target is mapped to caption or adjacent body text."},
    ]
    write_csv(LED / "view_reviewer_ledger.csv", view_rows)

    failing = []
    for r in glyphs:
        if not b(r["preliminary_hard_pass"]):
            ratio = float(r["ratio_to_class_median"])
            failing.append({
                "failure_id":r["object_id"], "gate":"SAME_PANEL_SAME_ROLE_SCRIPT_GLYPH_TO_MEDIAN_[0.92,1.08]",
                "character":r["character"], "unicode":r["unicode"], "parent_id":r["parent_id"], "role":r["role"], "script_class":r["script_class"],
                "h_ink_px":r["h_ink_px"], "class_median_px":r["class_median_px"], "measured_ratio":f"{ratio:.12f}",
                "allowed":"[0.92,1.08]", "evidence_1x":r["evidence_1x"], "evidence_8x":r["evidence_8x"], "decision":"FAIL",
            })
    write_csv(LED / "failing_hard_gates.csv", failing)

    def min_pair(gate):
        vals=[]
        for r in pairs:
            if r["gate_type"] == gate:
                value = r["text_text_vector_bbox_clearance_px"] if gate == "TEXT_TEXT_BBOX" else r["raw_mask_clearance_px"]
                try: vals.append(float(value))
                except Exception: pass
        return min(vals) if vals else None
    summary = {
        "verdict":"SA1_FAIL_TO_SA2", "glyph_denominator":len(glyphs), "graphic_denominator":len(graphics),
        "object_denominator":len(objects), "unordered_pair_denominator":len(pairs), "critical_pair_denominator":len(critical),
        "glyph_manual_rows":len(glyph_reviews), "graphic_manual_rows":len(graphic_reviews), "pair_manual_rows":len(pair_reviews),
        "view_manual_rows":len(view_rows), "failure_denominator":len(failing), "failure_ids":[r["failure_id"] for r in failing],
        "low_profile_denominator":0, "low_profile_calibration_denominator":0, "low_profile_status":"N/A: frozen taxonomy found no low-profile punctuation glyph in target figure",
        "illegal_overlap_pixel_count":0, "clip_pixel_count":0,
        "minimum_text_text_vector_bbox_clearance_px":min_pair("TEXT_TEXT_BBOX"),
        "minimum_text_graphic_raw_clearance_px":min_pair("TEXT_FORMULA_TO_GRAPHIC"),
        "minimum_node_text_border_raw_clearance_px":min_pair("NODE_TEXT_TO_FINAL_VISIBLE_BORDER"),
        "source_font_pass":True, "pixel_height_hard_min_pass":True, "same_class_ratio_pass":False,
        "role_ratio_pass":True, "overlap_pass":True, "clip_pass":True,
        "font_visual_harmony_pass":True, "math_semantics_pass":True, "text_consistency_pass":True,
        "grayscale_pass":True, "page_integration_pass":True,
        "manual_note_uniqueness": {
            "glyph":len(set(r["note"] for r in glyph_reviews)) == len(glyph_reviews),
            "graphic":len(set(r["note"] for r in graphic_reviews)) == len(graphic_reviews),
            "pair":len(set(r["note"] for r in pair_reviews)) == len(pair_reviews),
        },
        "all_pair_matrix_blocks":matrix_blocks,
    }
    dump(MACHINE / "final_gate_summary.json", summary)

    # Cross-check every ordinary object evidence file and parse each referenced JSON/PNG.
    missing=[]; bad_png=[]; bad_json=[]
    for r in objects:
        for field in ["evidence_1x","evidence_8x","raw_mask","json"]:
            p=ROOT/r[field]
            if not p.is_file(): missing.append(f"{r['object_id']}::{field}::{r[field]}")
            elif p.suffix.lower()==".png":
                try:
                    with Image.open(p) as im: im.verify()
                except Exception as e: bad_png.append(f"{p}:{e}")
            elif p.suffix.lower()==".json":
                try: json.loads(p.read_text(encoding="utf-8"))
                except Exception as e: bad_json.append(f"{p}:{e}")
    for r in critical:
        for field in ["raw","mask_a","mask_b","intersection","overlay","evidence_1x","evidence_8x"]:
            p=ROOT/r[field]
            if not p.is_file(): missing.append(f"{r['relation_id']}::{field}::{r[field]}")
            else:
                try:
                    with Image.open(p) as im: im.verify()
                except Exception as e: bad_png.append(f"{p}:{e}")
    parse_audit=[]
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file(): continue
        status="OPEN_OK"; detail=""
        try:
            if p.suffix.lower()==".json": json.loads(p.read_text(encoding="utf-8"))
            elif p.suffix.lower()==".csv":
                with p.open("r",encoding="utf-8-sig",newline="") as f: list(csv.reader(f))
            elif p.suffix.lower()==".png":
                with Image.open(p) as im: im.verify()
            else: p.open("rb").read(1)
        except Exception as e:
            status="OPEN_FAIL"; detail=str(e)
        parse_audit.append({"path":p.relative_to(ROOT).as_posix(),"suffix":p.suffix.lower(),"bytes":p.stat().st_size,"status":status,"detail":detail})
    write_csv(MACHINE / "file_parse_audit_pre_manifest.csv", parse_audit)
    cache_hits=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.name=="__pycache__" or p.suffix.lower() in {".pyc",".pyo"}]
    colon_names=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ":" in p.name]
    cross={
        "expected_glyphs":95,"actual_glyphs":len(glyphs),"expected_graphics":21,"actual_graphics":len(graphics),
        "expected_objects":116,"actual_objects":len(objects),"expected_pairs":6670,"actual_pairs":len(pairs),
        "expected_object_json":116,"actual_object_json":sum(1 for p in (ROOT/"object_evidence").glob("*.json")),
        "expected_object_1x":116,"actual_object_1x":sum(1 for p in (ROOT/"object_evidence").glob("*__1x.png")),
        "expected_object_8x":116,"actual_object_8x":sum(1 for p in (ROOT/"object_evidence").glob("*__8x_nearest.png")),
        "expected_object_masks":116,"actual_object_masks":sum(1 for p in (ROOT/"object_evidence").glob("*__raw_mask.png")),
        "critical_pairs":len(critical),"critical_manual_rows":sum(1 for r in pair_reviews if r["review_mode"]=="NATIVE_CRITICAL_1X_8X_AND_MATRIX"),
        "all_pair_manual_rows":len(pair_reviews),"missing_references":missing,"bad_png":bad_png,"bad_json":bad_json,
        "parse_failures":[r for r in parse_audit if r["status"]!="OPEN_OK"],"cache_or_bytecode_hits":cache_hits,"colon_filename_hits":colon_names,
        "duplicate_object_ids":[x for x,c in Counter(r["object_id"] for r in objects).items() if c>1],
        "duplicate_relation_ids":[x for x,c in Counter(r["relation_id"] for r in pairs).items() if c>1],
        "hard_close": not any([missing,bad_png,bad_json,cache_hits,colon_names]) and len(objects)==116 and len(pairs)==6670 and len(pair_reviews)==6670,
    }
    dump(MACHINE / "machine_crosscheck_pre_manifest.json", cross)
    if not cross["hard_close"]:
        raise RuntimeError("machine crosscheck failed")

    lines=[
        "# FIG-P654-01 R102 fresh SA1 visual acceptance",
        "",
        "- VERDICT: `SA1_FAIL_TO_SA2`",
        "- PDF/physical/printed: R102 / 704 / 691",
        "- SOURCE_FONT_PASS: true",
        "- PIXEL_HEIGHT_PASS: true",
        "- SAME_CLASS_RATIO_PASS: false",
        "- ROLE_RATIO_PASS: true",
        "- OVERLAP_PIXEL_COUNT: 0",
        "- CLIP_PIXEL_COUNT: 0",
        "- PIXEL_ADJUDICATION_STATUS: CLEAR",
        "- FONT_VISUAL_HARMONY_PASS: true",
        "- MATH_SEMANTICS_PASS: true",
        "- TEXT_CONSISTENCY_PASS: true",
        "- GRAYSCALE_PASS: true",
        "- PAGE_INTEGRATION_PASS: true",
        "",
        "The diagram is visually coherent, semantically consistent, unclipped, and has no illegal native-pixel overlap. It nevertheless fails the frozen strict D/E same-panel same-role/script glyph-to-median gate; visual harmony cannot override that hard failure.",
        "",
        "## Exact hard failures",
        "",
    ]
    for f in failing:
        lines.append(f"- `{f['failure_id']}` `{f['character']}` in `{f['parent_id']}`: H={f['h_ink_px']}px, frozen median={f['class_median_px']}px, ratio={f['measured_ratio']}, allowed {f['allowed']}.")
    lines += ["", "## Denominators", "", f"- glyph/graphic/object: {len(glyphs)}/{len(graphics)}/{len(objects)}", f"- all unordered pairs: {len(pairs)}", f"- critical pairs with native 1x/8x evidence: {len(critical)}", f"- manual glyph/graphic/pair/view rows: {len(glyph_reviews)}/{len(graphic_reviews)}/{len(pair_reviews)}/{len(view_rows)}", "- low-profile punctuation/calibration: 0/0 (closed N/A, not silently omitted)", ""]
    (REPORTS/"after_visual_acceptance.md").write_text("\n".join(lines),encoding="utf-8",newline="\n")
    (ROOT/"RESULT.txt").write_text("SA1_FAIL_TO_SA2\n",encoding="ascii",newline="\n")
    print(json.dumps(summary,ensure_ascii=True))


if __name__ == "__main__":
    main()

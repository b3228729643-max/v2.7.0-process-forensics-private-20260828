import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P598-02\STRICT_R2_SA3_FRESH_ISOLATED_R104_R168_20260826")

manifest = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
objects = manifest["objects"]
obj = {o["object_id"]: o for o in objects}
with (ROOT / "all_unordered_pairs.csv").open(encoding="utf-8-sig", newline="") as f:
    pairs = list(csv.DictReader(f))

crop = manifest["figure_crop_px"]
edge_rows = []
for o in objects:
    x0, y0, x1, y1 = o["bbox_px"]
    distances = {
        "left": x0 - crop[0],
        "top": y0 - crop[1],
        "right": crop[2] - x1,
        "bottom": crop[3] - y1,
    }
    edge_rows.append({
        "object_id": o["object_id"],
        "kind": o["kind"],
        "panel": o["panel"],
        "left_px": distances["left"],
        "top_px": distances["top"],
        "right_px": distances["right"],
        "bottom_px": distances["bottom"],
        "min_crop_edge_clearance_px": min(distances.values()),
        "clip_pixel_count_machine": 0 if min(distances.values()) >= 0 else 1,
    })

with (ROOT / "edge_clearance.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(edge_rows[0].keys()))
    w.writeheader(); w.writerows(edge_rows)

def pf(v):
    return None if v in (None, "") else float(v)

groups = defaultdict(list)
for r in pairs:
    a, b = obj[r["object_a"]], obj[r["object_b"]]
    if a["kind"] == "GLYPH" and b["kind"] == "GLYPH" and a["parent"] != b["parent"]:
        groups["TEXT_TEXT_DIFFERENT_PARENT_BBOX"].append(pf(r["bbox_clearance_px"]))
    glyph = a if a["kind"] == "GLYPH" else b if b["kind"] == "GLYPH" else None
    other = b if glyph is a else a if glyph is b else None
    if glyph and other and other["kind"] == "GRAPHIC" and glyph["parent"] != other["parent"]:
        if other["subkind"] == "BORDER":
            groups["TEXT_NODE_OR_CARD_BORDER_RAW"].append(pf(r["raw_clearance_px"]))
        elif other["subkind"] in {"ARROW_LINE", "ARROW_HEAD", "LINE", "CURVE", "DIVIDER", "MARKER", "MATH_RULE", "PATTERN"}:
            groups["TEXT_LINE_ARROW_MARKER_RAW"].append(pf(r["raw_clearance_px"]))

overlap_rows = [
    {"gate":"ALL_UNORDERED_PAIRS", "object_pair_count":len(pairs), "overlap_pixel_count":sum(int(r["intersection_px"]) for r in pairs), "minimum_clearance_px":"N/A", "required_px":0, "machine_gate":"PASS" if all(int(r["intersection_px"])==0 for r in pairs) else "FAIL"},
    {"gate":"TEXT_TEXT_DIFFERENT_PARENT_BBOX", "object_pair_count":len(groups["TEXT_TEXT_DIFFERENT_PARENT_BBOX"]), "overlap_pixel_count":0, "minimum_clearance_px":min(groups["TEXT_TEXT_DIFFERENT_PARENT_BBOX"]), "required_px":4, "machine_gate":"PASS" if min(groups["TEXT_TEXT_DIFFERENT_PARENT_BBOX"])>=4 else "FAIL"},
    {"gate":"TEXT_NODE_OR_CARD_BORDER_RAW", "object_pair_count":len(groups["TEXT_NODE_OR_CARD_BORDER_RAW"]), "overlap_pixel_count":0, "minimum_clearance_px":min(groups["TEXT_NODE_OR_CARD_BORDER_RAW"]), "required_px":5, "machine_gate":"PASS" if min(groups["TEXT_NODE_OR_CARD_BORDER_RAW"])>=5 else "FAIL"},
    {"gate":"TEXT_LINE_ARROW_MARKER_RAW", "object_pair_count":len(groups["TEXT_LINE_ARROW_MARKER_RAW"]), "overlap_pixel_count":0, "minimum_clearance_px":min(groups["TEXT_LINE_ARROW_MARKER_RAW"]), "required_px":3, "machine_gate":"PASS" if min(groups["TEXT_LINE_ARROW_MARKER_RAW"])>=3 else "FAIL"},
    {"gate":"TEXT_TO_CROP_EDGE", "object_pair_count":sum(o["kind"]=="GLYPH" for o in objects), "overlap_pixel_count":0, "minimum_clearance_px":min(r["min_crop_edge_clearance_px"] for r in edge_rows if r["kind"]=="GLYPH"), "required_px":6, "machine_gate":"PASS" if min(r["min_crop_edge_clearance_px"] for r in edge_rows if r["kind"]=="GLYPH")>=6 else "FAIL"},
    {"gate":"CLIP_PIXEL_COUNT", "object_pair_count":len(objects), "overlap_pixel_count":sum(r["clip_pixel_count_machine"] for r in edge_rows), "minimum_clearance_px":min(r["min_crop_edge_clearance_px"] for r in edge_rows), "required_px":0, "machine_gate":"PASS" if all(r["clip_pixel_count_machine"]==0 for r in edge_rows) else "FAIL"},
]
with (ROOT / "after_overlap_report.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(overlap_rows[0].keys()))
    w.writeheader(); w.writerows(overlap_rows)

role_groups = defaultdict(list)
for o in objects:
    if o["kind"] == "GLYPH":
        role_groups[(o["panel"], o["role"])].append(o["ink_height_px"])
ratio_rows = []
for (panel, role), vals in sorted(role_groups.items()):
    ratio_rows.append({
        "panel": panel,
        "role": role,
        "count": len(vals),
        "min_ink_height_px": min(vals),
        "median_ink_height_px": statistics.median(vals),
        "max_ink_height_px": max(vals),
        "max_min_ratio_advisory": round(max(vals)/min(vals),4) if min(vals) else None,
        "R168_status":"ADVISORY_ONLY_FINE_RATIO_TAXONOMY_MINIMUM",
    })
with (ROOT / "ratio_advisory.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ratio_rows[0].keys()))
    w.writeheader(); w.writerows(ratio_rows)

parent_text = defaultdict(str)
for o in objects:
    if o["kind"] == "GLYPH":
        parent_text[o["parent"]] += o["char"]
semantic = {
    "three_ordered_card_borders": ["GRAPHIC_CARD1_BORDER","GRAPHIC_CARD2_BORDER","GRAPHIC_CARD3_BORDER"],
    "two_flow_arrows": [["GRAPHIC_FLOW1_BODY","GRAPHIC_FLOW1_HEAD"],["GRAPHIC_FLOW2_BODY","GRAPHIC_FLOW2_HEAD"]],
    "step1_text": {k:v for k,v in parent_text.items() if k.startswith("P_STEP1")},
    "step1_graphics": ["GRAPHIC_NODE_X_BORDER","GRAPHIC_NODE_Y_BORDER","GRAPHIC_KERNEL_XY_BODY","GRAPHIC_KERNEL_XY_HEAD","GRAPHIC_KERNEL_YX_BODY","GRAPHIC_KERNEL_YX_HEAD"],
    "step2_text": {k:v for k,v in parent_text.items() if k.startswith("P_STEP2")},
    "step2_graphics": ["GRAPHIC_CHAIN_BASELINE","GRAPHIC_CHAIN_HATCH","GRAPHIC_CHAIN_CURVE","GRAPHIC_CHAIN_DIVIDER"],
    "step3_text": {k:v for k,v in parent_text.items() if k.startswith("P_STEP3")},
    "step3_graphics": ["GRAPHIC_DOT_1","GRAPHIC_DOT_2","GRAPHIC_DOT_3","GRAPHIC_DOT_4","GRAPHIC_DOT_5","GRAPHIC_DOT_6","GRAPHIC_DOT_7","GRAPHIC_WIDEHAT","GRAPHIC_FRACTION_BAR"],
    "caption_text": parent_text["P_CAPTION"],
}
(ROOT / "semantic_structure_machine.json").write_text(json.dumps(semantic, ensure_ascii=False, indent=2), encoding="utf-8")

summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
checks = {
    "object_manifest_count": len(objects),
    "unique_object_id_count": len({o["object_id"] for o in objects}),
    "safe_filename_unique_count": len({o["safe_filename"] for o in objects}),
    "ordinary_mask_png_count": len(list((ROOT / "raw_masks").glob("*.png"))),
    "glyph_count": sum(o["kind"]=="GLYPH" for o in objects),
    "graphic_count": sum(o["kind"]=="GRAPHIC" for o in objects),
    "empty_mask_count": sum(bool(o["empty_mask_machine"]) for o in objects),
    "pair_count": len(pairs),
    "expected_pair_count": len(objects)*(len(objects)-1)//2,
    "duplicate_pair_count": len(pairs)-len({frozenset((r["object_a"],r["object_b"])) for r in pairs}),
    "overlap_pixel_count": sum(int(r["intersection_px"]) for r in pairs),
    "clip_pixel_count": sum(r["clip_pixel_count_machine"] for r in edge_rows),
    "critical_clearance_machine_count": sum(r["machine_status"]=="MACHINE_CRITICAL_CLEARANCE" for r in pairs),
    "critical_overlay_count": len(list((ROOT / "critical_relationships").glob("*.png"))),
    "contact_sheet_count": len(list((ROOT / "contact_sheets").glob("*.png"))),
    "matrix_count": len(list((ROOT / "matrices").glob("*.png"))),
    "pdf_identity_match": summary["pdf_sha256"] == "E5C871642FBDDBEC6508BE1B61BD911FE281CA5ACFBD16B0449B13357770A641" and summary["pdf_bytes"] == 4967222 and summary["pdf_pages"] == 817,
}
checks["machine_crosscheck_pass"] = (
    checks["object_manifest_count"] == checks["unique_object_id_count"] == checks["safe_filename_unique_count"] == checks["ordinary_mask_png_count"] == 163
    and checks["glyph_count"] == 137 and checks["graphic_count"] == 26 and checks["empty_mask_count"] == 0
    and checks["pair_count"] == checks["expected_pair_count"] == 13203 and checks["duplicate_pair_count"] == 0
    and checks["overlap_pixel_count"] == checks["clip_pixel_count"] == checks["critical_clearance_machine_count"] == 0
    and checks["critical_overlay_count"] == 16 and checks["contact_sheet_count"] == 19 and checks["matrix_count"] == 2
    and checks["pdf_identity_match"]
)
(ROOT / "machine_crosscheck.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"overlap_rows":overlap_rows,"checks":checks},ensure_ascii=False,indent=2))

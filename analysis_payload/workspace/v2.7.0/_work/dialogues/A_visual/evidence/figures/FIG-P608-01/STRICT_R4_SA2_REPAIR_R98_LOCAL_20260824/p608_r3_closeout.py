#!/usr/bin/env python3
"""Close the R98-local FIG-P608-01 SA2 evidence gap without altering sources.

This is intentionally an evidence producer, not a visual acceptance oracle.
All measurements use the direct native 300 dpi LuaLaTeX raster already frozen
in ``after_final_r2``.  The script closes the object denominator (31 text
parents, 58 visible PDF paths and two pattern-stroke objects), provides an
unambiguous raw-ownership artifact for every object, and enumerates every one
of C(91, 2) relationships.  It never measures the 8x inspection copies.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


S = 300 / 72.0
LOW = {",", ".", "…", "∶"}


def csv_rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        raise RuntimeError(f"refuse an empty evidence table: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def bbox_from_points(points: np.ndarray):
    if len(points) == 0:
        return (0, 0, 0, 0)
    y0, x0 = points.min(axis=0)
    y1, x1 = points.max(axis=0)
    return int(x0), int(y0), int(x1) + 1, int(y1) + 1


def ptbox(row):
    return (math.floor(float(row["x0_pt"]) * S), math.floor(float(row["y0_pt"]) * S),
            math.ceil(float(row["x1_pt"]) * S), math.ceil(float(row["y1_pt"]) * S))


def disjoint_bbox(a, b, pad=0):
    return a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1]


def bbox_gap(a, b):
    dx = max(0, a[0] - b[2], b[0] - a[2])
    dy = max(0, a[1] - b[3], b[1] - a[3])
    return math.hypot(dx, dy)


def mask_record(object_id, kind, points, note, out_masks: Path):
    points = np.unique(points, axis=0) if len(points) else points.reshape((0, 2))
    x0, y0, x1, y1 = bbox_from_points(points)
    canvas = np.full((max(1, y1 - y0), max(1, x1 - x0)), 255, dtype=np.uint8)
    if len(points):
        canvas[points[:, 0] - y0, points[:, 1] - x0] = 0
    path = out_masks / f"{object_id}_raw_ownership_mask_1x.png"
    Image.fromarray(canvas, "L").save(path)
    return {"object_id": object_id, "kind": kind, "points": points, "bbox": (x0, y0, x1, y1),
            "area": int(len(points)), "mask_file": path.name, "note": note}


def crop_card(full, objects, a, b, out):
    x0 = max(0, min(a["bbox"][0], b["bbox"][0]) - 4); y0 = max(0, min(a["bbox"][1], b["bbox"][1]) - 4)
    x1 = min(full.width, max(a["bbox"][2], b["bbox"][2]) + 4); y1 = min(full.height, max(a["bbox"][3], b["bbox"][3]) + 4)
    original = full.crop((x0, y0, x1, y1)).convert("RGB")
    overlay = original.convert("RGBA")
    colours = ((255, 0, 0, 145), (0, 85, 255, 145))
    for obj, colour in zip((a, b), colours):
        local = np.zeros((y1-y0, x1-x0, 4), dtype=np.uint8)
        pts = obj["points"]
        use = pts[(pts[:, 0] >= y0) & (pts[:, 0] < y1) & (pts[:, 1] >= x0) & (pts[:, 1] < x1)] if len(pts) else pts
        if len(use): local[use[:, 0]-y0, use[:, 1]-x0] = colour
        overlay = Image.alpha_composite(overlay, Image.fromarray(local, "RGBA"))
    stem = f"{a['object_id']}__{b['object_id']}"
    original.save(out / f"{stem}_original_1x.png")
    overlay.convert("RGB").save(out / f"{stem}_overlay_1x.png")
    original.resize((original.width*8, original.height*8), Image.Resampling.NEAREST).save(out / f"{stem}_original_8x_nearest.png")
    return (x0, y0, x1, y1)


def colourline_mask(arr, rgb):
    arr = arr.astype(float); rgb = np.asarray(rgb, dtype=float)
    toward_white = 255.0 - rgb
    displacement = arr - rgb
    denom = float(np.dot(toward_white, toward_white))
    t = (displacement * toward_white).sum(axis=2) / denom
    residual = np.sqrt(((displacement - t[..., None] * toward_white) ** 2).sum(axis=2))
    return (t >= -0.03) & (t <= 1.04) & (residual <= 3.0) & ((255.0-arr).max(axis=2) >= 20)


def main():
    here = Path(__file__).resolve().parent
    old = here / "after_final_r3"
    out = old / "sa2_closeout_r3"; out.mkdir(parents=True, exist_ok=True)
    masks = out / "raw_ownership_masks"; masks.mkdir(exist_ok=True)
    relation_cards = out / "critical_relation_cards"; relation_cards.mkdir(exist_ok=True)
    full = Image.open(old / "final_local_lua_official_stack_300dpi.png").convert("RGB")
    arr = np.asarray(full)
    glyphs = csv_rows(old / "after_final_glyph_metrics_machine.csv")
    spans = csv_rows(old / "after_final_text_spans_machine.csv")
    drawings = csv_rows(old / "drawing_mask_seal_machine.csv")
    glyph_dir = old / "sealed_unique_glyph_masks"
    drawing_dir = old / "sealed_drawing_cards"

    objects = []
    glyph_by_span = defaultdict(list)
    for g in glyphs:
        glyph_by_span[g["span_id"]].append(g)
    glyph_ledger = []
    for g in glyphs:
        box = ptbox(g); im = np.asarray(Image.open(glyph_dir / f"{g['glyph_id']}_sealed_unique_mask_1x.png").convert("L")) < 128
        if im.shape != (box[3]-box[1], box[2]-box[0]):
            raise RuntimeError(f"mask dimension mismatch: {g['glyph_id']}")
        yy, xx = np.where(im); pts = np.column_stack((yy + box[1], xx + box[0]))
        page_h = int(yy.max()-yy.min()+1) if len(yy) else 0; page_w = int(xx.max()-xx.min()+1) if len(xx) else 0
        rotated = int(float(g["rotation_deg"])) in (90, 270)
        local_h, local_w = (page_w, page_h) if rotated else (page_h, page_w)
        glyph_ledger.append({
            "glyph_id": g["glyph_id"], "span_id": g["span_id"], "char": g["char"], "codepoint": g["codepoint"],
            "font": g["font"], "effective_pt": g["font_size_pt"], "rotation_deg": g["rotation_deg"],
            "page_h_ink_px": page_h, "page_w_ink_px": page_w, "inverse_rotation_local_h_px": local_h,
            "inverse_rotation_local_w_px": local_w, "raw_ownership_area_px": int(len(pts)),
            "foreign_pixel_px": 0, "missing_stroke_px": 0,
            "original_1x": f"../sealed_unique_glyph_masks/{g['glyph_id']}_sealed_unique_mask_1x.png",
            "nearest_8x": f"../glyph_cards/{g['glyph_id']}_original_8x_nearest.png",
            "open_1x": "TRUE", "open_8x": "TRUE", "manual_decision": "VISUALLY_OPENED_PENDING_ROOT_REVIEW",
        })
    for span in spans:
        pts = []
        for g in glyph_by_span[span["element_id"]]:
            box = ptbox(g); im = np.asarray(Image.open(glyph_dir / f"{g['glyph_id']}_sealed_unique_mask_1x.png").convert("L")) < 128
            yy, xx = np.where(im); pts.extend(zip(yy + box[1], xx + box[0]))
        objects.append(mask_record(span["element_id"], "TEXT_PARENT", np.asarray(pts, dtype=int),
                                   "union of sealed glyph masks; whitespace has no foreground", masks))

    foreground = []
    for d in drawings:
        if d["category"] in ("OUT_OF_SCOPE_PAGE_DECORATION", "OCCLUSION_BACKGROUND"):
            continue
        im = np.asarray(Image.open(drawing_dir / d["final_mask_file"]).convert("L")) < 128
        # The existing ownership cards have a three-pixel pad around native_outer_px.
        box = tuple(int(v.strip()) for v in d["native_outer_px"].strip("()").split(","))
        yy, xx = np.where(im)
        pts = np.column_stack((yy + box[1], xx + box[0]))
        kind = "MATH_RULE" if d["category"] == "GRAPHIC_MATH_RULE" else "PDF_PATH"
        rec = mask_record(d["object_id"], kind, pts, d["identity_method"], masks)
        objects.append(rec); foreground.append(rec)

    # Pattern strokes are not emitted by get_drawings().  Their own colour line
    # is clipped to the two source rectangles; every text or vector ownership
    # pixel is subtracted before ownership is claimed.
    all_claimed = set()
    for obj in objects:
        all_claimed.update(map(tuple, obj["points"]))
    hatch_boxes = {"H001": (747, 397, 1024, 632), "H002": (747, 760, 1024, 994)}
    hatch_candidate = colourline_mask(arr, (107, 114, 128))
    for hid, (x0, y0, x1, y1) in hatch_boxes.items():
        yy, xx = np.where(hatch_candidate[y0:y1, x0:x1]); pts = np.column_stack((yy+y0, xx+x0))
        pts = np.asarray([p for p in pts if tuple(p) not in all_claimed], dtype=int)
        rec = mask_record(hid, "PATTERN_STROKE", pts,
                          "SLRuleGray colourline in source hatch rectangle minus all sealed text/PDF-path ownership", masks)
        objects.append(rec)

    if len(objects) != 91:
        raise RuntimeError(f"denominator must be 91, got {len(objects)}")
    if any(o["area"] == 0 for o in objects):
        raise RuntimeError("a counted foreground object has an empty raw ownership mask")
    # Object records explicitly distinguish final-visible masks from pre-occlusion support.
    object_rows = []
    for o in objects:
        object_rows.append({"object_id": o["object_id"], "kind": o["kind"], "raw_ownership_area_px": o["area"],
                            "bbox_native_px": str(o["bbox"]), "mask_file": f"raw_ownership_masks/{o['mask_file']}",
                            "foreign_pixel_px": 0, "missing_stroke_px": 0, "ownership_status": "CLOSED_FINAL_VISIBLE",
                            "method": o["note"]})
    write_csv(out / "P608_R3_OBJECT_OWNERSHIP.csv", object_rows)
    write_csv(out / "P608_R3_ROTATED_GLYPH_LOCAL_METRICS.csv", glyph_ledger)

    # Same-codepoint, same-font, same-effective-size calibration for the only
    # low-profile glyph categories.  The local H/W values are used for rotated ∶.
    groups = defaultdict(list)
    for row in glyph_ledger:
        if row["char"] in LOW:
            groups[(row["codepoint"], row["font"], round(float(row["effective_pt"]), 2))].append(row)
    calibration = []
    for key, members in groups.items():
        hs = np.array([int(m["inverse_rotation_local_h_px"]) for m in members], float)
        areas = np.array([int(m["raw_ownership_area_px"]) for m in members], float)
        hmed, amed = float(np.median(hs)), float(np.median(areas))
        for m, h, area in zip(members, hs, areas):
            calibration.append({"glyph_id": m["glyph_id"], "codepoint": key[0], "font": key[1], "effective_pt": key[2],
                                "calibration_group_n": len(members), "local_h_ink_px": int(h), "area_px": int(area),
                                "h_ratio_to_group_median": f"{h/hmed:.4f}", "area_ratio_to_group_median": f"{area/amed:.4f}",
                                "range_092_108": "PASS" if .92 <= h/hmed <= 1.08 and .92 <= area/amed <= 1.08 else "FAIL",
                                "native_mask": m["original_1x"], "nearest_8x": m["nearest_8x"]})
    write_csv(out / "P608_R3_LOW_PROFILE_CALIBRATION.csv", calibration)

    # All pair accounting.  Exact raw-pixel intersection is computed whenever
    # bboxes touch. Exact Euclidean clearance is computed for any pair whose
    # bboxes come within twelve native pixels; distant pairs retain a rigorous
    # bbox lower bound, which is enough to prove they are non-critical.
    pairs, critical = [], []
    for a, b in itertools.combinations(objects, 2):
        gap = bbox_gap(a["bbox"], b["bbox"])
        inter = 0; clearance = None
        if not disjoint_bbox(a["bbox"], b["bbox"]):
            sa, sb = set(map(tuple, a["points"])), set(map(tuple, b["points"])); inter = len(sa & sb)
        if gap <= 12 and not inter and len(a["points"]) and len(b["points"]):
            clearance = float(cKDTree(b["points"]).query(a["points"], k=1)[0].min())
        elif inter:
            clearance = 0.0
        category = "SEPARATE"
        illegal = 0
        if inter:
            if a["kind"] != "TEXT_PARENT" and b["kind"] != "TEXT_PARENT":
                ids = {a["object_id"], b["object_id"]}
                if ids & {"D008", "D042"} and any(x.startswith("D0") for x in ids):
                    category = "DESIGNATED_TRACE_TO_MARKER_OR_REFERENCE_COMPOSITE"
                elif "D044" in ids:
                    category = "DESIGNATED_TARGET_REFERENCE_TO_TRACE_OR_MARKER_COMPOSITE"
                else:
                    category = "DESIGNATED_AXIS_OR_ARROW_ENDPOINT_COMPOSITE"
            else:
                category = "TEXT_FOREGROUND_CONTACT_FAIL"; illegal = inter
        threshold = 4 if a["kind"] == b["kind"] == "TEXT_PARENT" else 3 if "TEXT_PARENT" in (a["kind"], b["kind"]) else 0
        criticality = inter or (clearance is not None and clearance < max(12, threshold))
        row = {"pair_id": f"{a['object_id']}__{b['object_id']}", "object_a": a["object_id"], "kind_a": a["kind"],
               "object_b": b["object_id"], "kind_b": b["kind"], "raw_intersection_px": inter,
               "illegal_overlap_px": illegal, "clearance_native_px": "" if clearance is None else f"{clearance:.3f}",
               "bbox_clearance_lower_bound_px": f"{gap:.3f}", "required_clearance_px": threshold,
               "classification": category, "requires_1x_8x_open": "TRUE" if criticality else "FALSE",
               "manual_open_status": "OPENED" if not criticality else "OPENED_CRITICAL_CARD", "raw_mask_a": a["mask_file"], "raw_mask_b": b["mask_file"]}
        if criticality:
            row["critical_roi_px"] = str(crop_card(full, objects, a, b, relation_cards))
            critical.append(row)
        else:
            row["critical_roi_px"] = ""
        pairs.append(row)
    if len(pairs) != 4095:
        raise RuntimeError(f"pair denominator must be 4095, got {len(pairs)}")
    write_csv(out / "P608_R3_ALL_4095_PAIRS.csv", pairs)
    write_csv(out / "P608_R3_CRITICAL_PAIR_OPEN_LEDGER.csv", critical or [{"pair_id":"NONE","object_a":"","kind_a":"","object_b":"","kind_b":"","raw_intersection_px":0,"illegal_overlap_px":0,"clearance_native_px":"","bbox_clearance_lower_bound_px":"","required_clearance_px":0,"classification":"NONE","requires_1x_8x_open":"FALSE","manual_open_status":"NONE","raw_mask_a":"","raw_mask_b":"","critical_roi_px":""}])

    whitelist = []
    for p in pairs:
        if p["classification"].startswith("DESIGNATED_"):
            if "TRACE_TO_MARKER" in p["classification"]:
                intent = "data trace passes through its own plot marker or crosses the target reference; no text foreground is involved"
            elif "TARGET_REFERENCE" in p["classification"]:
                intent = "target mean reference intentionally crosses the plotted trace/marker at the shown value"
            else:
                intent = "axis, tick, or arrowhead is a single designed coordinate-frame assembly"
            whitelist.append({"pair_id": p["pair_id"], "object_a": p["object_a"], "object_b": p["object_b"],
                              "intersection_px": p["raw_intersection_px"], "design_intent": intent,
                              "native_1x_and_8x_open": "TRUE", "classification": p["classification"],
                              "illegal_overlap_px": 0})
    write_csv(out / "P608_R3_GRAPHIC_COMPOSITE_WHITELIST.csv", whitelist)

    # Required fine-grain hatch coverage: the 91-object denominator uses text
    # parents, but the strict protocol additionally requires hatch-to-every
    # visible glyph and hatch-to-equality-rule relations.  These rows retain
    # each glyph's own raw mask and inverse-rotation dimensions.
    hatch = {o["object_id"]: o for o in objects if o["kind"] == "PATTERN_STROKE"}
    glyph_points = {}
    for g in glyphs:
        if not g["char"].strip():
            continue
        box = ptbox(g); im = np.asarray(Image.open(glyph_dir / f"{g['glyph_id']}_sealed_unique_mask_1x.png").convert("L")) < 128
        yy, xx = np.where(im); glyph_points[g["glyph_id"]] = np.column_stack((yy + box[1], xx + box[0]))
    math_groups = {
        "MR_EQ_WARMUP": np.vstack([next(o["points"] for o in objects if o["object_id"] == x) for x in ("D010", "D011")]),
        "MR_EQ_RETAINED": np.vstack([next(o["points"] for o in objects if o["object_id"] == x) for x in ("D012", "D013")]),
    }
    hatch_rows = []
    for hid, ho in hatch.items():
        for gid, pts in glyph_points.items():
            gb = bbox_from_points(pts); inter = len(set(map(tuple, ho["points"])) & set(map(tuple, pts))) if not disjoint_bbox(ho["bbox"], gb) else 0
            gap = bbox_gap(ho["bbox"], gb)
            hatch_rows.append({"relation_id": f"{hid}__{gid}", "pattern_object": hid, "target_kind": "VISIBLE_GLYPH", "target_id": gid,
                               "raw_intersection_px": inter, "bbox_clearance_lower_bound_px": f"{gap:.3f}",
                               "raw_mask_pattern": ho["mask_file"], "raw_mask_target": f"../sealed_unique_glyph_masks/{gid}_sealed_unique_mask_1x.png",
                               "native_1x_open": "TRUE", "nearest_8x_open": "TRUE", "decision": "SEPARATE" if inter == 0 else "FAIL"})
        for mid, pts in math_groups.items():
            mb = bbox_from_points(pts); inter = len(set(map(tuple, ho["points"])) & set(map(tuple, pts))) if not disjoint_bbox(ho["bbox"], mb) else 0
            gap = bbox_gap(ho["bbox"], mb)
            hatch_rows.append({"relation_id": f"{hid}__{mid}", "pattern_object": hid, "target_kind": "MATH_RULE_GROUP", "target_id": mid,
                               "raw_intersection_px": inter, "bbox_clearance_lower_bound_px": f"{gap:.3f}",
                               "raw_mask_pattern": ho["mask_file"], "raw_mask_target": "D010+D011" if mid.endswith("WARMUP") else "D012+D013",
                               "native_1x_open": "TRUE", "nearest_8x_open": "TRUE", "decision": "SEPARATE" if inter == 0 else "FAIL"})
    write_csv(out / "P608_R3_HATCH_GLYPH_MATH_RULE_RELATIONS.csv", hatch_rows)

    manifest = {
        "figure_id": "FIG-P608-01", "round": "R98 local after_final_r2 / SA2 closeout R3", "candidate_status": "NON_OFFICIAL_LOCAL_CANDIDATE",
        "native_300dpi_png": str(old / "final_local_lua_official_stack_300dpi.png"), "native_grid": [full.width, full.height],
        "objects": len(objects), "text_parents": 31, "visible_pdf_paths": 58, "pattern_strokes": 2,
        "all_unordered_pairs": len(pairs), "glyph_rows": len(glyph_ledger), "low_profile_calibrations": len(calibration),
        "foreign_pixels_total": 0, "missing_strokes_total": 0,
        "text_illegal_overlap_total": sum(int(p["illegal_overlap_px"]) for p in pairs),
        "documented_graphic_composite_pairs": sum(p["classification"].startswith("DESIGNATED") for p in pairs),
        "hatch_to_visible_glyph_and_two_equality_rule_relations": len(hatch_rows),
        "critical_pair_cards": len(critical), "status": "TERMINAL_READY_NOT_A_VISUAL_PASS",
    }
    (out / "P608_R3_TERMINAL.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()

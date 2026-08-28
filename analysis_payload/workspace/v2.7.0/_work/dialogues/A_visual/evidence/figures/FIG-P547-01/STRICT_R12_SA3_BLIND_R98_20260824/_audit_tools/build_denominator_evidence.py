from __future__ import annotations

import csv
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image, ImageDraw


EV = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P547-01\STRICT_R12_SA3_BLIND_R98_20260824")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r98_fullbook\main_full.pdf")
PAGE_INDEX = 590
SCALE = 300.0 / 72.0
FIG_CROP = (280, 1180, 2160, 1850)
H = FIG_CROP[3] - FIG_CROP[1]
W = FIG_CROP[2] - FIG_CROP[0]

sys.path.insert(0, str(EV / "_audit_tools"))
import generate_core_evidence as core  # noqa: E402


def save_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_full_mask(path: Path) -> np.ndarray:
    arr = np.asarray(Image.open(path).convert("L"))
    assert arr.shape == (H, W), (path, arr.shape)
    return arr >= 128


def tight_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def bbox_gap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def write_mask(path: Path, mask: np.ndarray, crop: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if crop:
        bb = tight_bbox(mask)
        assert bb is not None
        mask = mask[bb[1]:bb[3], bb[0]:bb[2]]
    Image.fromarray((mask * 255).astype(np.uint8)).save(path)


def make_card(original: np.ndarray, mask: np.ndarray, bbox: tuple[int, int, int, int], label: str, scale: int) -> Image.Image:
    x0, y0, x1, y1 = bbox
    pad = 3
    xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    orig = original[ya:yb, xa:xb].copy()
    m = mask[ya:yb, xa:xb]
    over = orig.copy()
    over[m] = (255, 0, 0)
    only = np.full_like(orig, 255)
    only[m] = (0, 0, 0)
    ims = [Image.fromarray(x).resize((x.shape[1] * scale, x.shape[0] * scale), Image.Resampling.NEAREST) for x in (orig, over, only)]
    head = 28
    out = Image.new("RGB", (sum(im.width for im in ims), max(im.height for im in ims) + head), "white")
    draw = ImageDraw.Draw(out)
    draw.text((3, 3), f"{label} | ORIGINAL | OVERLAY | MASK ONLY | {scale}x nearest", fill="black")
    xx = 0
    for im in ims:
        out.paste(im, (xx, head))
        xx += im.width
    return out


def contact_sheets(cards: list[tuple[str, Image.Image]], outdir: Path, prefix: str, per_sheet: int, cols: int = 2) -> list[dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    register = []
    for start in range(0, len(cards), per_sheet):
        batch = cards[start:start + per_sheet]
        rows = math.ceil(len(batch) / cols)
        cw = max(im.width for _, im in batch) + 8
        ch = max(im.height for _, im in batch) + 8
        sheet = Image.new("RGB", (cw * cols, ch * rows), (235, 235, 235))
        name = f"{prefix}_{start // per_sheet + 1:03d}.png"
        for ci, (ident, im) in enumerate(batch):
            x = (ci % cols) * cw + 4
            y = (ci // cols) * ch + 4
            sheet.paste(im, (x, y))
            register.append({"ID": ident, "SHEET": name, "CELL": ci + 1})
        sheet.save(outdir / name)
    return register


def render_ledger_pages(rows: list[dict], fields: list[str], outdir: Path, prefix: str, per_page: int = 48) -> list[str]:
    outdir.mkdir(parents=True, exist_ok=True)
    pages = []
    for start in range(0, len(rows), per_page):
        batch = rows[start:start + per_page]
        lines = [" | ".join(fields)]
        for row in batch:
            lines.append(" | ".join(str(row.get(k, "")) for k in fields))
        width = max(1600, min(4200, 9 * max(len(x) for x in lines) + 30))
        im = Image.new("RGB", (width, 26 * (len(lines) + 1)), "white")
        draw = ImageDraw.Draw(im)
        for i, line in enumerate(lines):
            draw.text((8, 6 + i * 26), line, fill="black")
        name = f"{prefix}_{start // per_page + 1:03d}.png"
        im.save(outdir / name)
        pages.append(name)
    return pages


def pair_overlay(original: np.ndarray, a: np.ndarray, b: np.ndarray, label: str, scale: int) -> Image.Image:
    union = a | b
    bb = tight_bbox(union)
    assert bb is not None
    x0, y0, x1, y1 = bb
    pad = 6
    xa, ya, xb, yb = max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad)
    orig = original[ya:yb, xa:xb].copy()
    aa = a[ya:yb, xa:xb]
    bbm = b[ya:yb, xa:xb]
    over = orig.copy()
    over[aa] = (255, 0, 0)
    over[bbm] = (0, 150, 255)
    over[aa & bbm] = (255, 0, 255)
    only = np.full_like(orig, 255)
    only[aa] = (255, 0, 0)
    only[bbm] = (0, 100, 255)
    only[aa & bbm] = (255, 0, 255)
    ims = [Image.fromarray(x).resize((x.shape[1] * scale, x.shape[0] * scale), Image.Resampling.NEAREST) for x in (orig, over, only)]
    head = 30
    out = Image.new("RGB", (sum(i.width for i in ims), max(i.height for i in ims) + head), "white")
    draw = ImageDraw.Draw(out)
    draw.text((4, 4), f"{label} | ORIGINAL | A red/B blue | MASKS | {scale}x nearest", fill="black")
    xx = 0
    for im in ims:
        out.paste(im, (xx, head))
        xx += im.width
    return out


def command_mask(page_rect: fitz.Rect, drawing: dict, item: tuple, clip: fitz.Rect) -> np.ndarray:
    tmp = fitz.open()
    page = tmp.new_page(width=page_rect.width, height=page_rect.height)
    shape = page.new_shape()
    kind = item[0]
    if kind == "l":
        shape.draw_line(item[1], item[2])
    elif kind == "c":
        shape.draw_bezier(item[1], item[2], item[3], item[4])
    elif kind == "re":
        shape.draw_rect(item[1])
    else:
        raise ValueError(kind)
    width = max(0.25, float(drawing.get("width") or 0.25))
    shape.finish(width=width, color=(0, 0, 0), fill=None, lineCap=1, lineJoin=1, closePath=False)
    shape.commit()
    pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), clip=clip, alpha=False, colorspace=fitz.csRGB)
    arr = np.asarray(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), dtype=np.int16)
    tmp.close()
    return np.max(np.abs(arr - 255), axis=2) >= 20


def make_matrix(ids: list[str], pair_rows: list[dict], key_a: str, key_b: str, out: Path, state_key: str) -> None:
    cell = 24
    margin = 165
    n = len(ids)
    im = Image.new("RGB", (margin + n * cell + 10, margin + n * cell + 10), "white")
    draw = ImageDraw.Draw(im)
    idx = {x: i for i, x in enumerate(ids)}
    colors = {"PASS": (170, 230, 170), "DISJOINT": (190, 235, 190), "DESIGN": (170, 205, 245), "FAIL": (245, 150, 150), "PENDING": (255, 220, 130)}
    for i, ident in enumerate(ids):
        draw.text((margin + i * cell + 2, 145), str(i + 1), fill="black")
        draw.text((3, margin + i * cell + 5), f"{i + 1:02d} {ident}", fill="black")
        draw.rectangle((margin + i * cell, margin + i * cell, margin + (i + 1) * cell - 1, margin + (i + 1) * cell - 1), fill=(225, 225, 225))
    for row in pair_rows:
        i = idx[row[key_a]]
        j = idx[row[key_b]]
        state = row[state_key]
        color = colors.get(state, colors["PENDING"])
        for x, y in ((i, j), (j, i)):
            draw.rectangle((margin + x * cell, margin + y * cell, margin + (x + 1) * cell - 1, margin + (y + 1) * cell - 1), fill=color)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def main() -> None:
    fig = np.asarray(Image.open(EV / "figure_crop_300dpi.png").convert("RGB"))
    assert fig.shape == (H, W, 3)
    glyph_rows = load_csv(EV / "04_glyphs/glyph_mapping_ledger.csv")
    assert len(glyph_rows) == 193

    glyph_masks: dict[str, np.ndarray] = {}
    text_masks = {f"T{i:02d}": np.zeros((H, W), bool) for i in range(1, 24)}
    text_pdf_bbox: dict[str, tuple[int, int, int, int]] = {}
    glyph_manual = []
    glyph_1x_cards = []
    for row in glyph_rows:
        ident = row["GLYPH_ID"]
        path = EV / row["MASK_PATH"]
        crop = np.asarray(Image.open(path).convert("L")) >= 128
        x0 = int(row["INK_X0"]) - FIG_CROP[0]
        y0 = int(row["INK_Y0"]) - FIG_CROP[1]
        mask = np.zeros((H, W), bool)
        mask[y0:y0 + crop.shape[0], x0:x0 + crop.shape[1]] = crop
        assert int(mask.sum()) == int(row["INK_AREA_PX"])
        glyph_masks[ident] = mask
        text_masks[row["PARENT_ID"]] |= mask
        bb = (int(row["BBOX_X0"]), int(row["BBOX_Y0"]), int(row["BBOX_X1"]), int(row["BBOX_Y1"]))
        if row["PARENT_ID"] not in text_pdf_bbox:
            text_pdf_bbox[row["PARENT_ID"]] = bb
        else:
            old = text_pdf_bbox[row["PARENT_ID"]]
            text_pdf_bbox[row["PARENT_ID"]] = (min(old[0], bb[0]), min(old[1], bb[1]), max(old[2], bb[2]), max(old[3], bb[3]))
        card = make_card(fig, mask, tight_bbox(mask), f"{ident} {row['CHAR']} {row['PARENT_ID']}", 1)
        glyph_1x_cards.append((ident, card))
        glyph_manual.append({
            "GLYPH_ID": ident, "CHAR": row["CHAR"], "PARENT_ID": row["PARENT_ID"],
            "ORIGINAL_1X": row["ORIGINAL_PATH"], "MASK_1X": row["MASK_PATH"], "CARD_8X": row["CARD_PATH"],
            "H_INK_PX": row["H_INK_PX"], "AREA_PX": row["INK_AREA_PX"],
            "MISSING_STROKE_PX": row["MISSING_STROKE_PX"], "FOREIGN_PIXEL_PX": row["FOREIGN_PIXEL_PX"],
            "MACHINE_DECISION": row["PASS_FAIL"], "REVIEWER": "PENDING", "ORIGINAL_MATCH": "PENDING",
            "OVERLAY_COMPLETE": "PENDING", "MASK_ONLY_PURE": "PENDING", "DECISION": "PENDING_VISUAL_OPEN",
        })
    assert all(m.any() for m in text_masks.values())
    reg = contact_sheets(glyph_1x_cards, EV / "04_glyphs/contact_sheets_1x", "glyphs_native_1x", 20, cols=4)
    regmap = {r["ID"]: r for r in reg}
    for row in glyph_manual:
        rr = regmap[row["GLYPH_ID"]]
        row["CONTACT_SHEET_1X"] = f"04_glyphs/contact_sheets_1x/{rr['SHEET']}"
        row["CONTACT_CELL_1X"] = rr["CELL"]
    save_csv(EV / "04_glyphs/glyph_manual_review_pending.csv", glyph_manual)

    ownership = json.loads((EV / "04_glyphs/component_ownership_audit.json").read_text(encoding="utf-8"))
    owner_rows = []
    for item in ownership["resolved_component_splits"]:
        pre = item.get("pre_reassignment_pixels_by_glyph", {})
        values = sorted(pre.items(), key=lambda kv: kv[1], reverse=True)
        dominant = values[0][0] if values else ""
        major = values[0][1] if values else 0
        minor = sum(v for _, v in values[1:])
        ratio = major / max(1, minor)
        reassigned = item.get("dominant_connected_component_reassignment")
        decision = "DOMINANT_COMPONENT_20_TO_1" if reassigned else "PDF_CANDIDATE_SUPPORT_SPLIT"
        final_assignment = item["assigned_pixels_by_glyph"]
        if set(pre) == {"G114", "G115"} and sum(pre.values()) == 28:
            final_assignment = {"G120": 28}
            decision = "STRETCHY_DELIMITER_VISIBLE_CONTOUR_OVERRIDE"
        owner_rows.append({
            "COMPONENT": item["component"], "CANDIDATE_OWNERS_JSON": json.dumps(pre, ensure_ascii=False),
            "DOMINANT_GLYPH": dominant, "DOMINANT_PX": major, "MINOR_PX": minor,
            "DOMINANT_TO_MINOR_RATIO": round(ratio, 6), "RULE_THRESHOLD": "20:1", "SHARED_CANDIDATE_PX": item["shared_candidate_pixels"],
            "UNASSIGNED_PX": item["unassigned_pixels"], "FINAL_ASSIGNMENT_JSON": json.dumps(final_assignment, ensure_ascii=False),
            "DECISION": decision, "G139_DISPOSITION": "1px is G140 p boundary antialias overhang; not a G139 stroke" if "G139" in pre else "N/A",
            "REVIEWER": "PENDING", "REVIEW_DECISION": "PENDING_VISUAL_OPEN",
        })
    save_csv(EV / "04_glyphs/multi_owner_component_ledger_pending.csv", owner_rows)
    stretchy_rows = []
    for item in ownership.get("extended_visible_contour_corrections", []):
        stretchy_rows.append({
            "GLYPH_ID": item["glyph"], "CHAR": item["char"], "PARENT_ID": item["semantic_parent"],
            "RAW_CHAR_BBOX_WHOLEPAGE_PX": json.dumps(item["raw_char_bbox_wholepage_px"]),
            "OWNERSHIP_ROI_WHOLEPAGE_PX": json.dumps(item["ownership_roi_wholepage_px"]),
            "PREVIOUS_OWNED_PX": item["previous_owned_px"], "FINAL_COMPLETE_CONTOUR_PX": item["final_owned_px"],
            "CLEARED_FOREIGN_CANDIDATES_JSON": json.dumps(item["cleared_foreign_candidate_pixels"], ensure_ascii=False),
            "METHOD": item["method"], "REVIEWER": "PENDING", "REVIEW_DECISION": "PENDING_VISUAL_OPEN",
        })
    assert len(stretchy_rows) == 4
    save_csv(EV / "04_glyphs/stretchy_delimiter_ownership_ledger_pending.csv", stretchy_rows)
    compare = [
        (x, Image.open(EV / next(r["CARD_PATH"] for r in glyph_rows if r["GLYPH_ID"] == x)).convert("RGB"))
        for x in ("G054", "G139", "G140")
    ]
    contact_sheets(compare, EV / "04_glyphs/g139_ownership", "G054_G139_G140_8x", 3, cols=1)

    record_rows = load_csv(EV / "06_primitives/vector_record_ledger.csv")
    assert len(record_rows) == 71
    record_masks = {}
    record_manual = []
    record_1x_cards = []
    record_8x_cards = []
    semantic_masks: dict[str, np.ndarray] = defaultdict(lambda: np.zeros((H, W), bool))
    semantic_order = []
    for row in record_rows:
        rid = row["RECORD_ID"]
        final = load_full_mask(EV / row["FINAL_MASK"])
        if final.any():
            audit = final
            domain = "FINAL_VISIBLE_FOREGROUND"
        else:
            bg_path = EV / "06_primitives/record_masks" / f"{rid}_background.png"
            audit = load_full_mask(bg_path)
            domain = "OPAQUE_BACKGROUND_GEOMETRY"
        assert audit.any()
        record_masks[rid] = audit
        sid = row["SEMANTIC_ID"]
        if not sid.startswith("BG"):
            semantic_masks[sid] |= final
            if sid not in semantic_order:
                semantic_order.append(sid)
        bb = tight_bbox(audit)
        card = make_card(fig, audit, bb, f"{rid} seq={row['SEQNO']} {sid}", 1)
        record_1x_cards.append((rid, card))
        record_8x_cards.append((rid, Image.open(EV / row["CARD"]).convert("RGB")))
        record_manual.append({
            "RECORD_ID": rid, "SEQNO": row["SEQNO"], "SEMANTIC_ID": sid, "AUDIT_DOMAIN": domain,
            "MASK_1X": row["FINAL_MASK"] if final.any() else f"06_primitives/record_masks/{rid}_background.png",
            "CARD_8X": row["CARD"], "PIXELS": int(audit.sum()), "REVIEWER": "PENDING",
            "ORIGINAL_MATCH": "PENDING", "MASK_ONLY_PURE": "PENDING", "DECISION": "PENDING_VISUAL_OPEN",
        })
    assert len(semantic_order) == 34, semantic_order
    reg = contact_sheets(record_1x_cards, EV / "06_primitives/contact_sheets_1x", "vector_records_native_1x", 12, cols=2)
    contact_sheets(record_8x_cards, EV / "06_primitives/contact_sheets_8x_small", "vector_records_8x", 4, cols=1)
    regmap = {r["ID"]: r for r in reg}
    for row in record_manual:
        rr = regmap[row["RECORD_ID"]]
        row["CONTACT_SHEET_1X"] = f"06_primitives/contact_sheets_1x/{rr['SHEET']}"
        row["CONTACT_CELL_1X"] = rr["CELL"]
    save_csv(EV / "06_primitives/path_record_manual_review_pending.csv", record_manual)

    object_masks = {**text_masks, **semantic_masks}
    object_ids = list(text_masks) + semantic_order
    assert len(object_ids) == 57
    object_rows = []
    object_cards_1x = []
    object_cards_8x = []
    object_bbox = {}
    object_class = {}
    for ident in object_ids:
        mask = object_masks[ident]
        bb = tight_bbox(mask)
        assert bb is not None, ident
        object_bbox[ident] = (bb[0] + FIG_CROP[0], bb[1] + FIG_CROP[1], bb[2] + FIG_CROP[0], bb[3] + FIG_CROP[1])
        if ident.startswith("T"):
            cls = "TEXT_PARENT"
        elif ident.startswith(("R", "H")):
            cls = "MATH_RULE"
        elif ident.startswith(("N", "B")) or ident == "C01":
            cls = "NODE_BORDER"
        else:
            cls = "LINE_ARROW"
        object_class[ident] = cls
        rel = f"03_objects/object_masks/{ident}_mask_1x.png"
        write_mask(EV / rel, mask)
        c1 = make_card(fig, mask, bb, f"{ident} {cls}", 1)
        c8 = make_card(fig, mask, bb, f"{ident} {cls}", 8)
        (EV / "03_objects/object_cards").mkdir(parents=True, exist_ok=True)
        c1.save(EV / "03_objects/object_cards" / f"{ident}_1x.png")
        c8.save(EV / "03_objects/object_cards" / f"{ident}_8x.png")
        object_cards_1x.append((ident, c1))
        object_cards_8x.append((ident, c8))
        object_rows.append({"OBJECT_ID": ident, "OBJECT_CLASS": cls, "PIXELS": int(mask.sum()), "BBOX_WHOLEPAGE_PX": json.dumps(object_bbox[ident]), "MASK_1X": rel,
                            "CARD_1X": f"03_objects/object_cards/{ident}_1x.png", "CARD_8X": f"03_objects/object_cards/{ident}_8x.png"})
    save_csv(EV / "03_objects/object_manifest_57.csv", object_rows)
    contact_sheets(object_cards_1x, EV / "03_objects/object_contact_sheets_1x", "objects_native_1x", 12, cols=2)
    contact_sheets(object_cards_8x, EV / "03_objects/object_contact_sheets_8x_small", "objects_8x", 4, cols=1)

    distances = {ident: cv2.distanceTransform((~object_masks[ident]).astype(np.uint8), cv2.DIST_L2, 5) for ident in object_ids}
    pair_rows = []
    critical_cards_1x = []
    critical_cards_8x = []
    for pi, (a, b) in enumerate(itertools.combinations(object_ids, 2), 1):
        ma, mb = object_masks[a], object_masks[b]
        overlap = int((ma & mb).sum())
        min_center = 0.0 if overlap else float(distances[a][mb].min())
        mask_clear = max(0.0, min_center - 1.0)
        if a.startswith("T") and b.startswith("T"):
            metric = "FINAL_VISIBLE_GLYPH_VECTOR_BBOX"
            rawdict_gap = bbox_gap(text_pdf_bbox[a], text_pdf_bbox[b])
            clearance = bbox_gap(object_bbox[a], object_bbox[b])
            threshold = 4.0
            relation = "TEXT_TEXT"
        elif a.startswith("T") or b.startswith("T"):
            text_id, vector_id = (a, b) if a.startswith("T") else (b, a)
            metric = "RAW_MASK"
            clearance = mask_clear
            tbb = object_bbox[text_id]
            vbb = object_bbox[vector_id]
            centre = ((tbb[0] + tbb[2]) / 2, (tbb[1] + tbb[3]) / 2)
            inside = vbb[0] <= centre[0] <= vbb[2] and vbb[1] <= centre[1] <= vbb[3]
            threshold = 5.0 if object_class[vector_id] == "NODE_BORDER" and inside else 3.0
            relation = "TEXT_NODE_BORDER" if threshold == 5.0 else "TEXT_VECTOR"
        else:
            metric = "RAW_MASK"
            clearance = mask_clear
            threshold = 0.0
            relation = "VECTOR_VECTOR"
        passed = overlap == 0 and clearance + 1e-6 >= threshold if threshold > 0 else True
        state = "PASS" if passed else "FAIL"
        row = {
            "PAIR_ID": f"PAIR_{pi:04d}", "A_ID": a, "B_ID": b, "A_CLASS": object_class[a], "B_CLASS": object_class[b],
            "RELATION": relation, "METRIC": metric, "RAW_INTERSECTION_PX": overlap,
            "MIN_CENTER_DISTANCE_PX": round(min_center, 4), "MIN_CLEARANCE_PX": round(clearance, 4), "THRESHOLD_PX": threshold,
            "RAWTEXT_FONT_METRIC_BBOX_GAP_PX": round(rawdict_gap, 4) if a.startswith("T") and b.startswith("T") else "N/A",
            "MACHINE_STATE": state, "ILLEGAL_OVERLAP_PX": overlap if threshold > 0 else 0,
            "REVIEWER": "PENDING", "MANUAL_DECISION": "PENDING_VISUAL_OPEN",
        }
        if threshold > 0 and (clearance < 12 or overlap > 0):
            name = row["PAIR_ID"]
            c1 = pair_overlay(fig, ma, mb, f"{name} {a}/{b} clr={clearance:.2f} thr={threshold:.0f}", 1)
            c8 = pair_overlay(fig, ma, mb, f"{name} {a}/{b} clr={clearance:.2f} thr={threshold:.0f}", 8)
            d = EV / "05_pairs/critical"
            d.mkdir(parents=True, exist_ok=True)
            c1.save(d / f"{name}_1x.png")
            c8.save(d / f"{name}_8x.png")
            row["CRITICAL_1X"] = f"05_pairs/critical/{name}_1x.png"
            row["CRITICAL_8X"] = f"05_pairs/critical/{name}_8x.png"
            critical_cards_1x.append((name, c1))
            critical_cards_8x.append((name, c8))
        pair_rows.append(row)
    assert len(pair_rows) == 1596
    save_csv(EV / "05_pairs/object_pair_ledger_pending.csv", pair_rows)
    render_ledger_pages(pair_rows, ["PAIR_ID", "A_ID", "B_ID", "RELATION", "RAW_INTERSECTION_PX", "MIN_CLEARANCE_PX", "THRESHOLD_PX", "MACHINE_STATE"], EV / "05_pairs/review_pages", "object_pairs", 48)
    make_matrix(object_ids, pair_rows, "A_ID", "B_ID", EV / "05_pairs/object_pair_matrix.png", "MACHINE_STATE")
    if critical_cards_1x:
        contact_sheets(critical_cards_1x, EV / "05_pairs/critical_contact_1x", "critical_pairs_1x", 8, cols=1)
        contact_sheets(critical_cards_8x, EV / "05_pairs/critical_contact_8x", "critical_pairs_8x", 4, cols=1)

    record_distances = {rid: cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 5) for rid, m in record_masks.items()}
    path_rows = []
    path_critical_1x = []
    path_critical_8x = []
    by_rid = {r["RECORD_ID"]: r for r in record_rows}
    for pi, (a, b) in enumerate(itertools.combinations(record_masks, 2), 1):
        ma, mb = record_masks[a], record_masks[b]
        overlap = int((ma & mb).sum())
        min_center = 0.0 if overlap else float(record_distances[a][mb].min())
        clearance = max(0.0, min_center - 1.0)
        sa, sb = by_rid[a]["SEMANTIC_ID"], by_rid[b]["SEMANTIC_ID"]
        if overlap == 0:
            state = "DISJOINT"
            rationale = "RAW_MASKS_DISJOINT"
        elif sa == sb:
            state = "DESIGN"
            rationale = "SAME_SEMANTIC_OBJECT_COMPOSITION"
        elif sa.startswith("BG") or sb.startswith("BG"):
            state = "DESIGN"
            rationale = "OPAQUE_BACKGROUND_PAINT_DOMAIN"
        else:
            state = "PENDING"
            rationale = "DIFFERENT_SEMANTIC_VECTOR_CONTACT_REQUIRES_OPEN"
        row = {"PATH_PAIR_ID": f"PATHPAIR_{pi:04d}", "A_RECORD": a, "B_RECORD": b, "A_SEMANTIC": sa, "B_SEMANTIC": sb,
               "RAW_INTERSECTION_PX": overlap, "MIN_CLEARANCE_PX": round(clearance, 4), "MACHINE_STATE": state, "RATIONALE": rationale,
               "REVIEWER": "PENDING", "MANUAL_DECISION": "PENDING_VISUAL_OPEN"}
        if overlap > 0 and sa != sb and not sa.startswith("BG") and not sb.startswith("BG"):
            name = row["PATH_PAIR_ID"]
            c1 = pair_overlay(fig, ma, mb, f"{name} {a}/{sa} vs {b}/{sb} ov={overlap}", 1)
            c8 = pair_overlay(fig, ma, mb, f"{name} {a}/{sa} vs {b}/{sb} ov={overlap}", 8)
            d = EV / "06_primitives/path_pair_critical"
            d.mkdir(parents=True, exist_ok=True)
            c1.save(d / f"{name}_1x.png")
            c8.save(d / f"{name}_8x.png")
            row["CRITICAL_1X"] = f"06_primitives/path_pair_critical/{name}_1x.png"
            row["CRITICAL_8X"] = f"06_primitives/path_pair_critical/{name}_8x.png"
            path_critical_1x.append((name, c1))
            path_critical_8x.append((name, c8))
        path_rows.append(row)
    assert len(path_rows) == 2485
    save_csv(EV / "06_primitives/path_pair_ledger_pending.csv", path_rows)
    render_ledger_pages(path_rows, ["PATH_PAIR_ID", "A_RECORD", "B_RECORD", "A_SEMANTIC", "B_SEMANTIC", "RAW_INTERSECTION_PX", "MIN_CLEARANCE_PX", "MACHINE_STATE"], EV / "06_primitives/path_pair_review_pages", "path_pairs", 50)
    make_matrix(list(record_masks), path_rows, "A_RECORD", "B_RECORD", EV / "06_primitives/path_pair_matrix.png", "MACHINE_STATE")
    if path_critical_1x:
        contact_sheets(path_critical_1x, EV / "06_primitives/path_pair_critical_contact_1x", "path_critical_1x", 8, cols=1)
        contact_sheets(path_critical_8x, EV / "06_primitives/path_pair_critical_contact_8x", "path_critical_8x", 4, cols=1)

    doc = fitz.open(PDF)
    page = doc[PAGE_INDEX]
    drawings = [d for d in page.get_drawings(extended=True) if int(d["seqno"]) in core.RULE_MAP]
    assert len(drawings) == 71
    clip = fitz.Rect(FIG_CROP[0] / SCALE, FIG_CROP[1] / SCALE, FIG_CROP[2] / SCALE, FIG_CROP[3] / SCALE)
    cmd_rows = []
    cmd_masks = {}
    cmd_cards_1x = []
    cmd_cards_8x = []
    cid_num = 0
    for ri, drawing in enumerate(drawings, 1):
        rid = f"D{ri:03d}"
        for ci, item in enumerate(drawing["items"], 1):
            cid_num += 1
            cid = f"V{cid_num:03d}"
            mask = command_mask(page.rect, drawing, item, clip)
            assert mask.any(), (cid, rid, item)
            cmd_masks[cid] = mask
            bb = tight_bbox(mask)
            rel = f"06_primitives/command_masks/{cid}_mask_1x.png"
            write_mask(EV / rel, mask, crop=True)
            c1 = make_card(fig, mask, bb, f"{cid} {rid} item={ci} type={item[0]}", 1)
            c8 = make_card(fig, mask, bb, f"{cid} {rid} item={ci} type={item[0]}", 8)
            (EV / "06_primitives/command_cards").mkdir(parents=True, exist_ok=True)
            c1.save(EV / "06_primitives/command_cards" / f"{cid}_1x.png")
            c8.save(EV / "06_primitives/command_cards" / f"{cid}_8x.png")
            cmd_cards_1x.append((cid, c1))
            cmd_cards_8x.append((cid, c8))
            cmd_rows.append({"COMMAND_ID": cid, "RECORD_ID": rid, "SEQNO": int(drawing["seqno"]), "SEMANTIC_ID": core.RULE_MAP[int(drawing["seqno"])],
                             "COMMAND_INDEX": ci, "COMMAND_TYPE": item[0], "REPLAY_DOMAIN": "INDEPENDENT_GEOMETRY_STROKE_300DPI",
                             "PIXELS": int(mask.sum()), "BBOX_CROP_PX": json.dumps(bb), "MASK_1X": rel,
                             "CARD_1X": f"06_primitives/command_cards/{cid}_1x.png", "CARD_8X": f"06_primitives/command_cards/{cid}_8x.png",
                             "REVIEWER": "PENDING", "MANUAL_DECISION": "PENDING_VISUAL_OPEN"})
    assert len(cmd_rows) == 143
    contact_sheets(cmd_cards_1x, EV / "06_primitives/command_contact_sheets_1x", "commands_native_1x", 16, cols=2)
    contact_sheets(cmd_cards_8x, EV / "06_primitives/command_contact_sheets_8x_small", "commands_8x", 6, cols=1)
    save_csv(EV / "06_primitives/command_replay_ledger_pending.csv", cmd_rows)

    commands_by_record = defaultdict(list)
    for row in cmd_rows:
        commands_by_record[row["RECORD_ID"]].append(row["COMMAND_ID"])
    command_pair_rows = []
    pair_no = 0
    for rid, cids in commands_by_record.items():
        for a, b in itertools.combinations(cids, 2):
            pair_no += 1
            overlap = int((cmd_masks[a] & cmd_masks[b]).sum())
            command_pair_rows.append({"COMMAND_PAIR_ID": f"CMDPAIR_{pair_no:03d}", "RECORD_ID": rid, "A_COMMAND": a, "B_COMMAND": b,
                                      "GEOMETRY_INTERSECTION_PX": overlap, "MACHINE_STATE": "DESIGN" if overlap else "DISJOINT",
                                      "RATIONALE": "SAME_RECORD_COMMAND_COMPOSITION", "REVIEWER": "PENDING", "MANUAL_DECISION": "PENDING_VISUAL_OPEN"})
    assert len(command_pair_rows) == 186, len(command_pair_rows)
    save_csv(EV / "06_primitives/within_record_command_pair_ledger_pending.csv", command_pair_rows)
    render_ledger_pages(command_pair_rows, ["COMMAND_PAIR_ID", "RECORD_ID", "A_COMMAND", "B_COMMAND", "GEOMETRY_INTERSECTION_PX", "MACHINE_STATE"], EV / "06_primitives/command_pair_review_pages", "command_pairs", 48)

    role_rows = []
    grouped = defaultdict(list)
    for row in glyph_rows:
        if row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION":
            continue
        grouped[(row["PANEL_ID"], row["ROLE"], row["PARENT_ID"], row["SCRIPT_CLASS"])].append(int(row["H_INK_PX"]))
    parent_medians = []
    for key, vals in grouped.items():
        panel, role, parent, script = key
        med = float(np.median(vals))
        parent_medians.append((panel, role, parent, script, med))
    role_groups = defaultdict(list)
    for panel, role, parent, script, med in parent_medians:
        role_groups[(panel, role, script)].append(med)
    for panel, role, parent, script, med in parent_medians:
        peers = role_groups[(panel, role, script)]
        ref = float(np.median(peers))
        ratio = med / ref if ref else 0
        role_rows.append({"PANEL_ID": panel, "ROLE": role, "PARENT_ID": parent, "SCRIPT_CLASS": script, "PARENT_MEDIAN_PX": med,
                          "ROLE_MEDIAN_PX": ref, "RATIO_TO_ROLE_MEDIAN": round(ratio, 6), "LOWER": 0.92, "UPPER": 1.08,
                          "PASS_FAIL": "PASS" if 0.92 <= ratio <= 1.08 else "FAIL"})
    save_csv(EV / "08_reports/glyph_role_ratio_audit.csv", role_rows)

    clip_px = 0
    for mask in object_masks.values():
        clip_px += int(mask[0, :].sum() + mask[-1, :].sum() + mask[:, 0].sum() + mask[:, -1].sum())
    summary = {
        "object_count": len(object_ids), "object_pair_count": len(pair_rows), "object_pair_fail_count": sum(r["MACHINE_STATE"] == "FAIL" for r in pair_rows),
        "glyph_count": len(glyph_rows), "glyph_fail_count": sum(r["PASS_FAIL"] != "PASS" for r in glyph_rows),
        "path_record_count": len(record_rows), "path_pair_count": len(path_rows), "path_pair_pending_contact_count": sum(r["MACHINE_STATE"] == "PENDING" for r in path_rows),
        "command_count": len(cmd_rows), "within_record_command_pair_count": len(command_pair_rows),
        "multi_owner_component_count": len(owner_rows), "unassigned_component_pixels": sum(int(r["UNASSIGNED_PX"]) for r in owner_rows),
        "g054": next({k: r[k] for k in ("H_INK_PX", "INK_AREA_PX", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "PASS_FAIL")} for r in glyph_rows if r["GLYPH_ID"] == "G054"),
        "g139": next({k: r[k] for k in ("H_INK_PX", "INK_AREA_PX", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX", "PASS_FAIL")} for r in glyph_rows if r["GLYPH_ID"] == "G139"),
        "clip_boundary_pixel_count": clip_px,
        "role_ratio_fail_count": sum(r["PASS_FAIL"] != "PASS" for r in role_rows),
        "review_status": "PENDING_ALL_NATIVE_1X_AND_8X_OPEN",
    }
    (EV / "08_reports/denominator_machine_summary_pending.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

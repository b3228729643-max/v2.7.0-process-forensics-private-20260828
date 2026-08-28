"""Build same-codepoint punctuation calibration only from the locked official PDF.

The XeTeX probe is deliberately not used as evidence.  Instead, each reference
is a separately located glyph from the same locked 813-page PDF with identical
codepoint, PDF font name, observed effective size, font colour, and weight.
All measurements are from its native 300-dpi raster; 8x images are nearest-only
review views and never used for counting.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "official_pdf_same_codepoint"
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r97_fullbook\main_full.pdf")
MANIFEST = ROOT.parent / "glyph_manifest.csv"
S300 = 300.0 / 72.0
TARGET_PHYSICAL_PAGE = 801


def px_rect(rect):
    return (int(math.floor(rect[0] * S300)), int(math.floor(rect[1] * S300)), int(math.ceil(rect[2] * S300)), int(math.ceil(rect[3] * S300)))


def clamp(rect, w, h, pad=1):
    x0, y0, x1, y1 = rect
    return (max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad))


def rgb_from_int(value):
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def dominant_rgb(arr):
    vals, cnt = np.unique(arr.reshape(-1, 3), axis=0, return_counts=True)
    return vals[int(np.argmax(cnt))].astype(float)


def foreground_by_color(arr, fg_rgb):
    # This mirrors the target raw-mask rule: native pixels only; no morphology.
    bg = dominant_rgb(arr)
    fg = np.array(fg_rgb, dtype=float)
    v = fg - bg
    v2 = float(np.dot(v, v))
    if v2 < 1.0:
        return np.zeros(arr.shape[:2], dtype=bool)
    d = arr.astype(float) - bg
    alpha = np.sum(d * v, axis=2) / v2
    residual = np.linalg.norm(d - alpha[..., None] * v, axis=2)
    threshold = 20.0 / max(20.0, float(np.max(np.abs(v))))
    return (alpha >= threshold) & (alpha <= 1.28) & (residual <= 44.0)


def save_mask(mask, path):
    Image.fromarray(np.where(mask, 0, 255).astype(np.uint8), mode="L").save(path)


def add_label(image, xy, value):
    try:
        font = ImageFont.truetype("arial.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(image).text(xy, value, fill=(30, 30, 30), font=font)


def make_card(item, out):
    """Save original / overlay / mask-only / 8x-nearest for one reference glyph."""
    orig = item["crop"]
    mask = item["mask"]
    overlay = orig.copy()
    overlay[mask] = np.array([225, 25, 35], dtype=np.uint8)
    mono = np.full_like(orig, 255)
    mono[mask] = 0
    base = out / item["ref_id"]
    paths = {
        "original": base.with_name(base.name + "_original_native_1x.png"),
        "overlay": base.with_name(base.name + "_target_overlay_native_1x.png"),
        "mask": base.with_name(base.name + "_mask_only_native_1x.png"),
        "nearest": base.with_name(base.name + "_8x_nearest.png"),
    }
    Image.fromarray(orig).save(paths["original"])
    Image.fromarray(overlay).save(paths["overlay"])
    Image.fromarray(mono).save(paths["mask"])
    Image.fromarray(overlay).resize((overlay.shape[1] * 8, overlay.shape[0] * 8), Image.Resampling.NEAREST).save(paths["nearest"])
    return paths


def make_sheets(items, out, per_sheet=20):
    sheets = []
    for start in range(0, len(items), per_sheet):
        chunk = items[start:start + per_sheet]
        cols, cell_w, cell_h = 4, 420, 180
        sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(chunk) / cols) * cell_h), "white")
        for j, item in enumerate(chunk):
            x, y = (j % cols) * cell_w, (j // cols) * cell_h
            im1 = Image.open(item["paths"]["original"]).convert("RGB")
            im2 = Image.open(item["paths"]["overlay"]).convert("RGB")
            im3 = Image.open(item["paths"]["mask"]).convert("RGB")
            im4 = Image.open(item["paths"]["nearest"]).convert("RGB")
            sheet.paste(im1, (x + 4, y + 30)); sheet.paste(im2, (x + 90, y + 30)); sheet.paste(im3, (x + 176, y + 30))
            ratio = min(220 / im4.width, 135 / im4.height, 1.0)
            if ratio < 1.0:
                im4 = im4.resize((max(1, int(im4.width * ratio)), max(1, int(im4.height * ratio))), Image.Resampling.NEAREST)
            sheet.paste(im4, (x + 192, y + 34))
            add_label(sheet, (x + 4, y + 4), f"{item['ref_id']} p{item['physical_page']} {item['codepoint']} {item['h_ink']}px/{item['area']}px")
            add_label(sheet, (x + 4, y + 16), "ORIG | OVERLAY | MASK | 8x nearest")
        path = out / f"same_codepoint_contact_sheet_{start // per_sheet + 1:02d}.png"
        sheet.save(path); sheets.append(path.name)
    return sheets


def key_from_row(row):
    return (row["rawdict_char"], row["source_font"], round(float(row["pdf_size_pt"]), 4), row["font_color_rgb"])


def main():
    # This subtree is generated solely by this calibration script; clear a
    # failed preliminary attempt before writing a coherent final calibration.
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    cards = OUT / "cards"
    sheets_dir = OUT / "contact_sheets"
    cards.mkdir(exist_ok=True); sheets_dir.mkdir(exist_ok=True)
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        targets = [r for r in csv.DictReader(f) if r["script_class"] == "LOW_PROFILE_PUNCTUATION"]
    keys = list(dict.fromkeys(key_from_row(r) for r in targets))
    want = set(keys)
    doc = fitz.open(PDF)
    candidates = defaultdict(list)
    # Read current official candidate only. Exclude the target page so the
    # calibration is genuinely independent of the glyph being judged.
    for pidx, page in enumerate(doc):
        if pidx + 1 == TARGET_PHYSICAL_PAGE:
            continue
        raw = page.get_text("rawdict")
        for block in raw["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    col = json.dumps(list(rgb_from_int(span["color"])))
                    for char in span["chars"]:
                        key = (char["c"], span["font"], round(float(span["size"]), 4), col)
                        if key in want and len(candidates[key]) < 12:
                            candidates[key].append({"physical_page": pidx + 1, "bbox_pt": char["bbox"], "font": span["font"], "size": round(float(span["size"]), 4), "color": list(rgb_from_int(span["color"]))})
    all_refs = []
    cache = {}
    for gi, key in enumerate(keys, 1):
        pool = candidates[key]
        if len(pool) < 2:
            raise RuntimeError(f"insufficient independent candidate references for {key}: {len(pool)}")
        for ri, item in enumerate(pool[:min(6, len(pool))], 1):
            pp = item["physical_page"]
            if pp not in cache:
                pix = doc[pp - 1].get_pixmap(matrix=fitz.Matrix(S300, S300), alpha=False)
                cache[pp] = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).copy()
            page_arr = cache[pp]
            # The rawdict character bbox is the exclusive ownership window.
            # Padding would admit same-colour neighbouring text into a small
            # punctuation mask, so the calibration follows the target rule.
            bbox = clamp(px_rect(item["bbox_pt"]), page_arr.shape[1], page_arr.shape[0], 0)
            crop = page_arr[bbox[1]:bbox[3], bbox[0]:bbox[2]].copy()
            mask = foreground_by_color(crop, item["color"])
            ref = {**item, "ref_id": f"CAL{gi:02d}_{ri:02d}", "group": gi, "codepoint": f"U+{ord(key[0]):04X}", "bbox_px": list(bbox), "crop": crop, "mask": mask, "h_ink": int(mask.any(axis=1).sum()), "area": int(mask.sum())}
            if not ref["area"]:
                raise RuntimeError(f"empty calibration mask: {ref['ref_id']}")
            ref["paths"] = make_card(ref, cards)
            all_refs.append(ref)
    sheets = make_sheets(all_refs, sheets_dir)
    by_key = defaultdict(list)
    for ref in all_refs:
        by_key[keys[ref["group"] - 1]].append(ref)
    reference_rows = []
    for ref in all_refs:
        reference_rows.append({"ref_id": ref["ref_id"], "group": ref["group"], "physical_page": ref["physical_page"], "codepoint": ref["codepoint"], "bbox_pt": json.dumps([round(x, 3) for x in ref["bbox_pt"]]), "bbox_px": json.dumps(ref["bbox_px"]), "font": ref["font"], "pdf_size_pt": ref["size"], "font_color_rgb": json.dumps(ref["color"]), "h_ink_px": ref["h_ink"], "ink_area_px": ref["area"], "original_path": str(ref["paths"]["original"].relative_to(OUT)), "overlay_path": str(ref["paths"]["overlay"].relative_to(OUT)), "mask_path": str(ref["paths"]["mask"].relative_to(OUT)), "nearest_path": str(ref["paths"]["nearest"].relative_to(OUT))})
    target_rows = []
    for target in targets:
        key = key_from_row(target)
        refs = by_key[key]
        # Fixed, non-optimizing baseline: median of six separately located
        # official-PDF instances. Both H_INK and area must independently pass.
        hs = [r["h_ink"] for r in refs]; areas = [r["area"] for r in refs]
        hmed = float(statistics.median(hs)); amed = float(statistics.median(areas))
        th, ta = int(target["h_ink_px"]), int(target["ink_area_px"])
        hr, ar = th / hmed, ta / amed
        decision = "PASS" if 0.92 <= hr <= 1.08 and 0.92 <= ar <= 1.08 else "FAIL"
        target_rows.append({"glyph_id": target["glyph_id"], "rawdict_char": target["rawdict_char"], "codepoint": target["codepoint"], "target_font": target["source_font"], "target_pdf_size_pt": target["pdf_size_pt"], "target_font_color_rgb": target["font_color_rgb"], "target_h_ink_px": th, "target_ink_area_px": ta, "reference_group": refs[0]["group"], "reference_ids": ";".join(r["ref_id"] for r in refs), "reference_h_values": ";".join(str(r["h_ink"]) for r in refs), "reference_area_values": ";".join(str(r["area"]) for r in refs), "reference_h_median": hmed, "reference_area_median": amed, "h_ratio": round(hr, 4), "area_ratio": round(ar, 4), "decision": decision, "manual_viewed": "PENDING_MANUAL", "note": "same codepoint/font/observed-size/RGB; six independent official-PDF instances, target page excluded"})
    def write(path, rows):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    write(OUT / "calibration_reference_instances.csv", reference_rows)
    write(OUT / "low_profile_punctuation_calibration.csv", target_rows)
    (OUT / "calibration_summary.json").write_text(json.dumps({"reference_source": str(PDF), "target_page_excluded": TARGET_PHYSICAL_PAGE, "target_glyphs": len(target_rows), "reference_instances": len(reference_rows), "contact_sheets": sheets, "failed_targets": [r["glyph_id"] for r in target_rows if r["decision"] != "PASS"], "manual_status": "PENDING_MANUAL"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
